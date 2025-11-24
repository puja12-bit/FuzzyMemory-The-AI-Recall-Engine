import os
import json
from typing import Optional, List

import numpy as np
import librosa
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from db import SessionLocal, ContentItem, init_db_and_seed

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_FILE = os.path.join(BASE_DIR, "seed_data.json")

# Audio params for humming
SR = 22050
FMIN = librosa.note_to_hz("C2")
FMAX = librosa.note_to_hz("C7")
FRAME_HOP = 512

# -------------------------------------------------------------------
# App init
# -------------------------------------------------------------------

app = FastAPI(title="Fuzzy Memory - Recall Context Engine")

# Initialize DB and seed from seed_data.json on startup
init_db_and_seed()

# Load seed JSON for humming (we still use this for semitones)
if os.path.exists(SEED_FILE):
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        SEED_ENTRIES = json.load(f)
else:
    SEED_ENTRIES = []
    print("WARNING: seed_data.json not found. Humming endpoint will have no matches.")


# -------------------------------------------------------------------
# Database dependency
# -------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------------------------
# Utility: Simple DTW distance for semitone sequences
# -------------------------------------------------------------------

def dtw_distance(semi_q: List[float], semi_t: List[float]) -> float:
    """
    Very simple DTW over 1D sequences.
    """
    q = np.array(semi_q, dtype=float)
    t = np.array(semi_t, dtype=float)

    if len(q) < 3 or len(t) < 3:
        return float("inf")

    n = len(q)
    m = len(t)
    cost = np.zeros((n, m), dtype=float)

    for i in range(n):
        for j in range(m):
            cost[i, j] = abs(q[i] - t[j])

    D = np.full((n + 1, m + 1), np.inf, dtype=float)
    D[0, 0] = 0.0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i, j] = cost[i - 1, j - 1] + min(
                D[i - 1, j], D[i, j - 1], D[i - 1, j - 1]
            )

    dist = D[n, m]
    norm = dist / (n + m)
    return float(norm)


def extract_semitones_from_audio_bytes(data: bytes) -> List[float]:
    """
    Convert an uploaded hum into a semitone contour.
    """
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        y, _ = librosa.load(tmp_path, sr=SR, mono=True)
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=FMIN,
            fmax=FMAX,
            sr=SR,
            frame_length=2048,
            hop_length=FRAME_HOP,
        )
        with np.errstate(divide="ignore", invalid="ignore"):
            semis = 12 * np.log2(f0 / 440.0)
        # keep voiced only
        voiced_idx = np.where(~np.isnan(semis))[0]
        if len(voiced_idx) < 3:
            return []
        semis_clean = semis[voiced_idx]
        semis_clean = semis_clean.tolist()
        return semis_clean
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Simple home / health endpoint.
    """
    return """
    <html>
      <head><title>Fuzzy Memory</title></head>
      <body>
        <h1>Fuzzy Memory - The Recall Context Engine</h1>
        <p>Backend is running.</p>
        <ul>
          <li>GET /api/search/text?q=your+query</li>
          <li>POST /api/search/hum (multipart/form-data, field: file)</li>
        </ul>
      </body>
    </html>
    """


@app.get("/api/search/text")
async def search_text(q: Optional[str] = "", db: Session = Depends(get_db)):
    """
    Text-based recall over the content_items table.
    Searches title, creator, and context using a LIKE-based filter.
    """
    q = (q or "").strip().lower()
    if not q:
        return {"query": q, "results": []}

    like_pattern = f"%{q}%"

    items = (
        db.query(ContentItem)
        .filter(
            (ContentItem.title.ilike(like_pattern))
            | (ContentItem.creator.ilike(like_pattern))
            | (ContentItem.context.ilike(like_pattern))
        )
        .limit(30)
        .all()
    )

    results = []
    for item in items:
        results.append(
            {
                "id": item.id,
                "type": item.type,
                "title": item.title,
                "creator": item.creator,
                "context": item.context,
                "metadata": json.loads(item.metadata_json)
                if item.metadata_json
                else {},
            }
        )

    return {"query": q, "results": results}


@app.post("/api/search/hum")
async def search_hum(file: UploadFile = File(...)):
    """
    Hum-based recall using semitone DTW against seed_data.json.
    This still uses the semitones from the JSON entries.
    Later we can move this into DB / embedding.
    """
    if not SEED_ENTRIES:
        raise HTTPException(
            status_code=500,
            detail="No seed entries loaded. Add seed_data.json to the app folder.",
        )

    data = await file.read()
    semis_q = extract_semitones_from_audio_bytes(data)
    if len(semis_q) < 3:
        return {
            "matches": [],
            "message": "Could not detect enough pitched frames. Try humming more clearly for 3–6 seconds.",
        }

    scored = []
    for entry in SEED_ENTRIES:
        seq = entry.get("semitones") or []
        if not seq:
            continue
        dist = dtw_distance(semis_q, seq)
        scored.append((dist, entry))

    scored.sort(key=lambda x: x[0])

    matches = []
    for dist, entry in scored[:5]:
        # rough threshold
        if np.isinf(dist) or dist > 8.0:
            continue
        matches.append(
            {
                "title": entry.get("title", ""),
                "artist": entry.get("artist", ""),
                "distance": dist,
                "youtube_search": entry.get("youtube_search", ""),
                "derivatives": entry.get("derivatives", []),
            }
        )

    if not matches:
        return {
            "matches": [],
            "message": "No close match found in the small demo seed set.",
        }

    return {"matches": matches}
