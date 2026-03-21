import { DiagnoserService } from "./src/services/diagnoser.service";
import { ReasoningTracer } from "./src/utils/reasoning-tracer";
import dotenv from "dotenv";
dotenv.config();

async function run() {
    const diagnoser = new DiagnoserService();
    const tracer = new ReasoningTracer();
    const text = "I am a Full Stack Developer. I know React, Node.js, Next.js, and MongoDB. I practice Agile teamwork. Leadership experience.";
    
    console.log("Extracting skills...");
    const skills = await diagnoser.extractSkills(text, tracer);
    console.log("Final JSON Parsed:", JSON.stringify(skills, null, 2));
}
run().catch(console.error);
