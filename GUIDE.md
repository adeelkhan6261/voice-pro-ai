# 🎙️ Voice Pro — AI Voiceover Studio

Professional, high-quality AI voiceovers with local processing.

---

## 💻 Local Running Guide

### 1. Prerequisites
- **Python**: Install Python 3.10 or higher.
- **FFmpeg**: Required for stitching audio chunks. [Download here](https://ffmpeg.org/download.html).

### 2. Installation
Open your terminal in the `voice_pro` folder and run:
```bash
pip install -r requirements.txt
```

### 3. Start the Server
Run the following command:
```bash
python main.py
```

### 4. Access the UI
Open your web browser and go to:
**`http://localhost:5000`**

---

## 🚀 Deployment Guide (Hugging Face Spaces)

This tool is ready to be hosted for free on Hugging Face using **Docker**.

### 1. Create a Space
- Go to [huggingface.co/new-space](https://huggingface.co/new-space).
- **Select SDK**: Choose **Docker** (very important!).
- **Template**: **Blank**.

### 2. Upload Files
Upload all files from this folder except for `__pycache__` and existing `outputs`.

### 3. Automatic Build
Hugging Face will automatically find the `Dockerfile` and build your app. Once finished, your studio will be live 24/7!

---

## 🛠️ Troubleshoot & Fixes

### Rate/Pitch "Normal" Fix
> [!IMPORTANT]
> Some versions of `edge-tts` fail if you send `0%` rate. **I have fixed this in `engine.py` and `app.js`**, so "Normal" (0) speed will now work perfectly by automatically sending `+0%`.

### Large Scripts
For scripts up to **30,000 words**, the tool processes in chunks and then joins them. On low-end systems, this may take a few minutes. Don't close the browser until it's finished!

---

**Developed with ❤️ and AI.**
