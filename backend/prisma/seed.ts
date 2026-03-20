import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
    console.log("Seeding database with gapgraph dummy data...");

    // Create User
    const user = await prisma.user.upsert({
        where: { email: "alex.rivera@example.com" },
        update: {},
        create: {
            id: "usr_01",
            email: "alex.rivera@example.com",
            role: "candidate",
            preferences: {
                notifications: true,
                theme: "dark",
                learning_pace: "accelerated"
            }
        }
    });

    console.log("Created user:", user.id);

    // Create Profile
    const profile = await prisma.profile.upsert({
        where: { userId: "usr_01" },
        update: {},
        create: {
            userId: "usr_01",
            resumeText: "Experienced Full Stack Developer building scalable web applications. Proficient in Python, Django, React, and SQL database architecture.",
            extractedSkills: {
                technical: [
                    { skill: "Python", confidence: 0.95 },
                    { skill: "React", confidence: 0.90 },
                    { skill: "Django", confidence: 0.85 },
                    { skill: "SQL", confidence: 0.80 }
                ],
                soft: [
                    { skill: "Communication", confidence: 0.88 },
                    { skill: "Problem Solving", confidence: 0.75 }
                ]
            }
        }
    });

    console.log("Created profile for user:", profile.userId);

    // Ensure Roadmap doesn't duplicate
    const existingRoadmap = await prisma.roadmap.findFirst({
        where: { userId: "usr_01", role: "AI Integration Architect" }
    });
    
    let roadmapId = "rm_01";
    
    if (!existingRoadmap) {
        // Create Roadmap
        const roadmap = await prisma.roadmap.create({
            data: {
                id: "rm_01",
                userId: "usr_01",
                role: "AI Integration Architect",
                readinessScore: 60,
                modules: [
                    { module_id: "GG-101", name: "Foundations of Agentic Systems", status: "COMPLETED", order: 1 },
                    { module_id: "GG-401", name: "O*NET Competency Standardization", status: "IN_PROGRESS", order: 2 },
                    { module_id: "GG-201", name: "Mastering LangGraph Orchestration", status: "LOCKED", order: 3 },
                    { module_id: "GG-301", name: "Vector Datasets & RAG Architectures", status: "LOCKED", order: 4 }
                ]
            }
        });
        console.log("Created roadmap:", roadmap.id);
        roadmapId = roadmap.id;
    } else {
        roadmapId = existingRoadmap.id;
    }

    // Create ModuleCompleted
    await prisma.moduleCompleted.upsert({
        where: { 
            roadmapId_moduleId: {
                roadmapId: roadmapId,
                moduleId: "GG-101"
            }
        },
        update: {},
        create: {
            roadmapId: roadmapId,
            moduleId: "GG-101",
            completedAt: new Date("2026-03-18T10:30:00Z")
        }
    });
    
    console.log("Created module completion status.");
    console.log("Seeding completed successfully!");
}

main()
    .catch((e) => {
        console.error(e);
        process.exit(1);
    })
    .finally(async () => {
        await prisma.$disconnect();
    });
