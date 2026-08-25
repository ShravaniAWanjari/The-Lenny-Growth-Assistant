import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import { getBuiltinModel } from "@earendil-works/pi-ai/providers/all";
import { streamSimple } from "@earendil-works/pi-ai/api/google-generative-ai";
import type { Context, TextContent } from "@earendil-works/pi-ai";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

async function runGeminiTest() {
  const rawKey = process.env.GEMINI_API_KEY || "";
  const apiKey = rawKey.trim();

  if (!apiKey) {
    throw new Error("GEMINI_API_KEY is not set in .env");
  }

  console.log("Testing Checkpoint 5: Pi -> Gemini (gemini-2.5-flash)...");

  const model = getBuiltinModel("google", "gemini-2.5-flash");

  const context: Context = {
    messages: [
      {
        role: "user",
        content: "What is an MVP in product management? Explain in 2 sentences.",
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

  console.log("\n\nFull Response:", textParts);
  console.log(`Tokens - Input: ${finalMessage.usage?.input}, Output: ${finalMessage.usage?.output}`);
  console.log("Checkpoint 5 PASSED: Pi -> Gemini communication verified!");
}

runGeminiTest().catch((err) => {
  console.error("Checkpoint 5 FAILED:", err);
  process.exit(1);
});
