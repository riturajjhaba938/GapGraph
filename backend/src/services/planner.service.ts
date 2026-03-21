import { Graph, alg } from "@dagrejs/graphlib";
import catalogData from "../data/catalog.json";
import { ReasoningTracer } from "../utils/reasoning-tracer";

interface CatalogCourse {
    courseId: string;
    title: string;
    description: string;
    skillsCovered: string[];
    prerequisites: string[];
    provider: string;
    difficulty: string;
    durationHours: number;
}

export interface PathNode {
    courseId: string;
    title: string;
    skillsCovered: string[];
    difficulty: string;
    durationHours: number;
    status: "AVAILABLE" | "EXTERNAL_REQUIRED";
}

export interface LearningPath {
    nodes: PathNode[];
    edges: Array<{ from: string; to: string }>;
    flaggedExternal: string[];
    totalHours: number;
}

export class PlannerService {
    private catalog: CatalogCourse[];
    private skillToCourseMap: Map<string, CatalogCourse[]>;

    constructor() {
        this.catalog = catalogData.courses as CatalogCourse[];
        this.skillToCourseMap = new Map();

        // Build a reverse index: skill → courses that teach it
        for (const course of this.catalog) {
            for (const skill of course.skillsCovered) {
                const normalized = skill.toLowerCase().trim();
                if (!this.skillToCourseMap.has(normalized)) {
                    this.skillToCourseMap.set(normalized, []);
                }
                this.skillToCourseMap.get(normalized)!.push(course);
            }
        }
    }

    /**
     * Identify skill gaps: skills required by JD but missing from resume
     */
    identifyGaps(
        resumeSkills: string[],
        jdSkills: string[],
        tracer: ReasoningTracer
    ): string[] {
        const resumeSet = new Set(resumeSkills.filter(Boolean).map((s) => s.toLowerCase().trim()));
        const gaps = jdSkills
            .filter(Boolean)
            .map((s) => s.toLowerCase().trim())
            .filter((s) => !resumeSet.has(s));

        tracer.addStep(
            `Identified ${gaps.length} skill gaps from ${jdSkills.length} JD skills vs ${resumeSkills.length} resume skills`,
            "Computing skill gap list"
        );

        return gaps;
    }

    /**
     * Build a DAG of courses and use BFS to find the shortest prerequisite path
     * to bridge identified skill gaps.
     */
    buildLearningPath(
        skillGaps: string[],
        tracer: ReasoningTracer
    ): LearningPath {
        tracer.addStep(
            "Building Directed Acyclic Graph (DAG) from course catalog",
            "Constructing graph nodes and prerequisite edges"
        );

        // Build the full catalog graph
        const g = new Graph({ directed: true });

        // Add all courses as nodes
        for (const course of this.catalog) {
            g.setNode(course.courseId, course);
        }

        // Add prerequisite edges (prerequisite -> course)
        for (const course of this.catalog) {
            for (const prereq of course.prerequisites) {
                g.setEdge(prereq, course.courseId);
            }
        }

        tracer.addStep(
            `DAG constructed: ${g.nodeCount()} nodes, ${g.edgeCount()} edges`,
            "Finding courses that cover skill gaps"
        );

        // Find target courses for each skill gap
        const targetCourseIds = new Set<string>();
        const flaggedExternal: string[] = [];

        for (const gap of skillGaps) {
            const courses = this.skillToCourseMap.get(gap);
            if (courses && courses.length > 0) {
                // Pick the course with the lowest difficulty
                const sorted = [...courses].sort((a, b) => {
                    const order: Record<string, number> = {
                        beginner: 0,
                        intermediate: 1,
                        advanced: 2,
                    };
                    return (order[a.difficulty] || 0) - (order[b.difficulty] || 0);
                });
                targetCourseIds.add(sorted[0].courseId);
                tracer.addStep(
                    `Skill "${gap}" → mapped to course "${sorted[0].title}" (${sorted[0].courseId})`,
                    "Scanning Catalog"
                );
            } else {
                flaggedExternal.push(gap);
                tracer.addStep(
                    `Skill "${gap}" → NOT FOUND in local catalog`,
                    "Flagging as EXTERNAL_REQUIRED"
                );
            }
        }

        tracer.addStep(
            `${targetCourseIds.size} internal courses identified, ${flaggedExternal.length} flagged as external`,
            "Running BFS to resolve prerequisite chains"
        );

        // BFS backwards from each target course collecting all prerequisites
        const requiredCourseIds = new Set<string>();

        for (const targetId of targetCourseIds) {
            this.bfsCollectPrerequisites(g, targetId, requiredCourseIds);
        }

        // Also include the target courses themselves
        for (const id of targetCourseIds) {
            requiredCourseIds.add(id);
        }

        tracer.addStep(
            `BFS complete: ${requiredCourseIds.size} total courses in learning path (including prerequisites)`,
            "Building final path output"
        );

        // Build subgraph and topological sort for ordering
        const subG = new Graph({ directed: true });
        for (const id of requiredCourseIds) {
            const course = this.catalog.find((c) => c.courseId === id);
            if (course) {
                subG.setNode(id, course);
            }
        }

        // Add edges only within the subgraph
        for (const id of requiredCourseIds) {
            const course = this.catalog.find((c) => c.courseId === id);
            if (course) {
                for (const prereq of course.prerequisites) {
                    if (requiredCourseIds.has(prereq)) {
                        subG.setEdge(prereq, id);
                    }
                }
            }
        }

        // Topological sort for proper ordering
        let orderedIds: string[];
        try {
            orderedIds = alg.topsort(subG);
        } catch {
            orderedIds = Array.from(requiredCourseIds);
        }

        // Build output
        const nodes: PathNode[] = orderedIds.map((id) => {
            const course = this.catalog.find((c) => c.courseId === id)!;
            return {
                courseId: course.courseId,
                title: course.title,
                skillsCovered: course.skillsCovered,
                difficulty: course.difficulty,
                durationHours: course.durationHours,
                status: "AVAILABLE" as const,
            };
        });

        const edges: Array<{ from: string; to: string }> = [];
        for (const id of requiredCourseIds) {
            const course = this.catalog.find((c) => c.courseId === id);
            if (course) {
                for (const prereq of course.prerequisites) {
                    if (requiredCourseIds.has(prereq)) {
                        edges.push({ from: prereq, to: id });
                    }
                }
            }
        }

        const totalHours = nodes.reduce((sum, n) => sum + n.durationHours, 0);

        tracer.addStep(
            `Learning path finalized: ${nodes.length} courses, ${edges.length} edges, ${totalHours} total hours, ${flaggedExternal.length} external skills`,
            "Path construction complete"
        );

        return { nodes, edges, flaggedExternal, totalHours };
    }

    /**
     * BFS to collect all prerequisite courses for a target course
     */
    private bfsCollectPrerequisites(
        g: Graph,
        targetId: string,
        collected: Set<string>
    ): void {
        const queue: string[] = [targetId];
        const visited = new Set<string>();

        while (queue.length > 0) {
            const current = queue.shift()!;
            if (visited.has(current)) continue;
            visited.add(current);

            // Get predecessors (prerequisites)
            const predecessors = g.predecessors(current);
            if (predecessors) {
                for (const pred of predecessors) {
                    collected.add(pred as string);
                    queue.push(pred as string);
                }
            }
        }
    }
}
