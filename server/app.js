const express = require("express");
const cors = require("cors");
const multer = require("multer");
const path = require("path");
const fs = require("fs");

const app = express();
const PORT = 5000;

// לאפשר קריאות מהפרונט
app.use(cors());
app.use(express.json());

// יצירת תיקיית uploads אם לא קיימת
const uploadDir = path.join(__dirname, "uploads");
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir);
}

// הגדרת multer – שמירת קבצים ב־uploads/
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => cb(null, Date.now() + "-" + file.originalname)
});
const upload = multer({ storage });

// נקודת API שמקבלת את הקובץ ואת המצב
app.post("/upload", upload.single("video"), (req, res) => {
  const file = req.file;
  const mode = req.body.mode;

  if (!file) return res.status(400).send("No file uploaded");

  console.log("Received file:", file.filename);
  console.log("Selected mode:", mode);

  res.json({ message: "Upload successful", filename: file.filename, mode });
});

// הרצת השרת
app.listen(PORT, () => {
  console.log(`✅ Server is running on http://localhost:${PORT}`);
});
