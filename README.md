# AI Crop-Specific Pruning Recommendation System (MVP)

A beginner-friendly but production-minded prototype for branch pruning recommendations from plant/tree images.

## 1) Architecture (MVP first)

### High-level flow
1. User uploads plant image from web UI.
2. Node.js (Express) receives image and saves it.
3. Node.js calls Python OpenCV script.
4. Python detects branch-like line segments + applies pruning rules.
5. Python returns JSON suggestions + writes annotated image.
6. Frontend renders annotated image and human-readable reasons.

### Components
- **Frontend (`frontend/`)**: simple HTML/CSS/JS UI with canvas drawing.
- **Backend (`backend/src/server.js`)**: upload API, Python process orchestration, static file serving.
- **AI Processing (`backend/python/analyze_pruning.py`)**: branch detection + rule engine + explanation generator.
- **Storage (`backend/uploads`, `backend/results`)**: raw uploads and output images.

### Why this is good for 1 month
- Week 1: end-to-end MVP (this repo).
- Week 2: improve rule tuning per crop.
- Week 3: add minimal ML scoring feature.
- Week 4: polish, test, and document patent claims.

---

## 2) Folder structure

```text
.
├── backend
│   ├── package.json
│   ├── src
│   │   └── server.js
│   ├── python
│   │   ├── analyze_pruning.py
│   │   └── requirements.txt
│   ├── uploads/             # runtime
│   └── results/             # runtime
├── frontend
│   ├── index.html
│   ├── styles.css
│   └── script.js
└── README.md
```

---

## 3) Core APIs and JSON contract

### Endpoint
`POST /api/analyze`

### Form-data input
- `image`: image file

### Response JSON example

```json
{
  "message": "Analysis complete",
  "inputImage": "17100000-uuid.jpg",
  "annotatedImageUrl": "/results/annotated-17100000-uuid.png",
  "stats": {
    "detectedBranches": 42,
    "pruneCandidates": 8
  },
  "suggestions": [
    {
      "branch_id": 3,
      "center_x": 320,
      "center_y": 210,
      "radius": 14,
      "reason": "Overcrowded area, Blocking sunlight",
      "confidence": 0.7
    }
  ]
}
```

---

## 4) Branch detection + pruning rules (implemented)

Inside `analyze_pruning.py`:

### Detection (OpenCV)
- Convert to grayscale
- Gaussian blur
- Canny edges
- Probabilistic Hough transform (`HoughLinesP`) to detect branch-like lines

### Rule-based pruning logic
Each detected branch gets a score:
- **Overcrowded area**: too many nearby branch midpoints.
- **Blocking sunlight**: branch direction points inward toward canopy center.
- **Weak branch**: very short branch length.
- **Overlapping branch**: local crossing/angle conflict with nearby lines.

If total score >= threshold, branch is marked for pruning.

### Explainability
For every pruning candidate we store:
- coordinates `(center_x, center_y)`
- `radius` for red circle
- `reason` (human readable)
- `confidence`

---

## 5) Frontend rendering of red circles

The frontend does both:
1. display the annotated image from backend
2. draw circles and reason labels on canvas using returned coordinates

This makes the output auditable and easy for farmers/experts to validate.

---

## 6) Simple ML upgrade (optional, one feature)

Add one tiny ML module after MVP:

**Upgrade idea: Branch Weakness Classifier (Logistic Regression)**
- Features: branch length, local density, angle, overlap count.
- Label: prune/not-prune from expert examples.
- Keep rules as baseline; ML only adjusts confidence.

Why this is beginner-friendly:
- very small dataset needed initially
- easy to train with `scikit-learn`
- interpretable coefficients (helps patent narrative)

---

## 7) Patent-oriented improvements (practical)

Potential novelty direction:
1. **Hybrid rule + explainability scoring engine** for pruning.
2. **Crop-specific policy profiles** (mango, grape, apple): same detector, different thresholds/reason weights.
3. **Reason trace object**: store which rule contributed what score (auditable decision path).
4. **Temporal comparison**: compare before/after images to validate pruning outcomes.

For patent preparation, document:
- unique rule combinations
- confidence fusion method
- explainability schema
- crop profile adaptation logic

---

## 8) Production-level checklist (next steps)

- Add authentication and role-based access.
- Use queue workers (BullMQ/Celery) for heavy image jobs.
- Move files to object storage (S3/GCS).
- Add API validation (`zod`/`joi`) and rate limiting.
- Add structured logs + monitoring.
- Containerize backend/python and deploy behind reverse proxy.

---

## 9) Run locally (step-by-step)

### Prerequisites
- Node.js 20+
- Python 3.10+

### Backend setup

```bash
cd backend
npm install
python3 -m venv .venv
source .venv/bin/activate
pip install -r python/requirements.txt
npm run dev
```

Backend starts on `http://localhost:4000`.

### Frontend setup

In another terminal:

```bash
cd frontend
python3 -m http.server 5500
```

Open `http://localhost:5500`.

Upload an image and inspect pruning recommendations.

---

## 10) 1-month execution plan

### Week 1 (MVP)
- Complete upload/analyze/render loop.
- Validate rules on 20-30 sample images.

### Week 2 (Crop-specific tuning)
- Add profile JSON (e.g., mango/grape).
- Tune thresholds per crop.

### Week 3 (One ML feature)
- Train logistic regression weakness scorer.
- Blend with rule confidence.

### Week 4 (Hackathon + patent prep)
- Demo script + case studies.
- Draft provisional patent claims around hybrid explainable pruning engine.

---

If you want, next I can add **crop profile support** (e.g., mango/grape rules) with only ~2 extra files and endpoint changes.
