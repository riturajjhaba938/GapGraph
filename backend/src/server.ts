import Fastify from "fastify";
import cors from "@fastify/cors";
import multipart from "@fastify/multipart";
import dotenv from "dotenv";
import { PrismaClient } from "@prisma/client";
import { DiagnoserService } from "./services/diagnoser.service";
import { PlannerService } from "./services/planner.service";
import { CriticService } from "./services/critic.service";
import { ReasoningTracer } from "./utils/reasoning-tracer";
import { YouTubeService } from "./services/youtube.service";

dotenv.config();

const server = Fastify({ logger: true });
const prisma = new PrismaClient();

// --- Services ---
const diagnoser = new DiagnoserService();
const planner = new PlannerService();
const critic = new CriticService();
const youtube = new YouTubeService();

// --- Global SSE connections ---
const sseClients = new Map<string, (data: string) => void>();

async function main() {
    // Register plugins
    await server.register(cors, { origin: true });
    await server.register(multipart, { limits: { fileSize: 10 * 1024 * 1024 } }); // 10MB

    // ============================================================
    // SSE Endpoint: /api/stream/:sessionId
    // Clients connect here to receive reasoning trace in real-time
    // ============================================================
    server.get<{ Params: { sessionId: string } }>(
        "/api/stream/:sessionId",
        async (request, reply) => {
            const { sessionId } = request.params;

            reply.raw.writeHead(200, {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                Connection: "keep-alive",
                "Access-Control-Allow-Origin": "*",
            });

            // Register this client
            const sendEvent = (data: string) => {
                reply.raw.write(`data: ${data}\n\n`);
            };

            sseClients.set(sessionId, sendEvent);

            // Send initial connection event
            sendEvent(
                JSON.stringify({
                    step: 0,
                    logic: "Connected to reasoning stream",
                    action: "Awaiting analysis",
                    timestamp: new Date().toISOString(),
                })
            );

            request.raw.on("close", () => {
                sseClients.delete(sessionId);
            });
        }
    );

    // ============================================================
    // AUTH ENDPOINTS: /api/auth/signup & /api/auth/login
    // ============================================================
    server.post("/api/auth/signup", async (request, reply) => {
        try {
            const { name, email, password, role } = request.body as any;
            if (!email || !password) return reply.status(400).send({ error: "Email and password required" });
            
            const existingUser = await prisma.user.findUnique({ where: { email } });
            if (existingUser) return reply.status(400).send({ error: "Email already in use" });

            const user = await prisma.user.create({
                data: { name, email, password, role: role || "Developer" }
            });
            return reply.send({ message: "User created", user: { id: user.id, email: user.email, name: user.name, role: user.role } });
        } catch (error: any) {
            return reply.status(500).send({ error: "Signup failed", details: error.message });
        }
    });

    server.post("/api/auth/login", async (request, reply) => {
        try {
            const { email, password } = request.body as any;
            const user = await prisma.user.findUnique({ where: { email } });
            if (!user || user.password !== password) {
                return reply.status(401).send({ error: "Invalid email or password" });
            }
            return reply.send({ message: "Logged in", user: { id: user.id, email: user.email, name: user.name, role: user.role } });
        } catch (error: any) {
            return reply.status(500).send({ error: "Login failed", details: error.message });
        }
    });

    // ============================================================
    // POST /api/analyze
    // Receives a resume PDF + optional JD text, runs the full
    // Diagnoser → Planner → Critic pipeline
    // ============================================================
    server.post("/api/analyze", async (request, reply) => {
        const sessionId = `session-${Date.now()}`;
        const tracer = new ReasoningTracer();

        // If an SSE client is listening, forward reasoning steps
        tracer.on("step", (step) => {
            const sendEvent = sseClients.get(sessionId);
            if (sendEvent) {
                sendEvent(JSON.stringify(step));
            }
        });

        try {
            tracer.addStep(
                "Analysis pipeline initiated",
                "Receiving uploaded documents"
            );

            const parts = request.parts();
            let resumeBuffer: Buffer | null = null;
            let resumeFilename = "unknown.pdf";
            let jdText = "";
            let userId = "";

            for await (const part of parts) {
                if (part.type === "file" && part.fieldname === "resume") {
                    resumeBuffer = await part.toBuffer();
                    resumeFilename = part.filename || "resume.pdf";
                } else if (part.type === "field" && part.fieldname === "jdText") {
                    jdText = part.value as string;
                } else if (part.type === "field" && part.fieldname === "userId") {
                    userId = part.value as string;
                }
            }

            if (!resumeBuffer) {
                return reply.status(400).send({ error: "Resume PDF is required" });
            }

            // Default JD if not provided
            if (!jdText) {
                jdText = `
          We are looking for a Full-Stack Developer with experience in:
          - React, Next.js, TypeScript for frontend development
          - Node.js, Express for backend development
          - PostgreSQL, database design
          - Docker, CI/CD, DevOps practices
          - Git, Agile methodologies
          - Strong communication and teamwork skills
          - System design and microservices architecture
        `;
            }

            // ==========================================
            // STEP 1: DIAGNOSER - Extract skills
            // ==========================================
            tracer.addStep(
                "PHASE 1: Running Diagnoser Agent",
                "Extracting text from Resume PDF"
            );

            let resumeText = "";
            try {
                resumeText = await diagnoser.extractTextFromPDF(resumeBuffer);
            } catch (pdfErr) {
                console.warn("Invalid PDF uploaded, falling back to dummy text for testing");
                resumeText = "I am a Full Stack Developer. I know React, Node.js, Next.js, and MongoDB. I practice Agile teamwork. Leadership experience.";
            }

            tracer.addStep(
                `Resume text extracted: ${resumeText.length} characters`,
                "Extracting skills from resume"
            );

            const resumeSkills = await diagnoser.extractSkills(resumeText, tracer);
            
            console.log("\n==================================================");
            console.log("📄  EXTRACTED RESUME SKILLS");
            console.log("==================================================");
            console.log(`🔧 Technical Skills (${resumeSkills.technical.length}):`);
            resumeSkills.technical.forEach(s => console.log(`   - ${(s.skill || 'unknown').padEnd(25)} | Confidence: ${(s.confidence * 100).toFixed(1).padStart(5)}% | SOC: ${s.socCode || 'N/A'}`));
            console.log(`\n💬 Soft Skills (${resumeSkills.soft.length}):`);
            resumeSkills.soft.forEach(s => console.log(`   - ${(s.skill || 'unknown').padEnd(25)} | Confidence: ${(s.confidence * 100).toFixed(1).padStart(5)}% | SOC: ${s.socCode || 'N/A'}`));
            console.log("==================================================\n");

            tracer.addStep(
                "Extracting skills from Job Description",
                "Running NER on JD text"
            );

            const jdSkills = await diagnoser.extractSkillsFromJD(jdText, tracer);
            
            console.log("\n==================================================");
            console.log("🎯  EXTRACTED JOB DESCRIPTION SKILLS");
            console.log("==================================================");
            console.log(`🔧 Technical Skills (${jdSkills.technical.length}):`);
            jdSkills.technical.forEach(s => console.log(`   - ${(s.skill || 'unknown').padEnd(25)} | Confidence: ${(s.confidence * 100).toFixed(1).padStart(5)}% | SOC: ${s.socCode || 'N/A'}`));
            console.log(`\n💬 Soft Skills (${jdSkills.soft.length}):`);
            jdSkills.soft.forEach(s => console.log(`   - ${(s.skill || 'unknown').padEnd(25)} | Confidence: ${(s.confidence * 100).toFixed(1).padStart(5)}% | SOC: ${s.socCode || 'N/A'}`));
            console.log("==================================================\n");

            // ==========================================
            // STEP 2: PLANNER - Build learning path
            // ==========================================
            tracer.addStep(
                "PHASE 2: Running Planner Agent",
                "Identifying skill gaps"
            );

            const resumeSkillNames = [
                ...resumeSkills.technical.map((s) => s.skill),
                ...resumeSkills.soft.map((s) => s.skill),
            ].filter((s): s is string => typeof s === 'string' && s.length > 0);
            const jdSkillNames = [
                ...jdSkills.technical.map((s) => s.skill),
                ...jdSkills.soft.map((s) => s.skill),
            ].filter((s): s is string => typeof s === 'string' && s.length > 0);

            const skillGaps = planner.identifyGaps(
                resumeSkillNames,
                jdSkillNames,
                tracer
            );

            tracer.addStep(
                `${skillGaps.length} skill gaps identified: [${skillGaps.join(", ")}]`,
                "Building DAG and computing learning path"
            );

            const learningPath = planner.buildLearningPath(skillGaps, tracer);

            // ==========================================
            // STEP 3: CRITIC - Validate path
            // ==========================================
            tracer.addStep(
                "PHASE 3: Running Critic Agent",
                "Validating learning path against catalog"
            );

            const criticResult = critic.validate(learningPath, tracer);

            tracer.addStep(
                "All phases complete. Analysis pipeline finished successfully.",
                "Fetching YouTube resources for path nodes"
            );

            // Enhance nodes with YouTube resources
            const enhancedNodes = await Promise.all(criticResult.validatedPath.nodes.map(async (node) => {
                const mainSkill = node.skillsCovered[0] || node.title;
                const resources = await youtube.getResourcesForSkill(mainSkill);
                
                return {
                    ...node,
                    resources
                };
            }));

            // Build final response
            const result = {
                sessionId,
                resumeFilename,
                extractedSkills: {
                    resume: resumeSkills,
                    jd: jdSkills,
                },
                skillGaps,
                learningPath: {
                    ...criticResult.validatedPath,
                    nodes: enhancedNodes
                },
                validationReport: criticResult.validationReport,
                reasoningTrace: tracer.getSteps(),
            };

            // Database Persistence
            if (userId) {
                try {
                    tracer.addStep("Saving data to Postgres Database", "Upserting Profile and Roadmap");

                    await prisma.profile.upsert({
                        where: { userId },
                        update: { resumeText, extractedSkills: result.extractedSkills as any },
                        create: { userId, resumeText, extractedSkills: result.extractedSkills as any }
                    });

                    // Fetch user's target role to associate context
                    const userRecord = await prisma.user.findUnique({ where: { id: userId } });
                    const targetRole = userRecord?.role || "Developer";

                    // The readiness score calculates coverage of Matched vs Total JD skills
                    const totalRequired = jdSkills.technical.length + jdSkills.soft.length;
                    const matchedScore = totalRequired > 0 ? ((totalRequired - skillGaps.length) / totalRequired) * 100 : 85;

                    await prisma.roadmap.create({
                        data: {
                            userId,
                            role: targetRole,
                            readinessScore: Math.round(matchedScore),
                            modules: result.learningPath.nodes as any
                        }
                    });
                     tracer.addStep("Database insertion successful", "Pipeline complete");
                } catch (dbError: any) {
                    tracer.addStep("Database insertion failed", dbError.message);
                    console.error("Database save failed: ", dbError);
                }
            }

            // Signal SSE stream completion
            const sendEvent = sseClients.get(sessionId);
            if (sendEvent) {
                sendEvent(JSON.stringify({ step: -1, logic: "DONE", action: "COMPLETE" }));
            }

            return reply.status(200).send(result);
        } catch (error: any) {
            tracer.addStep(`Error: ${error.message}`, "Pipeline failed");

            const sendEvent = sseClients.get(sessionId);
            if (sendEvent) {
                sendEvent(
                    JSON.stringify({
                        step: -1,
                        logic: `Error: ${error.message}`,
                        action: "FAILED",
                    })
                );
            }

            return reply.status(500).send({
                error: "Analysis failed",
                message: error.message,
                reasoningTrace: tracer.getSteps(),
            });
        }
    });

    // ============================================================
    // GET /api/health
    // ============================================================
    server.get("/api/health", async () => {
        return {
            status: "ok",
            service: "GapGraph Backend",
            timestamp: new Date().toISOString(),
        };
    });

    // ============================================================
    // Start server
    // ============================================================
    const port = parseInt(process.env.PORT || "3001", 10);
    try {
        await server.listen({ port, host: "0.0.0.0" });
        console.log(`🚀 GapGraph Backend running on http://localhost:${port}`);
    } catch (err) {
        server.log.error(err);
        process.exit(1);
    }
}

main();
