# Persona — AI-Powered Story-to-Video Studio

> Turn your moments into cinematic stories.
> Upload media → Generate AI audio → Create beat-synced videos — all in one flow.

---

## Overview

**Persona** is a full-stack AI application that allows users to:

1. Upload **images, videos, or audio**
2. Generate **custom music/audio using AI (Wubble API)**
3. Convert that audio + media into **short-form videos**
4. Automatically **sync cuts to beats** using the Beat Sync engine

Designed for creators, marketers, and anyone who wants to produce **high-quality social media content instantly**.

---

## Core Features

### 1. AI Audio Generation

* Powered by **Wubble API**
* Generates:

  * Background music
  * Cinematic audio stories
* Input:

  * Text prompt
  * Image / Video / Audio

---

### 2. Multi-Modal Input

Users can upload:

* Images (JPG, PNG)
* Videos (MP4, MOV)
* Audio (MP3, WAV)

Mixed media supported for richer storytelling

---

### 3. Intelligent Story Generation

* Combines user input + prompt
* Produces:

  * AI-generated soundtrack
  * Emotion-aware audio

---

### 4. Automated Video Creation

* Converts media into video using:

  * AI planning
  * FFmpeg pipeline
* Outputs platform-ready MP4

---

### 5. Beat Sync Engine (Highlight Feature)

Automatically aligns video cuts with music beats.

#### How it works:

* Extracts:

  * BPM (tempo)
  * Beat timestamps
  * Energy levels
* Applies:

  * Fast cuts on high energy
  * Longer clips on low energy

Result: **professional, rhythm-synced videos**

---

### 📱 6. Social Media Ready Output

| Platform                 | Resolution |
| ------------------------ | ---------- |
| Instagram Reels / TikTok | 1080×1920  |
| YouTube                  | 1920×1080  |
| Square                   | 1080×1080  |

---

## System Architecture

```text
User Input (Text + Media)
        ↓
Frontend (React)
        ↓
FastAPI Backend
        ↓
Wubble API (Audio Generation)
        ↓
Audio Analysis (librosa)
        ↓
AI Edit Planning (LLM)
        ↓
FFmpeg Rendering
        ↓
Beat-Synced Video Output
```

---

## Project Structure

```text
WUBBLE-SOLUTION/
│
├── backend/
│   ├── main.py
│   ├── utilities/
│   │   ├── beat_sync.py
│   │   ├── video.py
│   │   ├── file_upload.py
│   │   └── video_generator/
│   │
│   ├── wubble/
│   │   ├── chat.py
│   │   ├── get_response.py
│   │   └── user_creation.py
│   │
│   ├── uploads/
│   ├── outputs/
│   └── .env
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── vite.config.js
│
└── README.md
```

---

## API Endpoints

### 🔹 Health Check

```http
GET /
```

---

### 🔹 User Login

```http
POST /login
```

---

### 🔹 Generate Audio Story

```http
POST /upload
```

**FormData:**

* `prompt` (string)
* `file` (image/video/audio)

---

### 🔹 Generate Video

```http
POST /generate-video
```

---

### 🔹 Beat Sync Video 

```http
POST /generate-video/beat-sync
```

**FormData:**

* `req_id`
* `platform`
* `media[]`

**Response:**

* MP4 file
* Headers:

  * `X-BPM`
  * `X-Total-Cuts`
  * `X-Audio-Duration`

---

## Tech Stack

### Frontend

* React (Vite)
* Axios
* Custom UI + animations

### Backend

* FastAPI
* FFmpeg
* librosa
* Cloudinary (media storage)

### AI / APIs

* Wubble API (audio generation)
* Groq (edit planning)

---

## 🛠 Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/codemosaic7/persona.git
cd persona
```

---

### 2. Backend Setup

```bash
cd backend
python -m venv myenv
source myenv/bin/activate

pip install -r requirements.txt
```

---

### 3. Environment Variables

Create `.env`:

```env
WUBBLE_API_KEY=your_key
GROQ_API_KEY=your_key
CLOUDINARY_URL=your_url
```

---

### 4. Run Backend

```bash
uvicorn main:app --reload
```

---

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## Deployment

### Backend

* Render / Railway

### Frontend

* Vercel / Netlify

---

## Use Cases

* Content creators (Reels, TikTok)
* Marketing & ads
* AI-powered editing tools
* Social media automation

---

## Key Innovation

### Beat-Synced Video Generation

Persona doesn’t just create videos — it creates **rhythm-aware experiences**.

- Every cut matches the music
- Every transition feels intentional

---

## Limitations

* Requires processing time for video rendering
* Large files may slow down generation
* Backend needs FFmpeg installed

---

## Future Improvements

* Real-time preview before rendering
* AI scene detection
* Auto subtitles
* Style templates
* Music genre selection UI

---

## Author

Built by **Manika** 
For Wubble Hackathon

---

## Conclusion

Persona simplifies content creation:

> Upload → Generate → Sync → Share

From raw memories to **social-ready videos in seconds**.

Example execution


https://github.com/user-attachments/assets/5933960d-2cd9-49a8-9cd8-5836ca8b74c8


<video controls src="Screencast From 2026-04-07 23-07-12.mp4" title="Title"></video>

---
