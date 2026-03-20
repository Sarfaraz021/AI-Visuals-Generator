"""
YouTube Thumbnail Generator — Redesigned
Run: streamlit run youtube_thumbnail_generator.py
Requires: pip install streamlit google-genai pillow python-dotenv
"""

import base64
import os
from io import BytesIO
from typing import List, Optional, Tuple

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

GEMINI_MODEL = "gemini-3.1-flash-image-preview"

THUMBNAIL_SYSTEM_PROMPT = """Role: You are an expert YouTube thumbnail art director creating high-performing, professional thumbnails.

Task:
- Generate one eye-catching, attractive, high-quality YouTube thumbnail image.
- Thumbnail must be native 16:9 and optimized for YouTube feed visibility.
- Use the user's VIDEO_TITLE as primary text source, with minimal text.

Critical rules:
1) Text rules:
- On-image text must be short and readable at small size (2-6 words preferred).
- Use words from VIDEO_TITLE only (or a short phrase clearly derived from it).
- Do not add random extra text, paragraphs, bullets, hashtags, or prices.

2) Creator image (if provided):
- If a creator image is provided, keep identity and face recognizable.
- You may change wardrobe, outfit, and styling if requested by the user context.
- Preserve realistic anatomy and natural facial proportions.

3) Reference image (if provided):
- Use reference image for concept/style guidance: composition, color mood, lighting, text placement style.
- Do not copy exact text from reference.
- Do not copy another person's face/identity from reference.
- If a person appears in reference and creator image is not provided, generate a unique person.

4) Design quality:
- Strong visual hierarchy.
- Clean, professional typography.
- High contrast between text and background.
- Avoid clutter.
- Keep focus on one clear hero subject.

5) Safety and consistency:
- No placeholder tokens like VIDEO_TITLE or HOOK on image.
- No logos unless explicitly provided in user assets or text context.
"""

PNG_MAGIC  = b"\x89PNG"
JPEG_MAGIC = b"\xff\xd8\xff"
WEBP_MAGIC = b"RIFF"
GIF_MAGIC  = b"GIF8"


def _is_valid_image_bytes(data: bytes) -> bool:
    return (
        data[:4] == PNG_MAGIC
        or data[:3] == JPEG_MAGIC
        or data[:4] == WEBP_MAGIC
        or data[:4] == GIF_MAGIC
    )


def image_to_bytes(image_file) -> Tuple[bytes, str]:
    raw  = image_file.read()
    mime = image_file.type or "image/png"
    return raw, mime


def build_thumbnail_prompt(
    video_title: str,
    video_description: str,
    extra_prompt: str,
    wardrobe_change: str,
) -> str:
    prompt = f"VIDEO_TITLE: {video_title.strip()}"
    if video_description.strip():
        prompt += f"\n\nVIDEO_DESCRIPTION:\n{video_description.strip()}"
    if extra_prompt.strip():
        prompt += f"\n\nEXTRA_CONTEXT:\n{extra_prompt.strip()}"

    prompt += "\n\nYOUTUBE_THUMBNAIL_REQUIREMENTS:\n- TARGET_ASPECT_RATIO: 16:9\n- TARGET_DIMENSIONS: 1280x720\n- STYLE: Eye-catching, professional, high CTR"

    if wardrobe_change.strip():
        prompt += (
            "\n\nCREATOR_STYLING_INSTRUCTION:\n"
            f"- {wardrobe_change.strip()}\n"
            "- Keep the same person identity while changing clothing/style as instructed."
        )
    return prompt


def generate_thumbnail_with_gemini(
    prompt_text: str,
    gemini_client: genai.Client,
    creator_image: Optional[Tuple[bytes, str]] = None,
    reference_images: Optional[List[Tuple[bytes, str]]] = None,
) -> Tuple[bytes, List[str]]:
    debug_log: List[str] = []
    parts: List[types.Part] = [types.Part.from_text(text=prompt_text)]

    if creator_image:
        parts.append(types.Part.from_text(text="[Context: The next image is the CREATOR IMAGE. Preserve identity; wardrobe/style changes are allowed if requested.]"))
        parts.append(types.Part.from_bytes(data=creator_image[0], mime_type=creator_image[1] or "image/png"))

    for idx, (raw, mime) in enumerate(reference_images or [], start=1):
        parts.append(types.Part.from_text(text=f"[Context: The next image is REFERENCE IMAGE {idx}. Use concept/style only. Do not copy text or identity.]"))
        parts.append(types.Part.from_bytes(data=raw, mime_type=mime or "image/png"))

    debug_log.append(f"Parts={len(parts)} | Creator={'yes' if creator_image else 'no'} | Refs={len(reference_images or [])}")

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=parts,
        config=types.GenerateContentConfig(
            system_instruction=THUMBNAIL_SYSTEM_PROMPT,
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    candidates = getattr(response, "candidates", []) or []
    debug_log.append(f"Candidates: {len(candidates)}")

    for candidate in candidates:
        content = getattr(candidate, "content", None)
        if not content:
            continue
        for part in (getattr(content, "parts", None) or []):
            inline = getattr(part, "inline_data", None)
            if not inline:
                continue
            data = getattr(inline, "data", None)
            if not data:
                continue
            if isinstance(data, bytes):
                img_bytes = data if _is_valid_image_bytes(data) else base64.b64decode(data)
            elif isinstance(data, str):
                img_bytes = base64.b64decode(data)
            else:
                continue
            if _is_valid_image_bytes(img_bytes):
                return img_bytes, debug_log

    raise ValueError("Gemini returned no valid image data.")


# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ThumbCraft — AI Thumbnail Studio",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
:root {
  --bg:         #0d0d0d;
  --surface:    #161616;
  --surface2:   #1e1e1e;
  --border:     rgba(255,255,255,0.08);
  --border2:    rgba(255,255,255,0.14);
  --orange:     #ff6b2b;
  --yellow:     #ffe44d;
  --green:      #4dff91;
  --text:       #f2f2f2;
  --muted:      #6b6b6b;
  --muted2:     #9a9a9a;
  --radius:     14px;
  --font-display: 'Bebas Neue', sans-serif;
  --font-body:    'DM Sans', sans-serif;
  --font-mono:    'JetBrains Mono', monospace;
}

/* ── RESET / BASE ── */
*, *::before, *::after { box-sizing: border-box; }

html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section[data-testid="stMain"],
[data-testid="stHeader"],
[data-testid="stToolbar"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.block-container {
    max-width: 760px !important;
    padding: 0 1.5rem 5rem !important;
}

#MainMenu, footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

h1,h2,h3,h4,h5,p,div,span,label {
    font-family: var(--font-body) !important;
    color: var(--text) !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }

/* ── FILM GRAIN OVERLAY ── */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
    background-size: 200px 200px;
    pointer-events: none;
    z-index: 9999;
    opacity: 0.4;
}

/* ── HERO HEADER ── */
.hero {
    padding: 3rem 0 2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
    position: relative;
}
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: var(--font-mono) !important;
    font-size: 0.62rem !important;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--orange) !important;
    background: rgba(255,107,43,0.08);
    border: 1px solid rgba(255,107,43,0.2);
    padding: 5px 12px;
    border-radius: 4px;
    margin-bottom: 1rem;
}
.hero-eyebrow::before {
    content: '';
    width: 5px; height: 5px;
    background: var(--orange);
    border-radius: 50%;
    animation: blink 1.8s ease-in-out infinite;
}
@keyframes blink {
    0%,100% { opacity:1; }
    50% { opacity:0.2; }
}
.hero-title {
    font-family: var(--font-display) !important;
    font-size: 5rem !important;
    font-weight: 400 !important;
    line-height: 0.9 !important;
    letter-spacing: 0.02em !important;
    color: var(--text) !important;
    margin: 0 0 0.6rem !important;
}
.hero-title .accent { color: var(--orange) !important; }
.hero-subtitle {
    font-family: var(--font-body) !important;
    font-size: 0.88rem !important;
    color: var(--muted2) !important;
    font-weight: 300 !important;
    letter-spacing: 0.01em;
    max-width: 480px;
}
.hero-model-tag {
    position: absolute;
    top: 3rem;
    right: 0;
    font-family: var(--font-mono) !important;
    font-size: 0.58rem !important;
    color: var(--muted) !important;
    letter-spacing: 0.1em;
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 4px 10px;
    border-radius: 4px;
}

/* ── SECTION HEADER ── */
.sect-head {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 2rem 0 1rem;
}
.sect-num {
    font-family: var(--font-mono) !important;
    font-size: 0.6rem !important;
    color: var(--orange) !important;
    background: rgba(255,107,43,0.1);
    border: 1px solid rgba(255,107,43,0.2);
    width: 26px; height: 26px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 6px;
    flex-shrink: 0;
}
.sect-title {
    font-family: var(--font-body) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--muted2) !important;
}
.sect-line {
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ── API KEY EXPANDER ── */
[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    margin-bottom: 0.5rem !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--font-mono) !important;
    font-size: 0.72rem !important;
    color: var(--muted2) !important;
    padding: 0.8rem 1rem !important;
}
[data-testid="stExpander"] summary:hover {
    color: var(--text) !important;
}

/* ── TEXT INPUTS ── */
[data-testid="stTextInput"] > div,
[data-testid="stTextArea"] > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    transition: border-color 0.2s !important;
}
[data-testid="stTextInput"] > div:focus-within,
[data-testid="stTextArea"] > div:focus-within {
    border-color: var(--orange) !important;
    box-shadow: 0 0 0 3px rgba(255,107,43,0.08) !important;
}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: transparent !important;
    border: none !important;
    color: var(--text) !important;
    font-family: var(--font-body) !important;
    font-size: 0.9rem !important;
    caret-color: var(--orange) !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: var(--muted) !important;
    font-style: italic;
    font-weight: 300;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    box-shadow: none !important;
    outline: none !important;
}

/* ── LABELS ── */
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stFileUploader"] label {
    font-family: var(--font-mono) !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--muted2) !important;
    margin-bottom: 6px !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] > div {
    background: var(--surface) !important;
    border: 1px dashed var(--border2) !important;
    border-radius: var(--radius) !important;
    transition: border-color 0.2s, background 0.2s !important;
}
[data-testid="stFileUploader"] > div:hover {
    background: var(--surface2) !important;
    border-color: var(--orange) !important;
}
[data-testid="stFileUploader"] span {
    font-family: var(--font-body) !important;
    font-size: 0.82rem !important;
    color: var(--muted2) !important;
}
[data-testid="stFileUploader"] small {
    font-family: var(--font-mono) !important;
    font-size: 0.6rem !important;
    color: var(--muted) !important;
}

/* ── DIVIDER ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 2rem 0 !important;
}

/* ── GENERATE BUTTON ── */
[data-testid="stButton"] > button[kind="primary"] {
    background: var(--orange) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-display) !important;
    font-size: 1.35rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.08em !important;
    padding: 1rem 2.5rem !important;
    text-transform: uppercase !important;
    transition: all 0.25s ease !important;
    cursor: pointer !important;
    width: 100% !important;
    position: relative;
    overflow: hidden;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #ff8147 !important;
    box-shadow: 0 12px 40px rgba(255,107,43,0.4) !important;
    transform: translateY(-2px) !important;
}
[data-testid="stButton"] > button[kind="primary"]:active {
    transform: translateY(0) !important;
    box-shadow: none !important;
}

/* ── SECONDARY BUTTON ── */
[data-testid="stButton"] > button:not([kind="primary"]) {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-body) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
    width: 100% !important;
}
[data-testid="stButton"] > button:not([kind="primary"]):hover {
    border-color: var(--orange) !important;
    color: var(--orange) !important;
    background: rgba(255,107,43,0.06) !important;
}

/* ── STATUS BOX ── */
[data-testid="stStatus"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.72rem !important;
}

/* ── ERROR / WARNING / INFO ── */
[data-testid="stAlert"] {
    background: var(--surface) !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-body) !important;
    font-size: 0.82rem !important;
}

/* ── IMAGE DISPLAY ── */
[data-testid="stImage"] img {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
}

/* ── RESULT FRAME ── */
.result-wrap {
    background: var(--surface);
    border: 1px solid var(--border2);
    border-radius: 18px;
    padding: 1.5rem;
    margin-top: 1.5rem;
}
.result-label {
    font-family: var(--font-mono) !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--orange) !important;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.result-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ── CAPTION TEXT ── */
[data-testid="stCaptionContainer"] p {
    font-family: var(--font-mono) !important;
    font-size: 0.62rem !important;
    color: var(--muted) !important;
    letter-spacing: 0.05em;
}

/* ── PREVIEW CHIPS ── */
.preview-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 0.6rem;
}
.preview-chip {
    font-family: var(--font-mono);
    font-size: 0.58rem;
    color: var(--muted2);
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 100px;
    padding: 3px 10px;
    letter-spacing: 0.08em;
}

/* ── FOOTER ── */
.footer {
    text-align: center;
    padding: 3rem 0 1rem;
    border-top: 1px solid var(--border);
    margin-top: 3rem;
}
.footer p {
    font-family: var(--font-mono) !important;
    font-size: 0.6rem !important;
    color: var(--muted) !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.footer span { color: var(--orange) !important; }
</style>
""", unsafe_allow_html=True)


# ─── HERO ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
    <div class="hero-model-tag">MODEL // {GEMINI_MODEL}</div>
    <div class="hero-eyebrow">AI Thumbnail Studio</div>
    <div class="hero-title">THUMB<span class="accent">CRAFT</span></div>
    <div class="hero-subtitle">
        Generate scroll-stopping YouTube thumbnails with Gemini AI —
        upload your photo, drop a reference, ship in seconds.
    </div>
</div>
""", unsafe_allow_html=True)


# ─── SECTION: API KEY ──────────────────────────────────────────────────────────
st.markdown("""
<div class="sect-head">
    <div class="sect-num">00</div>
    <div class="sect-title">API Configuration</div>
    <div class="sect-line"></div>
</div>
""", unsafe_allow_html=True)

with st.expander("🔑  Gemini API Key", expanded=not bool(os.getenv("GEMINI_API_KEY"))):
    gemini_key = st.text_input(
        "Gemini API Key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        placeholder="AIza...",
        label_visibility="collapsed",
    )

# ─── SECTION: VIDEO INFO ───────────────────────────────────────────────────────
st.markdown("""
<div class="sect-head">
    <div class="sect-num">01</div>
    <div class="sect-title">Video Details</div>
    <div class="sect-line"></div>
</div>
""", unsafe_allow_html=True)

video_title = st.text_input(
    "Video Title *",
    placeholder="e.g.  Google Stitch is HERE! Design UI in Minutes",
)

video_description = st.text_area(
    "Video Description",
    placeholder="Briefly describe topic, audience, mood…",
    height=100,
)

extra_prompt = st.text_area(
    "Extra Visual Direction",
    placeholder="Props, background style, color mood, special elements…",
    height=80,
)

wardrobe_change = st.text_input(
    "Dress / Styling Instruction",
    placeholder="e.g.  Dark plain t-shirt, warm cinematic backlight, serious expression",
)

# ─── SECTION: IMAGES ───────────────────────────────────────────────────────────
st.markdown("""
<div class="sect-head">
    <div class="sect-num">02</div>
    <div class="sect-title">Images</div>
    <div class="sect-line"></div>
</div>
""", unsafe_allow_html=True)

col_a, col_b = st.columns(2, gap="medium")

with col_a:
    creator_upload = st.file_uploader(
        "Your Photo (Creator)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=False,
        help="Your face will be preserved. Outfit can be changed via styling instruction.",
    )
    if creator_upload:
        st.image(creator_upload, use_container_width=True)
        st.markdown(f'<div class="preview-chip">✓ Creator image loaded</div>', unsafe_allow_html=True)

with col_b:
    reference_uploads = st.file_uploader(
        "Reference Thumbnail(s)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        help="Provide 1–3 thumbnails for layout/style inspiration.",
    )
    if reference_uploads:
        cols = st.columns(min(2, len(reference_uploads)))
        for i, img in enumerate(reference_uploads):
            with cols[i % len(cols)]:
                st.image(img, use_container_width=True)
        st.markdown(f'<div class="preview-chip">✓ {len(reference_uploads)} reference(s) loaded</div>', unsafe_allow_html=True)

# ─── GENERATE ──────────────────────────────────────────────────────────────────
st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
generate_btn = st.button("⚡  Generate Thumbnail", type="primary", use_container_width=True)

if generate_btn:
    if not video_title.strip():
        st.error("⚠️  Video title is required.")
        st.stop()
    if not gemini_key.strip():
        st.error("⚠️  Gemini API key is required.")
        st.stop()

    gemini_client = genai.Client(api_key=gemini_key.strip())

    creator_image_data: Optional[Tuple[bytes, str]] = None
    if creator_upload:
        creator_upload.seek(0)
        creator_image_data = image_to_bytes(creator_upload)

    refs_data: List[Tuple[bytes, str]] = []
    for ref in (reference_uploads or []):
        ref.seek(0)
        refs_data.append(image_to_bytes(ref))

    prompt_text = build_thumbnail_prompt(
        video_title=video_title,
        video_description=video_description,
        extra_prompt=extra_prompt,
        wardrobe_change=wardrobe_change,
    )

    with st.status("⚙️  Generating with Gemini…", expanded=True) as status:
        try:
            image_bytes, debug_log = generate_thumbnail_with_gemini(
                prompt_text=prompt_text,
                gemini_client=gemini_client,
                creator_image=creator_image_data,
                reference_images=refs_data,
            )
            with st.expander("Debug log"):
                for line in debug_log:
                    st.text(line)
            status.update(label="✅  Thumbnail generated!", state="complete")
        except Exception as exc:
            status.update(label="❌  Generation failed", state="error")
            st.error(f"Error: {exc}")
            st.stop()

    # ── RESULT ──
    st.markdown('<div class="result-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="result-label">Generated Thumbnail</div>', unsafe_allow_html=True)

    try:
        image = Image.open(BytesIO(image_bytes))
    except Exception as exc:
        st.error(f"Could not decode image: {exc}")
        st.stop()

    st.image(image, use_container_width=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    out = BytesIO()
    image.save(out, format="PNG")
    st.download_button(
        "⬇  Download PNG",
        data=out.getvalue(),
        file_name="thumbcraft_thumbnail.png",
        mime="image/png",
        use_container_width=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    <p>ThumbCraft · Powered by <span>Gemini AI</span> · Built for creators</p>
</div>
""", unsafe_allow_html=True)