import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import { getBuiltinModel } from "@earendil-works/pi-ai/providers/all";
import { streamSimple } from "@earendil-works/pi-ai/api/google-generative-ai";
import type { Context, TextContent } from "@earendil-works/pi-ai";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

async function runMinimal() {
  const rawKey = process.env.GEMINI_API_KEY || "";
  const apiKey = rawKey.trim();

  if (!apiKey) {
    throw new Error("GEMINI_API_KEY is not set in .env");
  }

  console.log("Testing Checkpoint 3: Minimal Pi SDK call with ONE model...");

  const model = getBuiltinModel("google", "gemini-2.5-flash");
  console.log(`Using model: ${model.id} (${model.name}) via ${model.provider}`);

  const context: Context = {
    messages: [
      {
        role: "user",
        content: "What is 2 + 2? Answer with just the number.",
        timestamp: Date.now(),
      },
    ],
  };

  const stream = streamSimple(model, context, {
    apiKey: apiKey,
  });

  for await (const event of stream) {
    if (event.type === "text_delta") {
      process.stdout.write(event.delta);
    }
  }

  const finalMessage = await stream.result();
  const textParts = finalMessage.content
    .filter((c): c is TextContent => c.type === "text")
    .map((c) => c.text)
    .join("");

  console.log("\n\nResult text:", textParts);
  console.log("Checkpoint 3 PASSED: Minimal Pi call succeeded!");
}

runMinimal().catch((err) => {
  console.error("Checkpoint 3 FAILED:", err);
  process.exit(1);
});
