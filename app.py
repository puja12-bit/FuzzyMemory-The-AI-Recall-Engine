from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from db import SessionLocal, ContentItem, init_db_and_seed

import json, os, math, sqlite3, datetime, re
import numpy as np
from scipy.spatial.distance import cdist
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import vertexai
from vertexai.generative_models import GenerativeModel

APP_DIR = os.path.dirname(__file__)
SEED_PATH = os.path.join(APP_DIR, "seed_data.json")
ANALYTICS_DB = os.path.join(APP_DIR, "analytics.db")

app = FastAPI(title="FuzzyMemory Core")

# --- 1. GOOGLE GEMINI SETUP (The Fix for Hackathon) ---
# This attempts to connect to Google's AI. If it fails, it falls back to keywords.
model = None
try:
    PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if PROJECT_ID:
        vertexai.init(project=PROJECT_ID, location="us-central1")
        model = GenerativeModel("gemini-1.5-flash-001")
        print("✅ Gemini AI Connected")
    else:
        print("⚠️ GOOGLE_CLOUD_PROJECT not set. AI features will be limited.")
except Exception as e:
    print(f"⚠️ AI Init Failed: {e}")

# ---------------- analytics ----------------
def init_analytics():
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        c = conn.cursor()
        c.execute('''
          CREATE TABLE IF NOT EXISTS hits (
            id INTEGER PRIMARY KEY,
            ts TIMESTAMP,
            endpoint TEXT,
            q TEXT
          )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Analytics DB Init skipped: {e}")

def log_hit(endpoint, q=""):
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        c = conn.cursor()
        c.execute('INSERT INTO hits (ts, endpoint, q) VALUES (?, ?, ?)', (datetime.datetime.utcnow(), endpoint, str(q)))
        conn.commit()
        conn.close()
    except Exception:
        pass # Fail silently on Cloud Run if DB is locked

init_analytics()

# ---------------- seed loader ----------------
def load_seed():
    if not os.path.exists(SEED_PATH):
        print("❌ Error: seed_data.json not found.")
        return []
    with open(SEED_PATH, "r", encoding="utf8") as f:
        data = json.load(f)
    for e in data:
        # Tokenized text for fallback search
        e["search_text"] = " ".join(filter(None, [
            e.get("title",""),
            e.get("artist",""),
            e.get("said_by",""),
            e.get("metadata",""),
            " ".join(e.get("context", []))
        ])).lower()
        # Preserve semitone arrays as numpy arrays
        e["semitones"] = np.array(e.get("semitones", []), dtype=float) if e.get("semitones") else np.array([], dtype=float)
    return data

SEED = load_seed()

# ---------------- DTW for melody compare (Your Math Logic) ----------------
def dtw_distance(q_arr, t_arr):
    if len(q_arr) == 0 or len(t_arr) == 0:
        return float('inf')
    q = np.array(q_arr, dtype=float).reshape(-1,1)
    t = np.array(t_arr, dtype=float).reshape(-1,1)
    cost = cdist(q, t, metric=lambda a,b: abs(a[0]-b[0]))
    n,m = cost.shape
    D = np.full((n+1, m+1), np.inf)
    D[0,0] = 0.0
    for i in range(1,n+1):
        for j in range(1,m+1):
            D[i,j] = cost[i-1,j-1] + min(D[i-1,j], D[i,j-1], D[i-1,j-1])
    dist = D[n,m]
    norm = dist / (n + m)
    return float(norm)

# ---------------- endpoints ----------------
@app.get("/")
def index():
    return FileResponse(os.path.join(APP_DIR, "index.html"))

@app.post("/api/context")
async def context_search(payload: dict):
    q = (payload.get("query","") or "").strip()
    log_hit("/api/context", q)
    if not q:
        return JSONResponse({"error":"send non-empty 'query' field"}, status_code=400)
    
    # --- STRATEGY 1: TRY GEMINI AI (New Hackathon Feature) ---
    if model:
        try:
            # Prepare clean data for AI (exclude heavy math arrays)
            slim_seed = [{k: v for k, v in x.items() if k != 'semitones'} for x in SEED]
            
            prompt = f"""
            You are a Cultural Historian.
            DATABASE: {json.dumps(slim_seed)}
            USER QUERY: "{q}"
            
            TASK: Find the best match in the DATABASE based on mood, scene, or context.
            Output JSON: {{ "id": 1, "explanation": "Reason..." }}
            """
            
            response = model.generate_content(prompt)
            cleaned = response.text.replace("```json", "").replace("```", "").strip()
            ai_res = json.loads(cleaned)
            
            matched_id = ai_res.get("id")
            matched_item = next((x for x in SEED if x["id"] == matched_id), None)
            
            if matched_item:
                return {"results": [{
                    "id": matched_item["id"],
                    "title": matched_item["title"],
                    "artist": matched_item.get("artist",""),
                    "context_score": 0.99, # AI is confident
                    "youtube_search": matched_item.get("youtube_search"),
                    "derivatives": matched_item.get("derivatives", []),
                    "context": [ai_res.get("explanation", "AI Match")]
                }]}
        except Exception as e:
            print(f"AI Failed, falling back to keywords: {e}")
            # Fall through to Strategy 2 if AI fails

    # --- STRATEGY 2: FALLBACK TO KEYWORDS (Your Old Logic) ---
    def context_score(query, item_text):
        q_tokens = query.lower().split()
        if not q_tokens: return 0.0
        itokens = item_text.split()
        overlap = sum(1 for t in q_tokens if t in itokens)
        return overlap / max(1, len(q_tokens))

    scored = []
    for e in SEED:
        score = context_score(q, e.get("search_text",""))
        scored.append((score, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    
    results = []
    for s,e in scored[:5]:
        if s <= 0: continue
        results.append({
            "id": e["id"],
            "title": e["title"],
            "artist": e.get("artist",""),
            "context_score": round(s,3),
            "youtube_search": e.get("youtube_search"),
            "derivatives": e.get("derivatives", []),
            "context": e.get("context",[])
        })
    
    if not results:
        return {"results": [], "message":"No matches found."}
    return {"results": results}

@app.get("/api/search")
def text_search(q: str = ""):
    log_hit("/api/search", q)
    ql = (q or "").strip().lower()
    if not ql: return {"results":[]}
    res = []
    for e in SEED:
        if ql in e["search_text"]:
            res.append({
                "id": e["id"],
                "title": e["title"],
                "artist": e["artist"],
                "youtube_search": e["youtube_search"],
                "derivatives": e.get("derivatives",[])
            })
    return {"results": res}

@app.post("/api/hum")
async def hum_match(payload: dict):
    log_hit("/api/hum", payload.get("semitone_seq", "") )
    seq = payload.get("semitone_seq", [])
    if not seq or len(seq) < 3:
        return JSONResponse({"error":"send semitone_seq of length >=3"}, status_code=400)
    
    scored = []
    for e in SEED:
        if e["semitones"].size == 0: continue
        dist = dtw_distance(seq, e["semitones"])
        scored.append((dist, e))
    
    scored.sort(key=lambda x: x[0])
    
    results = []
    for dist, e in scored[:5]:
        if math.isinf(dist) or dist > 8.0: continue
        results.append({
            "id": e["id"],
            "title": e["title"],
            "artist": e["artist"],
            "distance": round(dist, 2),
            "youtube_search": e.get("youtube_search"),
            "derivatives": e.get("derivatives", [])
        })
        
    if not results:
        return {"matches": [], "message":"No melody match found."}
    return {"matches": results}

@app.post("/api/check")
async def creator_check(payload: dict):
    # Re-using hum match logic for copyright check
    return await hum_match(payload)
