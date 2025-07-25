const express = require("express");
const cors = require("cors");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const { exec } = require("child_process");
const archiver = require("archiver");
const mime = require("mime-types");

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.json());

const uploadsDir = path.join(__dirname, "uploads");
const sessionsDir = path.join(__dirname, "sessions");
if (!fs.existsSync(uploadsDir)) fs.mkdirSync(uploadsDir);
if (!fs.existsSync(sessionsDir)) fs.mkdirSync(sessionsDir);

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename: (req, file, cb) => {
    const timestamp = Date.now();
    const safeName = file.originalname.replace(/\s+/g, "_");
    cb(null, `${timestamp}-${safeName}`);
  },
});
const allowedExtensions = [".lsm", ".mp4", ".webm", ".ogg"];
const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    cb(null, allowedExtensions.includes(ext));
  },
});

function convertVideoToFastStart(inputPath, outputPath, callback) {
  const ffmpegPath = path.join(__dirname, "tools", "ffmpeg.exe");
  const cmd = `"${ffmpegPath}" -i "${inputPath}" -c:v libx264 -c:a aac -movflags +faststart "${outputPath}"`;

  exec(cmd, (error, stdout, stderr) => {
    if (error) {
      console.error("❌ Video conversion failed:", error);
    } else {
      console.log("✅ Video converted to:", outputPath);
      if (typeof callback === "function") callback();
    }
  });
}

app.get("/sessions/:sessionId/:fileName", (req, res) => {
  const { sessionId, fileName } = req.params;
  const filePath = path.join(sessionsDir, sessionId, fileName);

  if (!fs.existsSync(filePath)) {
    return res.status(404).send("File not found");
  }

  if (fileName === "graph_custom.png") {
    return res.download(filePath, fileName);
  }

  const stat = fs.statSync(filePath);
  const fileSize = stat.size;
  const range = req.headers.range;

  const mimeType = path.extname(filePath) === ".mp4"
    ? "video/mp4"
    : (mime.lookup(filePath) || "application/octet-stream");

  console.log("[SERVE VIDEO]", filePath);
  console.log("[MIME TYPE]", mimeType);
  console.log("[HAS RANGE]", !!range);

  if (range) {
    const parts = range.replace(/bytes=/, "").split("-");
    const start = parseInt(parts[0], 10);
    const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
    const chunkSize = end - start + 1;

    const stream = fs.createReadStream(filePath, { start, end });
    res.writeHead(206, {
      "Content-Range": `bytes ${start}-${end}/${fileSize}`,
      "Accept-Ranges": "bytes",
      "Content-Length": chunkSize,
      "Content-Type": mimeType,
    });
    stream.pipe(res);
  } else {
    res.writeHead(200, {
      "Content-Length": fileSize,
      "Content-Type": mimeType,
      "Accept-Ranges": "bytes",
    });
    fs.createReadStream(filePath).pipe(res);
  }
});

app.use("/sessions", express.static(sessionsDir));

app.post("/upload", upload.single("video"), (req, res) => {
  const mode = req.body.mode;
  const videoFile = req.file;

  if (!videoFile || !mode) {
    return res.status(400).json({ message: "Missing file or mode" });
  }

  const sessionId = Date.now().toString();
  const sessionDir = path.join(sessionsDir, sessionId);
  fs.mkdirSync(sessionDir, { recursive: true });

  const inputPath = path.join(uploadsDir, videoFile.filename);
  let pythonScript = "";
  if (mode === "detection") pythonScript = "run_detection_only.py";
  else if (mode === "tracking_noise") pythonScript = "run_tracking_noise.py";
  else if (mode === "tracking_filtered") pythonScript = "run_tracking_filtered.py";
  else return res.status(400).json({ message: "Invalid processing mode" });

  const command = `python ${pythonScript} "${inputPath}" "${sessionDir}"`;
  console.log("Running:", command);

  exec(command, (error, stdout, stderr) => {
    console.log("stdout:", stdout);
    console.error("stderr:", stderr);

    if (error) {
      return res.status(500).json({ message: "Python script failed", error: stderr });
    }

    const base = `/sessions/${sessionId}`;
    const result = { sessionId, resultDir: base, mode }; // ✅ mode נוסף כאן

    let rawVideoName = "";
    if (mode === "detection") {
      rawVideoName = "labeled_video.mp4";
      result.labeledFramesDir = `${base}/labeled_frames`;
    } else if (mode === "tracking_noise") {
      rawVideoName = "tracked_video.mp4";
      result.labeledFramesDir = `${base}/labeled_frames`;
      result.summaryCSV = `${base}/final_summary.csv`;
      result.graph = `${base}/graph.png`;
      result.rawTracksCSV = `${base}/simple_tracks.csv`;
    } else if (mode === "tracking_filtered") {
      rawVideoName = "filtered_tracking_video.mp4";
      result.labeledFramesDir = `${base}/labeled_frames`;
      result.summaryCSV = `${base}/final_summary.csv`;
      result.graph = `${base}/graph.png`;
      result.rawTracksCSV = `${base}/filtered_tracks.csv`;
    }

    const rawVideoPath = path.join(sessionDir, rawVideoName);
    const readyVideoName = rawVideoName.replace(".mp4", "_ready.mp4");
    const readyVideoPath = path.join(sessionDir, readyVideoName);

    convertVideoToFastStart(rawVideoPath, readyVideoPath, () => {
      result.video = `${base}/${readyVideoName}`;

      const framesPath = path.join(sessionDir, "labeled_frames");
      if (fs.existsSync(framesPath)) {
        const frameFiles = fs.readdirSync(framesPath)
          .filter(f => f.endsWith(".png"))
          .sort();
        result.frameFiles = frameFiles;
      }

      const zipPath = path.join(sessionDir, "results.zip");
      const output = fs.createWriteStream(zipPath);
      const archive = archiver("zip", { zlib: { level: 9 } });

      output.on("close", () => {
        result.zip = `${base}/results.zip`;
        res.json(result);
      });

      archive.on("error", err => {
        console.error("Archive error:", err);
        res.json(result);
      });

      archive.pipe(output);
      const allowedZipExt = [".mp4", ".csv", ".png"];
      fs.readdirSync(sessionDir).forEach(file => {
        const filePath = path.join(sessionDir, file);
        if (fs.statSync(filePath).isFile() && allowedZipExt.includes(path.extname(file)))
          archive.file(filePath, { name: file });
      });

      if (fs.existsSync(framesPath)) {
        archive.directory(framesPath, "labeled_frames");
      }

      archive.finalize();
    });
  });
});

// ✅ יצירת גרף מותאם לפי כמות track_ids
app.post("/generate-graph", (req, res) => {
  const { sessionId, limit, mode } = req.body;
  const sessionDir = path.join(sessionsDir, sessionId);

  if (!fs.existsSync(sessionDir)) {
    return res.status(404).json({ message: "Session not found" });
  }

  const csvName = mode === "tracking_filtered" ? "filtered_tracks.csv" : "simple_tracks.csv";
  const inputCSV = path.join(sessionDir, csvName);
  const outputImage = path.join(sessionDir, "graph_custom.png");

  if (!fs.existsSync(inputCSV)) {
    return res.status(404).json({ message: `${csvName} not found` });
  }

  const graphScript = path.join(__dirname, "..", "python_code", "graph_of_sperm_tracks.py");
  const command = `python "${graphScript}" "${inputCSV}" "${outputImage}" ${limit}`;
  console.log("[GRAPH CUSTOM] Running:", command);

  exec(command, (error, stdout, stderr) => {
    console.log("stdout:", stdout);
    console.error("stderr:", stderr);

    if (error) {
      return res.status(500).json({ message: "Graph generation failed", error: stderr });
    }

    const imageUrl = `/sessions/${sessionId}/graph_custom.png`;
    return res.json({ graph: imageUrl });
  });
});

app.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
});
