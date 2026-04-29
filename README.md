# AI Crop-Specific Pruning Recommendation System (MVP - Fixed)

## What was fixed

1. **`Cannot GET /`** fixed by serving frontend static files from Express and adding SPA fallback route.
2. **Incorrect pruning circles** fixed by:
   - limiting branch detection to plant-colored regions (mask),
   - tightening Hough and pruning thresholds,
   - correcting frontend coordinate scaling using backend image dimensions,
   - avoiding mixed coordinate spaces from double-rendering different images.
3. **Frontend + backend integration** fixed so the UI can call the API on the same origin.

---

## Project structure

```text
.
├── .env.example
├── package.json
├── backend
│   ├── package.json
│   ├── src/server.js
│   ├── python/analyze_pruning.py
│   ├── python/requirements.txt
│   ├── uploads/
│   └── results/
└── frontend
    ├── index.html
    ├── styles.css
    └── script.js
```

---

## Dependencies to install

### System
- Node.js 20+
- Python 3.10+

### Backend Node packages
```bash
cd backend
npm install
```

### Python packages
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r python/requirements.txt
```

---

## Environment variables

Create `.env` in repository root (or copy from `.env.example`):

```bash
cp .env.example .env
```

Available variables:
- `PORT` (default `4000`)
- `HOST` (default `0.0.0.0`)

---

## How to run (recommended: single server)

From repo root:

```bash
cd backend
npm run dev
```

Open in browser:
- `http://localhost:4000/` (frontend page)
- API health: `http://localhost:4000/api/health`

This works because backend now serves files from `frontend/` directly.

---

## Optional: run frontend separately

If needed for static frontend-only development:

```bash
npm run start:frontend
```

Then open:
- `http://localhost:5500/`

> If running frontend separately, keep backend running on `http://localhost:4000`.

---

## Root cause of incorrect pruning markings

The circles were spread incorrectly due to **coordinate mismatch**:
- the frontend drew an already annotated backend image,
- then added a second overlay using dimensions from a different image coordinate space.

This caused scale drift and misplaced markers.

Fix applied:
- frontend now draws the uploaded image once and overlays circles using backend-provided original width/height;
- backend includes `imageWidth`/`imageHeight` in response;
- detection now ignores non-plant regions using HSV masking, reducing random false detections.

---

## API output format (current)

`POST /api/analyze` returns:

```json
{
  "message": "Analysis complete",
  "inputImage": "...",
  "annotatedImageUrl": "/results/annotated-...png",
  "stats": {
    "detectedBranches": 20,
    "pruneCandidates": 4,
    "imageWidth": 1280,
    "imageHeight": 720
  },
  "suggestions": [
    {
      "branch_id": 1,
      "center_x": 430,
      "center_y": 290,
      "radius": 14,
      "reason": "Overcrowded area, Weak branch",
      "confidence": 0.75
    }
  ]
}
```
