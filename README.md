# YouTube Thumbnail Generator (ThumbCraft)

This document explains how to set up and run `youtube_thumbnail_generator.py` on your machine to generate YouTube thumbnails with Google Gemini.

## What you need

- **Python 3.10+** (3.11 or 3.12 recommended)
- **pip** (comes with Python)
- A **Google AI (Gemini) API key** with access to image generation models (e.g. `gemini-3.1-flash-image-preview` as used in the script)

## 1. Get the code

Either clone this repository or copy only `youtube_thumbnail_generator.py` into a folder on your computer.

## 2. Create a virtual environment (recommended)

From the folder that contains `youtube_thumbnail_generator.py`:

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```bash
pip install --upgrade pip
pip install streamlit google-genai pillow python-dotenv
```

These match the imports at the top of `youtube_thumbnail_generator.py`.

## 4. Configure the API key

**Option A — environment variable (recommended)**

```bash
export GEMINI_API_KEY="YOUR_KEY_HERE"
```

On Windows (PowerShell):

```powershell
$env:GEMINI_API_KEY="YOUR_KEY_HERE"
```

**Option B — `.env` file**

In the same directory as the script, create a file named `.env` with:

```
GEMINI_API_KEY=YOUR_KEY_HERE
```

The app uses `python-dotenv` and will load this when the app starts.

You can also paste the key in the Streamlit UI under **API Configuration** if you prefer not to use env vars.

## 5. Run the app

From the directory that contains `youtube_thumbnail_generator.py`:

```bash
streamlit run youtube_thumbnail_generator.py
```

Your browser should open to a local URL (usually `http://localhost:8501`). If it does not, copy the URL printed in the terminal.

## 6. How to use the UI

1. Enter your **Gemini API key** in the expander if it is not already set via env or `.env`.
2. Fill in **Video Title** (required).
3. Optionally add **Video Description**, **Extra Visual Direction**, and **Dress / Styling Instruction** (e.g. change outfit while keeping your face if you upload a creator photo).
4. Optionally upload **Your Photo (Creator)** and/or **Reference Thumbnail(s)**.
5. Click **Generate Thumbnail** and wait for the image.
6. Use **Download PNG** to save the result.

## 7. Troubleshooting

| Issue | What to try |
|--------|-------------|
| `ImportError: cannot import name 'genai' from 'google'` | Install `google-genai` in the same Python/venv you use to run Streamlit. Remove conflicting packages if needed: `pip uninstall google` then `pip install google-genai`. |
| Wrong Python / packages | Activate the venv first, then `pip install` and `streamlit run` from the same environment. |
| `streamlit` not found | Run `python -m streamlit run youtube_thumbnail_generator.py` using the same interpreter as your venv. |
| API errors / quota | Check API key, billing, and that your project can call the Gemini image model used in `GEMINI_MODEL` inside the script. |

## 8. Changing the model

Open `youtube_thumbnail_generator.py` and edit the line:

```python
GEMINI_MODEL = "gemini-3.1-flash-image-preview"
```

Use a model ID your API key supports (see Google AI Studio / Gemini API docs for current image-capable models).

## 9. File layout (minimal)

You only need this file to run the thumbnail app:

```
your-folder/
  youtube_thumbnail_generator.py
  .env                 # optional
```

No separate config file is required beyond the API key.
