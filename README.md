Fuzzy Memory - The Recall Context Engine
Problem: Have you ever had a song or a movie scene or a quote or book context stuck in your head but couldn't remember the name? You know the vibe "that sad rain scene from the 90s" or you can hum the tune, but standard keyword search fails you.

Fuzzy Memory is a lightweight recall engine that helps users retrieve information from incomplete memory cues such as humming, vague text, or metadata fragments.
Powered by Cloud Run, FastAPI, and Gemini reasoning.

Features:

Hum based recall using semitone extraction and Dynamic Time Warping.
Vague text interpretation using Gemini.
Structured metadata lookup from a small seed dataset.
Cloud Run backend that acts as a recall agent.
Clean and simple UI for demo purposes.
Early foundation for creator compliance and similarity checks.


Components

Frontend UI
Cloud Run backend (FastAPI)
Seed dataset (JSON or optional MongoDB Atlas)
Optional Cloud Storage for audio
Gemini (Vertex AI) for reasoning

Tech Stack

Backend: Python, FastAPI, Uvicorn
AI Layer: Gemini API (Vertex AI)
Audio Processing: Dynamic Time Warping
Containerization: Docker
Cloud: Google Cloud Run, Cloud Storage
Database: JSON seed dataset (optional MongoDB Atlas)

Prerequisites

Python 3.9+
Docker
Google Cloud SDK
Vertex AI access
Optional: MongoDB Atlas

Installation

Clone the repository:
git clone https://github.com/<your-repo>/FuzzyMemory.git
cd FuzzyMemory

Install dependencies:
pip install -r requirements.txt

Run locally:
uvicorn app:app --reload

Docker Setup

Build the image:
docker build -t fuzzymemory .


Run the container:
docker run -p 8080:8080 fuzzymemory

Deploy to Cloud Run
gcloud run deploy fuzzymemory \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated


Roadmap

Planned enhancements include:
Larger audio and metadata collections
Academic and medical context recall
Vector database integration
Audio plagiarism and similarity detection
Reel and meme audio identification
Personalized recall history

Compliance

Only public domain melodies are used
Metadata is synthetic
User audio is processed only for matching and not stored
No copyrighted lyrics or commercial datasets are included
