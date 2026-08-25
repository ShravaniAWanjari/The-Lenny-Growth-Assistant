import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export interface SkillDefinition {
  name: string;
  description: string;
  triggers: string[];
  output_type: string;
  content: string;
}

const SKILLS_DIR = path.resolve(__dirname, "../skills");

let loadedSkills: SkillDefinition[] = [];

export function loadSkills(): SkillDefinition[] {
  if (loadedSkills.length > 0) {
    return loadedSkills;
  }

  const skills: SkillDefinition[] = [];

  if (!fs.existsSync(SKILLS_DIR)) {
    return skills;
  }

  const entries = fs.readdirSync(SKILLS_DIR, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.isDirectory()) {
      const skillFile = path.join(SKILLS_DIR, entry.name, "SKILL.md");
      if (fs.existsSync(skillFile)) {
        const raw = fs.readFileSync(skillFile, "utf-8");
        const parts = raw.split("---");
        if (parts.length >= 3) {
          const frontmatter = parts[1];
          const markdownBody = parts.slice(2).join("---").trim();

          const nameMatch = frontmatter.match(/name:\s*(.+)/);
          const descMatch = frontmatter.match(/description:\s*(.+)/);
          const outMatch = frontmatter.match(/output_type:\s*(.+)/);

          const triggerMatches = frontmatter.match(/triggers:\s*\n((?:\s*-\s*.+\n?)+)/);
          const triggers: string[] = [];
          if (triggerMatches) {
            const lines = triggerMatches[1].split("\n");
            for (const l of lines) {
              const clean = l.replace(/^\s*-\s*["']?/, "").replace(/["']?\s*$/, "").trim();
              if (clean) triggers.push(clean.toLowerCase());
            }
          }

          skills.push({
            name: nameMatch ? nameMatch[1].trim() : entry.name,
            description: descMatch ? descMatch[1].trim() : "",
            triggers,
            output_type: outMatch ? outMatch[1].trim() : "text",
            content: markdownBody,
          });
        }
      }
    }
  }

  loadedSkills = skills;
  return loadedSkills;
}

export function detectSkill(prompt: string): SkillDefinition | null {
  const skills = loadSkills();
  const lower = prompt.toLowerCase();

  for (const s of skills) {
    for (const t of s.triggers) {
      if (lower.includes(t)) {
        return s;
      }
    }
  }

  return null;
}
