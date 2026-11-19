# Clipper v2 — AI-Powered Automated Clipper Agent

Free, automated AI clipper agent with a mobile-first dark glassmorphism web dashboard.
Turn long YouTube videos into 3–5 vertical (1080×1920) captioned 20–45s clips, scored for virality, stored in Cloudflare R2 / Google Drive, and optionally scheduled and posted to Instagram Reels.

Runs 100% on free tiers:
- **Dashboard & API**: FastAPI + built React SPA deployed on Render (free tier, sleeps after 15m idle).
- **Worker Pipeline**: GitHub Actions (free 2,000 min/month runner).
- **Database**: Firebase Firestore & Auth (free Spark tier).
- **Storage**: Cloudflare R2 (10 GB free) or personal Google Drive (OAuth 2.0).
- **AI Models**: Groq Whisper API (`whisper-large-v3-turbo` with local fallback) + Gemini API (`gemini-2.0-flash` free tier).

---

## 15-Minute Setup Guide

### 1. Firebase Project Setup (Firestore + Auth)
1. Go to the [Firebase Console](https://console.firebase.google.com/) and create a free project.
2. In **Build > Firestore Database**, click **Create database** (start in production mode).
3. In **Build > Authentication**, enable **Google Sign-In** provider.
4. In **Project Settings > Service accounts**, click **Generate new private key**. Download the JSON file. Copy its entire raw content string into `FIREBASE_SA_JSON`.
5. In **Project Settings > General**, under *Your apps*, click the web icon (`</>`) to create a web app. Copy the `firebaseConfig` object as a JSON string for `FIREBASE_WEB_CONFIG`.

### 2. Free AI API Keys
- **Groq Whisper API**: Get a free API key at [console.groq.com](https://console.groq.com/).
- **Google Gemini API**: Get a free API key at [aistudio.google.com](https://aistudio.google.com/).

### 3. Video Storage Setup (R2 or Google Drive)

#### Option A: Cloudflare R2 (Recommended)
1. In Cloudflare Dashboard, navigate to **R2**.
2. Create a bucket named `clipper-clips`.
3. Under **Manage R2 API Tokens**, create a token with Object Read & Write permissions.
4. Note your `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, and `R2_SECRET_ACCESS_KEY`.
5. Under bucket settings, enable a public domain or R2.dev domain for playback (`R2_PUBLIC_URL`).

#### Option B: Google Drive (Personal Account)
1. In Google Cloud Console, create OAuth 2.0 credentials (Desktop Application).
2. Run the included helper script locally:
   ```bash
   python scripts/gdrive_auth.py
   ```
3. Follow the prompt to authorize your personal account and save `GDRIVE_REFRESH_TOKEN` and `GDRIVE_FOLDER_ID`.

### 4. GitHub Actions Secrets
In your GitHub repository, go to **Settings > Secrets and variables > Actions** and add the following repository secrets:
- `FIREBASE_SA_JSON`: Raw JSON of your Firebase service account.
- `GROQ_API_KEY`: Groq API key.
- `GEMINI_API_KEY`: Gemini API key.
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_PUBLIC_URL` (or Google Drive credentials).
- `IG_USERNAME`, `IG_PASSWORD`, `IG_PROXY` (optional, for Instagram Reel posting).

Create a GitHub Personal Access Token (Fine-grained PAT with Actions Read & Write on this repository) for the Render dashboard to trigger runs:
- `GITHUB_TOKEN`: Fine-grained PAT.
- `GITHUB_REPO`: `owner/repo`.

### 5. Deploy to Render (Dashboard Web Service)
1. Fork or push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/), click **New > Blueprint** and connect this repository (using `render.yaml`), or create a **New Web Service** pointing to the `Dockerfile`.
3. Fill in the environment variables:
   - `ALLOWED_EMAIL`: Your Google account email address.
   - `FIREBASE_SA_JSON`: Firebase service account JSON.
   - `FIREBASE_WEB_CONFIG`: Public Firebase web config JSON.
   - `GITHUB_TOKEN` & `GITHUB_REPO`.
4. Deploy! Render will build the React SPA and serve it from FastAPI with cold-start tolerance.

---

## Local Development & Testing

### Running the Worker CLI Locally (Dry Run)
You can test the entire clipping pipeline locally on any YouTube URL:

```bash
# 1. Install worker dependencies
pip install -r requirements-worker.txt

# 2. Run local dry run on any video
python -m worker.main --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --dry-run
```

Clips with word-highlighted ASS subtitles and 540×960 thumbnails with dominant accent colors will be rendered to `./output/`.

### Running Unit Tests
```bash
pytest tests/ -v
```

### Running Dashboard Locally
```bash
# Terminal 1: Backend
uvicorn server.app:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` to interact with the mobile-first dashboard.

---

## Firestore Schema Reference

- `config/main`: Global settings (dry run, auto post, clips count, storage backend, retention).
- `jobs/{id}`: Pipeline status (`queued` -> `downloading` -> `transcribing` -> `selecting` -> `rendering` -> `uploading` -> `posting` -> `done`/`failed`).
- `clips/{id}`: Rendered vertical clips metadata, virality scores, thumbnail URLs, captions.
- `posted/{clip_hash}`: Dedup ledger to prevent reposting the same clip.
- `state/instagram`: Session credentials, rate limits, daily post counters.
- `notifications/{id}`: Alert notifications for job completion and Instagram challenges.

---

## License
MIT. Only process content you own or have permission to use.

