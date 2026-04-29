const API_BASE = window.location.origin;
const form = document.getElementById("uploadForm");
const imageInput = document.getElementById("imageInput");
const previewCanvas = document.getElementById("previewCanvas");
const resultCanvas = document.getElementById("resultCanvas");
const statusEl = document.getElementById("status");
const suggestionsList = document.getElementById("suggestionsList");

function drawImageOnCanvas(canvas, img) {
  const ctx = canvas.getContext("2d");
  const ratio = img.width / img.height;
  const width = 500;
  const height = Math.round(width / ratio);
  canvas.width = width;
  canvas.height = height;
  ctx.clearRect(0, 0, width, height);
  ctx.drawImage(img, 0, 0, width, height);
}

function drawRedCircles(canvas, suggestions, imageWidth, imageHeight) {
  const ctx = canvas.getContext("2d");
  const scaleX = canvas.width / imageWidth;
  const scaleY = canvas.height / imageHeight;

  ctx.strokeStyle = "red";
  ctx.lineWidth = 2;
  ctx.fillStyle = "red";
  ctx.font = "12px Arial";

  suggestions.forEach((s) => {
    const x = s.center_x * scaleX;
    const y = s.center_y * scaleY;
    const r = Math.max(6, s.radius * ((scaleX + scaleY) / 2));

    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillText(s.reason, x + 6, y - 6);
  });
}

function renderSuggestions(suggestions) {
  suggestionsList.innerHTML = "";
  if (!suggestions.length) {
    suggestionsList.innerHTML = "<li>No pruning candidates found for current thresholds.</li>";
    return;
  }

  suggestions.forEach((s) => {
    const li = document.createElement("li");
    li.textContent = `Branch #${s.branch_id}: ${s.reason} (confidence ${s.confidence}) at (${s.center_x}, ${s.center_y})`;
    suggestionsList.appendChild(li);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!imageInput.files[0]) {
    return;
  }

  statusEl.textContent = "Analyzing image...";

  const imageFile = imageInput.files[0];
  const previewImg = new Image();
  previewImg.src = URL.createObjectURL(imageFile);
  await previewImg.decode();
  drawImageOnCanvas(previewCanvas, previewImg);

  const formData = new FormData();
  formData.append("image", imageFile);

  try {
    const response = await fetch(`${API_BASE}/api/analyze`, {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const result = await response.json();

    drawImageOnCanvas(resultCanvas, previewImg);
    drawRedCircles(
      resultCanvas,
      result.suggestions,
      result.stats.imageWidth,
      result.stats.imageHeight
    );

    renderSuggestions(result.suggestions);
    statusEl.textContent = `Done. Detected branches: ${result.stats.detectedBranches}. Prune candidates: ${result.stats.pruneCandidates}.`;
  } catch (error) {
    statusEl.textContent = `Error: ${error.message}`;
  }
});
