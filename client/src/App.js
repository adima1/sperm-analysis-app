import React, { useState } from "react";
import "./App.css";

function App() {
  const BASE_URL = "http://localhost:5000";

  const [selectedFile, setSelectedFile] = useState(null);
  const [mode, setMode] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [popupImageIndex, setPopupImageIndex] = useState(null);
  const [customGraphLimit, setCustomGraphLimit] = useState("");
  const [customGraphUrl, setCustomGraphUrl] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) handleFileValidation(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileValidation(file);
  };

  const handleFileValidation = (file) => {
    if (!file) {
      alert("No file selected.");
      return;
    }

    const allowedExtensions = [".lsm", ".mp4", ".webm", ".ogg"];
    const fileName = file.name.toLowerCase();
    const isAllowed = allowedExtensions.some((ext) => fileName.endsWith(ext));

    if (isAllowed) {
      setSelectedFile(file);
    } else {
      alert("Only LSM, MP4, WEBM or OGG files are supported.");
    }
  };

  const handleCheckboxChange = (value) => {
    setMode(value);
  };

  const handleSubmit = async () => {
    if (!selectedFile || !mode) {
      alert("Please select a video file and an option.");
      return;
    }

    const formData = new FormData();
    formData.append("video", selectedFile);
    formData.append("mode", mode);
    setIsLoading(true);
    setResult(null);
    setCustomGraphUrl(null);

    try {
      const response = await fetch(`${BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        console.log("📹 Video path:", data.video);
        setResult({ ...data, mode }); // 🧠 שומר את מצב המצב
      } else {
        alert("Upload failed.");
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert("An error occurred during upload.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setMode("");
    setResult(null);
    setCustomGraphLimit("");
    setCustomGraphUrl(null);
  };

  const handleGenerateCustomGraph = async () => {
    if (!result?.sessionId || !customGraphLimit) return;
    console.log("📤 Sending generate-graph request with:");
    console.log("🧠 Mode:", result.mode);
    console.log("🔢 Limit:", customGraphLimit);
    try {
      const response = await fetch(`${BASE_URL}/generate-graph`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sessionId: result.sessionId,
          limit: parseInt(customGraphLimit),
          mode: result.mode,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const timestamp = new Date().getTime();
        setCustomGraphUrl(`${BASE_URL}${data.graph}?t=${timestamp}`);
      } else {
        alert("Failed to generate custom graph.");
      }
    } catch (error) {
      console.error("Custom graph error:", error);
    }
  };

  return (
    <div className="App">
      <header className="topbar">
        <img src="logo_sami.jpg" alt="SCE Logo" className="logo" />
        <div className="title">Fly Sperm Analysis System</div>
      </header>

      <h1>Upload and Analyze Video</h1>

      <div
        className={`upload-area ${dragOver ? "drag-over" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <p>
          <i className="fas fa-upload upload-icon"></i>
          <br /> Drag & Drop a video (.lsm, .mp4, etc) here,
          <br /> or click to upload
        </p>
        <input
          type="file"
          accept=".lsm,.mp4,.webm,.ogg"
          onChange={handleFileChange}
        />
        {selectedFile && (
          <p className="selected-file">
            <strong>Selected:</strong> {selectedFile.name}
          </p>
        )}
      </div>

      <h1>Options</h1>

      <div className="options">
        <label>
          <input
            type="checkbox"
            checked={mode === "detection"}
            onChange={() => handleCheckboxChange("detection")}
          />
          Detection only
        </label>
        <label>
          <input
            type="checkbox"
            checked={mode === "tracking_noise"}
            onChange={() => handleCheckboxChange("tracking_noise")}
          />
          Tracking + Noisy
        </label>
        <label>
          <input
            type="checkbox"
            checked={mode === "tracking_filtered"}
            onChange={() => handleCheckboxChange("tracking_filtered")}
          />
          Tracking + Filtered
        </label>
      </div>

      <div className="buttons">
        <button onClick={handleSubmit} disabled={isLoading}>
          {isLoading ? "Processing..." : "Submit"}
        </button>
        <button onClick={handleClear}>Clear</button>
      </div>

      {result && (
        <div className="results">
          <h2>Results</h2>

          {result.video && (
            <>
              <p><strong>Analyzed Video:</strong></p>
              <video
                controls
                muted
                playsInline
                preload="auto"
                key={result.video}
                style={{
                  width: "530px",
                  maxWidth: "100%",
                  height: "auto",
                  backgroundColor: "#000",
                  borderRadius: "10px",
                  display: "block",
                  margin: "0 auto",
                }}
              >
                <source
                  src={`${BASE_URL}${result.video}`}
                  type="video/mp4"
                />
                Your browser does not support the video tag.
              </video>
            </>
          )}

          {result.labeledFramesDir && result.frameFiles?.length > 0 && (
            <>
              <p><strong>Labeled Frames:</strong></p>
              <div className="frame-gallery">
                {result.frameFiles.map((frameName, index) => (
                  <div
                    className="frame-item"
                    key={index}
                    onClick={() => setPopupImageIndex(index)}
                  >
                    <img
                      src={`${BASE_URL}${result.labeledFramesDir}/${frameName}`}
                      alt={`Frame ${index}`}
                    />
                    <div className="frame-label">{frameName}</div>
                  </div>
                ))}
              </div>
            </>
          )}

          {(mode === "tracking_noise" || mode === "tracking_filtered") && result.graph && (
            <div className="graph-section" style={{ textAlign: "center", marginTop: "30px" }}>
              <p className="graph-title" style={{ fontWeight: "bold", marginBottom: "10px" }}>
                Tracking Graph:
              </p>
              <img
                src={`${BASE_URL}${result.graph}`}
                alt="Tracking Graph"
                style={{
                  display: "block",
                  margin: "0 auto",
                  maxWidth: "600px",
                  width: "100%",
                  borderRadius: "10px",
                  border: "1px solid #ccc",
                  backgroundColor: "#f9f9f9"
                }}
              />

              <div style={{ marginTop: "20px" }}>
                <input
                  type="number"
                  placeholder="Number of IDs to show"
                  value={customGraphLimit}
                  onChange={(e) => setCustomGraphLimit(e.target.value)}
                  style={{ padding: "6px", marginRight: "10px", width: "200px" }}
                />
                <button onClick={handleGenerateCustomGraph}>Generate Custom Graph</button>
              </div>

              {customGraphUrl && (
                <div style={{ marginTop: "20px" }}>
                  <img
                    src={customGraphUrl}
                    alt="Custom Graph"
                    style={{
                      display: "block",
                      margin: "0 auto",
                      maxWidth: "600px",
                      width: "100%",
                      borderRadius: "10px",
                      border: "1px solid #ccc",
                      backgroundColor: "#f9f9f9"
                    }}
                  />
                  <a
                    href={customGraphUrl.replace(/\?.*/, "")}
                    download
                    style={{ display: "block", textAlign: "center", marginTop: "10px" }}
                  >
                    Download Custom Graph
                  </a>
                </div>
              )}
            </div>
          )}

          {(mode === "tracking_noise" || mode === "tracking_filtered") && (
            <>
              <a href={`${BASE_URL}${result.rawTracksCSV}`} download>
                Download Tracking CSV
              </a>
              <a href={`${BASE_URL}${result.summaryCSV}`} download>
                Download Final Summary CSV
              </a>
            </>
          )}

          {result.zip && (
            <a className="zip-button" href={`${BASE_URL}${result.zip}`} download>
              Download All Results (ZIP)
            </a>
          )}
        </div>
      )}

      {popupImageIndex !== null && (
        <div className="popup-overlay" onClick={() => setPopupImageIndex(null)}>
          <div className="popup-content" onClick={(e) => e.stopPropagation()}>
            <div className="popup-filename">
              {result.frameFiles[popupImageIndex]}
            </div>
            <button
              className="nav-button left"
              onClick={(e) => {
                e.stopPropagation();
                setPopupImageIndex(
                  (popupImageIndex - 1 + result.frameFiles.length) % result.frameFiles.length
                );
              }}
            >
              &lt;
            </button>
            <img
              src={`${BASE_URL}${result.labeledFramesDir}/${result.frameFiles[popupImageIndex]}`}
              alt="Enlarged frame"
            />
            <button
              className="nav-button right"
              onClick={(e) => {
                e.stopPropagation();
                setPopupImageIndex(
                  (popupImageIndex + 1) % result.frameFiles.length
                );
              }}
            >
              &gt;
            </button>
            <button className="close-button" onClick={e => { e.stopPropagation(); setPopupImageIndex(null); }}>×</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
