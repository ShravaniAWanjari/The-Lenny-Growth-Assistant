import express, { Request, Response } from "express";
import cors from "cors";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import { generateChatResponse } from "./agent.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

const app = express();
const PORT = parseInt(process.env.PI_AGENT_PORT || "3001", 10);

app.use(cors());
app.use(express.json({ limit: "10mb" }));

app.get("/health", (req: Request, res: Response) => {
  res.json({
    status: "ok",
    service: "pi-agent",
    timestamp: new Date().toISOString(),
  });
});

app.post("/chat", async (req: Request, res: Response) => {
  try {
    const { prompt, provider, model, systemPrompt, retrievedSources, conversationHistory } = req.body;

    if (!prompt || typeof prompt !== "string") {
      res.status(400).json({
        status: "error",
        error: "Field 'prompt' is required and must be a non-empty string.",
      });
      return;
    }

    const result = await generateChatResponse({
      prompt,
      provider,
      model,
      systemPrompt,
      retrievedSources,
      conversationHistory,
    });

    res.json({
      status: "ok",
      ...result,
    });
  } catch (err: any) {
    const message = err?.message || String(err);
    const statusCode = message.includes("Unsupported provider") || message.includes("is required") ? 400 : 500;
    res.status(statusCode).json({
      status: "error",
      error: message,
    });
  }
});

const server = app.listen(PORT, "0.0.0.0", () => {
  console.log(`[Pi Agent] Service running on http://localhost:${PORT}`);
});

export default app;
