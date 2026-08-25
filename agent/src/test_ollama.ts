import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import { streamSimple } from "@earendil-works/pi-ai/api/openai-completions";
import type { Context, Model, TextContent } from "@earendil-works/pi-ai";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

async function runOllamaTest() {
  const baseUrl = (process.env.OLLAMA_BASE_URL || "http://localhost:11434").replace(/\/$/, "");
  const envModel = process.env.OLLAMA_MODEL?.trim();

  console.log(`Testing Checkpoint 4: Pi -> Ollama (${baseUrl})...`);

  // 1. Check if Ollama is reachable
  let detectedModel = envModel || "";
  try {
    const tagsRes = await fetch(`${baseUrl}/api/tags`);
    if (!tagsRes.ok) {
      throw new Error(`Ollama responded with HTTP ${tagsRes.status}`);
    }
    const tagsData = (await tagsRes.json()) as { models?: Array<{ name: string }> };
    console.log("Ollama is reachable! Available models:", tagsData.models?.map((m) => m.name) || []);

    if (!detectedModel && tagsData.models && tagsData.models.length > 0) {
      detectedModel = tagsData.models[0].name;
      console.log(`Auto-selected available model: ${detectedModel}`);
    }
  } catch (err: any) {
    console.log(`[Note] Could not reach Ollama at ${baseUrl} (${err.message}).`);
    console.log("If Ollama is not currently running, ensure Ollama is started before calling with provider='ollama'.");
    return;
  }

  if (!detectedModel) {
    console.log("[Note] No Ollama models are currently installed. Run `ollama pull <model>` to download a model.");
    return;
  }

  // 2. Call Ollama via OpenAI-compatible endpoint
  const model: Model<"openai-completions"> = {
    id: detectedModel,
    name: detectedModel,
    provider: "ollama",
    api: "openai-completions",
    baseUrl: `${baseUrl}/v1`,
    reasoning: false,
    input: ["text"],
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow: 131072,
    maxTokens: 4096,
  };

  const context: Context = {
    messages: [
      {
        role: "user",
        content: "Hello from Lenny assistant test. Reply with one sentence.",
        timestamp: Date.now(),
      },
    ],
  };

  console.log(`Sending test prompt to Ollama model '${detectedModel}'...`);
  const stream = streamSimple(model, context, {
    apiKey: "ollama",
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

  console.log("\n\nResult from Ollama:", textParts);
  console.log("Checkpoint 4 PASSED: Pi -> Ollama communication verified!");
}

runOllamaTest().catch((err) => {
  console.error("Checkpoint 4 error:", err);
  process.exit(1);
});
