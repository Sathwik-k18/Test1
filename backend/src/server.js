import express from "express";
import cors from "cors";
import helmet from "helmet";
import morgan from "morgan";
import multer from "multer";
import { spawn } from "node:child_process";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { v4 as uuidv4 } from "uuid";
import dotenv from "dotenv";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const backendRoot = path.resolve(__dirname, "..");
const projectRoot = path.resolve(backendRoot, "..");
const frontendRoot = path.resolve(projectRoot, "frontend");

const app = express();
const PORT = Number(process.env.PORT || 4000);
const HOST = process.env.HOST || "0.0.0.0";

const uploadsDir = path.join(backendRoot, "uploads");
const resultsDir = path.join(backendRoot, "results");

for (const dir of [uploadsDir, resultsDir]) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

app.use(helmet({ crossOriginResourcePolicy: { policy: "cross-origin" } }));
app.use(cors());
app.use(express.json({ limit: "2mb" }));
app.use(morgan("dev"));
app.use("/results", express.static(resultsDir));

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, uploadsDir),
  filename: (_req, file, cb) => {
    const ext = path.extname(file.originalname || ".jpg").toLowerCase();
    cb(null, `${Date.now()}-${uuidv4()}${ext}`);
  }
});

const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    if (file.mimetype.startsWith("image/")) {
      cb(null, true);
      return;
    }
    cb(new Error("Only image uploads are supported."));
  }
});

app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", service: "pruning-backend" });
});

app.post("/api/analyze", upload.single("image"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "No image uploaded." });
    }

    const inputPath = req.file.path;
    const outputName = `annotated-${path.basename(req.file.filename, path.extname(req.file.filename))}.png`;
    const outputPath = path.join(resultsDir, outputName);

    const payload = await runPythonAnalysis(inputPath, outputPath);

    return res.json({
      message: "Analysis complete",
      inputImage: req.file.filename,
      annotatedImageUrl: `/results/${outputName}`,
      ...payload
    });
  } catch (error) {
    return res.status(500).json({ error: error.message || "Analysis failed" });
  }
});

app.use(express.static(frontendRoot));

app.get("*", (_req, res) => {
  res.sendFile(path.join(frontendRoot, "index.html"));
});

function runPythonAnalysis(inputPath, outputPath) {
  return new Promise((resolve, reject) => {
    const pythonScript = path.resolve(backendRoot, "python", "analyze_pruning.py");

    const child = spawn("python3", [pythonScript, inputPath, outputPath], {
      cwd: backendRoot
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`Python process failed (${code}): ${stderr}`));
        return;
      }

      try {
        const jsonStart = stdout.indexOf("{");
        const jsonText = jsonStart >= 0 ? stdout.slice(jsonStart) : stdout;
        resolve(JSON.parse(jsonText));
      } catch (e) {
        reject(new Error(`Could not parse python output: ${e.message}. Raw: ${stdout}`));
      }
    });
  });
}

app.use((err, _req, res, _next) => {
  res.status(400).json({ error: err.message || "Request failed" });
});

app.listen(PORT, HOST, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});
