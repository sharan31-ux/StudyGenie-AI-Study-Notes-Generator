# 🧞‍♂️ StudyGenie — AI Study Notes Generator

Turn any PDF (textbook chapter, research paper, lecture notes) into:

- 📝 A concise, well-organized **summary**
- 🔑 Exam-ready **key points**
- ❓ An interactive **MCQ quiz** with instant feedback and scoring
- 🗂️ Flip-style **flashcards** for quick revision

Built with **Python, Streamlit, Google Gemini API, and pypdf**, with a
custom glassmorphism / animated-gradient UI and a model-fallback layer
for reliable generation even under rate limits.

---

## ✨ Features

- **PDF text extraction** — handles multi-page PDFs via `pypdf`, gracefully
  skips unreadable pages, and detects password-protected/scanned PDFs.
- **Map-reduce summarization** — large documents are chunked, each chunk is
  summarized independently (MAP), then merged into one cohesive summary (REDUCE),
  so the app scales to long documents without blowing past context limits.
- **Model-fallback layer** — every generation call walks a prioritized list of
  Gemini models (`gemini-2.5-flash → gemini-2.0-flash → ...`) with retries and
  backoff, so a single rate-limited/overloaded model never breaks the pipeline.
- **Interactive quiz** — custom HTML/CSS/JS widget with click-to-answer options,
  color-coded correct/incorrect feedback, per-question explanations, a progress
  bar, and an animated circular score ring at the end.
- **Flip flashcards** — 3D CSS flip animation, shuffle, and prev/next navigation,
  rendered as a self-contained interactive widget (no page reloads).
- **Beautiful, on-theme UI** — animated gradient background, glassmorphism
  cards, gradient text, smooth fade-in animations, and a fully custom dark theme.
- **Downloadable output** — export the summary and key points as `.txt` files.

---

## 🏗️ Architecture

```
studygenie/
├── app.py                     # Streamlit app: UI, session state, pipeline orchestration
├── ui_components.py           # Self-contained HTML/CSS/JS widgets (flashcards, quiz)
├── requirements.txt
├── README.md
├── .streamlit/
│   ├── config.toml            # Theme configuration
│   └── secrets.toml.example   # Template for storing your Gemini API key
├── assets/
│   └── style.css              # Animated background, glass cards, buttons, tabs
└── utils/
    ├── pdf_extractor.py        # pypdf-based text extraction + reading stats
    ├── gemini_client.py        # Gemini API wrapper + model-fallback layer
    ├── summarizer.py            # Map-reduce summarization + key point extraction
    └── quiz_flashcards.py       # MCQ quiz + flashcard generation (robust JSON parsing)
```

**Pipeline flow (triggered by the "Generate" button):**

1. Extract raw text from the uploaded PDF (`pypdf`).
2. Chunk the text (with overlap) so each Gemini call stays fast and well within context limits.
3. **MAP** — summarize each chunk independently.
4. **REDUCE** — merge all chunk summaries into one cohesive final summary.
5. Derive key points, an MCQ quiz, and flashcards from the final summary.
6. Render everything in tabs with interactive widgets.

---

## 🚀 Getting Started (Local)

### 1. Clone / copy the project and install dependencies

```bash
cd studygenie
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get a free Gemini API key

Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey),
create a key, and either:

- Paste it directly into the sidebar text box when the app is running, **or**
- Create `.streamlit/secrets.toml` (copy from `secrets.toml.example`) and set:
  ```toml
  GEMINI_API_KEY = "your-key-here"
  ```

### 3. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## ☁️ Deploying to Streamlit Community Cloud (Free)

1. Push this project to a **public (or private) GitHub repository**.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **"New app"**, select your repo/branch, and set the main file to `app.py`.
4. Under **"Advanced settings" → "Secrets"**, paste:
   ```toml
   GEMINI_API_KEY = "your-key-here"
   ```
5. Click **Deploy**. Your app will be live at `https://<your-app-name>.streamlit.app`.

That's it — no server management, and it auto-redeploys on every push to the branch.

---

## 🧰 Tech Stack

| Layer            | Tool |
|-------------------|------|
| UI / App framework | Streamlit |
| Styling            | Custom CSS (animated gradients, glassmorphism, keyframe animations) |
| Interactivity      | Vanilla JS widgets via `streamlit.components.v1.html` |
| PDF parsing        | pypdf |
| LLM                | Google Gemini API (`google-genai` SDK) |
| Reliability        | Model-fallback layer with retry/backoff |
| Hosting            | Streamlit Community Cloud |

---

## 📌 Notes & Limitations

- Scanned/image-only PDFs won't extract text (no OCR is included in this version).
- Password-protected PDFs are detected and rejected with a clear message.
- Generation quality depends on the underlying Gemini model and document clarity.
- Your Gemini API key is only used server-side for API calls and is never logged.

---

## 💼 Overall Description

> **StudyGenie – AI Study Notes Generator** | Python, Streamlit, Google Gemini API, pypdf
> - Built an AI-powered study assistant that converts any PDF (textbooks, papers,
>   lecture notes) into concise summaries, key-point notes, auto-generated MCQ
>   quizzes, and flashcards.
> - Implemented PDF text extraction with map-reduce summarization for large
>   documents and a model-fallback layer for reliable generation; designed a
>   fully custom, animated glassmorphism UI with interactive quiz/flashcard
>   widgets; deployed as an interactive web app on Streamlit Community Cloud.

---
