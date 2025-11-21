# Fuzzy Memory - The Recall Context Engine

### ❓ The Problem
Have you ever had a song, movie scene, quote, or book context stuck in your head but couldn't remember the name? You know the *vibe*—*"that sad rain scene from the 90s"*—or you can hum the tune, but standard keyword search fails you.

### 💡 The Solution
**Fuzzy Memory** is a lightweight recall engine that helps users retrieve information from incomplete memory cues. It is powered by **Google Cloud Run**, **FastAPI**, and **Gemini reasoning** to bridge the gap between vague human memory and structured data.

---

### 🚀 Key Features
*   **Hum-based Recall:** Utilizes semitone extraction and Dynamic Time Warping (DTW) to match audio inputs.
*   **Vague Text Interpretation:** Leverages Gemini (Vertex AI) to understand context, mood, and "vibes."
*   **Structured Metadata Lookup:** Fast retrieval from a curated seed dataset.
*   **Agentic Backend:** Cloud Run acts as an intelligent recall agent orchestrating the flow.
*   **Clean UI:** A simple, intuitive interface designed for instant demos.
*   **Creator Tools:** Early foundation for copyright compliance and melody similarity checks.

---

### 🏗️ Components & Architecture
*   **Frontend:** Lightweight UI for audio capture and input.
*   **Backend:** FastAPI service running on Cloud Run.
*   **Data Layer:** JSON seed dataset (with support for optional MongoDB Atlas).
*   **Storage:** Optional Cloud Storage for audio artifacts.
*   **Reasoning Engine:** Gemini (Vertex AI) for semantic understanding.

### 🛠️ Tech Stack
*   **Backend:** Python, FastAPI, Uvicorn
*   **AI Layer:** Gemini API (Vertex AI)
*   **Audio Processing:** SciPy, Dynamic Time Warping (DTW)
*   **Containerization:** Docker
*   **Cloud Infrastructure:** Google Cloud Run, Cloud Storage
*   **Database:** In-Memory JSON (MVP) / MongoDB Atlas (Production)

---

### 📋 Prerequisites
Before running the project, ensure you have:
*   Python 3.9+
*   Docker installed
*   Google Cloud SDK installed and authenticated
*   Access to Vertex AI API enabled
*   *(Optional)* MongoDB Atlas account

---

### ⚡ Installation & Local Setup

**1. Clone the repository:**
```bash
git clone https://github.com/<your-repo>/FuzzyMemory.git
cd FuzzyMemory
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Run locally:**
```bash
uvicorn app:app --reload
```

---

### 🐳 Docker & Cloud Deployment

**1. Build the Docker image:**
```bash
docker build -t fuzzymemory .
```

**2. Run the container locally:**
```bash
docker run -p 8080:8080 fuzzymemory
```

**3. Deploy to Google Cloud Run:**
```bash
gcloud run deploy fuzzymemory \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated
```

---

### 🗺️ Roadmap
*   [ ] Expand audio and metadata collections.
*   [ ] Add Academic and Medical context recall domains.
*   [ ] Implement Vector Database (pgvector) integration.
*   [ ] Develop advanced audio plagiarism and similarity detection.
*   [ ] Add identification for Reels and Meme audio.
*   [ ] Implement personalized recall history.

### ⚖️ Compliance
*   **Melodies:** Only public domain melodies are used for the demo.
*   **Metadata:** Synthetic data used for testing purposes.
*   **Privacy:** User audio is processed for matching only and is not permanently stored.
*   **Copyright:** No copyrighted lyrics or commercial datasets are included.
