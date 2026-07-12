"""
StudyGenie — AI Study Notes Generator
--------------------------------------
Converts any PDF (textbook, paper, lecture notes) into:
  - a map-reduce generated summary
  - exam-ready key points
  - an interactive MCQ quiz
  - flip-card flashcards

Built with Streamlit + Google Gemini API + pypdf.
"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from utils.pdf_extractor import extract_text_from_pdf, estimate_reading_stats
from utils.gemini_client import GeminiClient, GeminiGenerationError
from utils.summarizer import chunk_text, map_summarize_chunk, reduce_summaries, generate_key_points
from utils.quiz_flashcards import generate_mcq_quiz, generate_flashcards
from ui_components import build_flashcard_html, build_quiz_html

# --------------------------------------------------------------------------
# Page config + styling
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="StudyGenie | AI Study Notes Generator",
    page_icon="🧞‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


load_css()

# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
DEFAULTS = {
    "full_text": None,
    "num_pages": 0,
    "summary": None,
    "key_points": None,
    "quiz": None,
    "flashcards": None,
    "processing_done": False,
    "file_name": None,
    "last_used_model": None,
}
for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --------------------------------------------------------------------------
# Sidebar — configuration
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## StudyGenie")
    st.caption("AI Study Notes Generator")
    st.divider()

    # Prefer a key stored in Streamlit secrets (recommended for deployment),
    # but always let the user override it in the UI.
    secret_key = ""
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        secret_key = ""

    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        value=st.session_state.get("api_key", secret_key),
        help="Get a free key at aistudio.google.com/app/apikey. "
             "For deployment, store it in Streamlit Secrets as GEMINI_API_KEY instead.",
    )
    if api_key:
        st.session_state["api_key"] = api_key

    st.divider()
    st.markdown("### ⚙️ Generation Settings")
    summary_style = st.select_slider(
        "Summary depth",
        options=["brief", "detailed", "comprehensive"],
        value="detailed",
    )
    num_key_points = st.slider("Key points", 5, 20, 10)
    num_quiz = st.slider("Quiz questions", 4, 15, 8)
    num_cards = st.slider("Flashcards", 5, 20, 10)

    st.divider()
    st.markdown(
        """
        <div style="font-size:13px; opacity:0.75; line-height:1.6;">
        <b>How it works</b><br>
        1. Extracts text with <code>pypdf</code><br>
        2. Chunks &amp; summarizes (map step)<br>
        3. Merges into one summary (reduce step)<br>
        4. Generates key points, quiz &amp; flashcards<br>
        5. Falls back across Gemini models if one is rate-limited
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption("Built with Python · Streamlit · Google Gemini API · pypdf")

# --------------------------------------------------------------------------
# Ambient background layer (floating light motes, purely decorative)
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="ambient-layer" aria-hidden="true">
        <span class="mote"></span><span class="mote"></span><span class="mote"></span>
        <span class="mote"></span><span class="mote"></span>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Hero header — the genie's lamp is the page's signature element
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero fade-in">
        <div class="lamp-wrap" aria-hidden="true">
            <div class="lamp-glow"></div>
            <svg class="lamp-icon" viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="lampGrad" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="#ffe9a8"/>
                        <stop offset="55%" stop-color="#e8b84b"/>
                        <stop offset="100%" stop-color="#8a6420"/>
                    </linearGradient>
                </defs>
                <path d="M20 60 Q8 38 36 34 Q32 18 58 16 Q98 13 102 40 Q104 56 84 59 Q58 66 20 60 Z" fill="url(#lampGrad)"/>
                <ellipse cx="28" cy="59" rx="15" ry="6.5" fill="url(#lampGrad)"/>
                <circle class="lamp-bulb" cx="56" cy="29" r="7" fill="#ffe9a8"/>
            </svg>
            <span class="sparkle s1">✦</span>
            <span class="sparkle s2">✧</span>
            <span class="sparkle s3">✦</span>
        </div>
        <h1>StudyGenie</h1>
        <p class="subtitle">Turn any PDF into summaries, key points, quizzes &amp; flashcards — instantly.</p>
        <div class="badges">
            <span class="badge">Any PDF</span>
            <span class="badge">Map-Reduce Summarization</span>
            <span class="badge">Model Fallback</span>
            <span class="badge">Auto MCQ Quiz</span>
            <span class="badge">Flashcards</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Upload
# --------------------------------------------------------------------------
st.markdown('<div class="upload-card fade-in">', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Slide a document under the lamp — textbook chapter, research paper, lecture notes...",
    type=["pdf"],
)
st.markdown("</div>", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    generate_clicked = st.button(
        "✨ Generate Study Materials",
        disabled=not (uploaded_file and st.session_state.get("api_key")),
        use_container_width=True,
    )
with col2:
    if st.session_state.processing_done:
        if st.button("🗑️ Clear results", use_container_width=True):
            for key, default in DEFAULTS.items():
                st.session_state[key] = default
            st.rerun()

if uploaded_file and not st.session_state.get("api_key"):
    st.info("👈 Enter your Gemini API key in the sidebar to enable generation.")

# --------------------------------------------------------------------------
# Generation pipeline
# --------------------------------------------------------------------------
if generate_clicked:
    try:
        client = GeminiClient(st.session_state["api_key"])

        with st.status("Reading your PDF...", expanded=True) as status:
            text, num_pages = extract_text_from_pdf(uploaded_file)

            if not text.strip():
                status.update(label="No extractable text found in this PDF.", state="error")
                st.error(
                    "This PDF doesn't contain selectable text (it may be a scanned image). "
                    "Try a text-based PDF instead."
                )
                st.stop()

            st.session_state.full_text = text
            st.session_state.num_pages = num_pages
            st.session_state.file_name = uploaded_file.name
            stats = estimate_reading_stats(text)
            status.write(
                f"✅ Extracted **{stats['word_count']:,} words** from **{num_pages} pages**."
            )

            status.write("✂️ Chunking document for map-reduce summarization...")
            chunks = chunk_text(text)
            status.write(f"✅ Split into **{len(chunks)} chunk(s)**.")

            status.write("🧩 MAP step — summarizing each chunk...")
            progress = st.progress(0.0)
            chunk_summaries = []
            for i, c in enumerate(chunks):
                s = map_summarize_chunk(client, c, i, len(chunks))
                chunk_summaries.append(s)
                progress.progress((i + 1) / max(len(chunks), 1))
            status.write("✅ All chunks summarized.")

            status.write("🧠 REDUCE step — merging into one cohesive summary...")
            final_summary = reduce_summaries(client, chunk_summaries, style=summary_style)
            st.session_state.summary = final_summary
            status.write("✅ Final summary ready.")

            status.write("🔑 Extracting key points...")
            st.session_state.key_points = generate_key_points(client, final_summary, num_key_points)
            status.write("✅ Key points ready.")

            status.write("❓ Generating MCQ quiz...")
            st.session_state.quiz = generate_mcq_quiz(client, final_summary, num_quiz)
            status.write("✅ Quiz ready.")

            status.write("🗂️ Building flashcards...")
            st.session_state.flashcards = generate_flashcards(client, final_summary, num_cards)
            status.write("✅ Flashcards ready.")

            st.session_state.last_used_model = client.last_used_model
            st.session_state.processing_done = True
            status.update(label="All done! 🎉", state="complete", expanded=False)

    except GeminiGenerationError as e:
        st.error("⚠️ Gemini generation failed after trying every model in the fallback chain.")
        st.code(str(e), language=None)
        st.caption(
            "If every model 404s, your API key may not have access to these model names yet, "
            "or the key itself may be invalid — double-check it at aistudio.google.com/app/apikey."
        )
    except ValueError as e:
        st.error(f"⚠️ {e}")
    except Exception as e:  # noqa: BLE001
        st.error(f"⚠️ Something went wrong: {e}")

# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
if st.session_state.processing_done:
    st.markdown(
        f"""
        <div class="fade-in" style="margin: 1.2rem 0;">
            <span class="stat-pill">📄 {st.session_state.file_name}</span>
            <span class="stat-pill">📃 {st.session_state.num_pages} pages</span>
            <span class="stat-pill">🤖 {st.session_state.last_used_model or 'Gemini'}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_summary, tab_points, tab_quiz, tab_cards = st.tabs(
        ["📝 Summary", "🔑 Key Points", "❓ Quiz", "🗂️ Flashcards"]
    )

    with tab_summary:
        st.markdown(
            f'<div class="paper-card fade-in">{st.session_state.summary}</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇️ Download Summary (.txt)",
            st.session_state.summary or "",
            file_name=f"{Path(st.session_state.file_name or 'summary').stem}_summary.txt",
        )

    with tab_points:
        if st.session_state.key_points:
            for i, kp in enumerate(st.session_state.key_points):
                st.markdown(
                    f'<div class="key-point fade-in" style="animation-delay:{i * 0.05}s">✅ {kp}</div>',
                    unsafe_allow_html=True,
                )
            points_text = "\n".join(f"- {kp}" for kp in st.session_state.key_points)
            st.download_button(
                "⬇️ Download Key Points (.txt)",
                points_text,
                file_name=f"{Path(st.session_state.file_name or 'notes').stem}_key_points.txt",
            )
        else:
            st.warning("Key points could not be generated. Try regenerating.")

    with tab_quiz:
        if st.session_state.quiz:
            st.caption("Click an option to answer — you'll get instant feedback and an explanation.")
            html = build_quiz_html(st.session_state.quiz)
            components.html(html, height=560, scrolling=True)
        else:
            st.warning("Quiz could not be generated. Try regenerating.")

    with tab_cards:
        if st.session_state.flashcards:
            st.caption("Click a card to flip it. Use Shuffle to randomize the deck.")
            html = build_flashcard_html(st.session_state.flashcards)
            components.html(html, height=460, scrolling=False)
        else:
            st.warning("Flashcards could not be generated. Try regenerating.")

st.markdown(
    '<div class="footer-note">StudyGenie · Built with Streamlit &amp; Google Gemini API</div>',
    unsafe_allow_html=True,
)
