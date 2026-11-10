# AI-Powered Article Summarizer

An AI-powered article summarization application built with Google Gemini. Includes a responsive modern web application, a FastAPI REST API for Vercel Serverless Functions, and the original command-line interface.

## Features

- **Modern Web Interface:** Clean, responsive interface with real-time word and character counts, sample loader, and one-click copy.
- **FastAPI Backend:** Lightweight serverless Python backend with input validation, bounded timeouts, and graceful error handling.
- **Production Ready for Vercel:** Preconfigured for zero-friction Vercel deployment with static asset CDN routing and serverless Python functions.
- **CLI Utility:** Retains command-line functionality for terminal input or text file processing.
- **Robust Error Handling:** Distinguishes rate limits (429), timeouts (504), service unavailability (503), authentication failures, and bad requests without leaking server secrets or tracebacks.

## Requirements

- Python 3.10 or newer (Python 3.12 recommended for Vercel)
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Setup

Run these commands in PowerShell from the project directory. The first command creates or reuses `.venv`:

```powershell
if (-not (Test-Path .venv)) { py -m venv .venv }
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

In Notepad, replace `your_gemini_api_key_here` with your active Gemini API key. Save and close the file. Never commit `.env`; it is excluded by `.gitignore`.

## Running the Web Application Locally

Start the local development server with `uvicorn`:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn api.index:app --reload --port 8000
```

Open your browser to:
- **Web App:** [http://localhost:8000](http://localhost:8000)
- **API Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

## API Reference

### `POST /api/summarize`

Summarizes article text using the server-side Gemini integration.

**Request:**

```json
{
  "article": "Your long article text goes here..."
}
```

**Response (HTTP 200):**

```json
{
  "summary": "Concise factual summary of the article."
}
```

**Validation & Error Codes:**
- `400 Bad Request`: Empty input, whitespace-only, missing article field, or input exceeding 100,000 characters.
- `429 Too Many Requests`: Upstream Gemini rate limit or quota exceeded.
- `500 Internal Server Error`: Server configuration issue or Gemini authentication failure.
- `503 Service Unavailable`: Upstream Gemini service temporarily unavailable or retries exhausted.
- `504 Gateway Timeout`: Gemini request exceeded the 60-second bounded timeout.

## Running the Command-Line Interface (CLI)

### Interactive input

```powershell
python article_summarizer.py
```

Type or paste the article. Enter `END` on a line by itself to submit:

```text
The first article paragraph.
The second article paragraph.
END
```

Press `Ctrl+C` to cancel without sending a request.

### File input

Summarize a UTF-8 text file directly:

```powershell
python article_summarizer.py --file examples/sample_article.txt
```

To specify an alternate model:

```powershell
python article_summarizer.py --file examples/sample_article.txt --model gemini-3.8-flash
```

## Running Automated Tests

The automated test suite runs offline using Python's standard library and FastAPI's `TestClient` with mocked Gemini responses. No API key or paid network calls are required:

```powershell
python -m unittest discover -s tests -v
```

This discovers and runs all tests across `tests/test_article_summarizer.py` and `tests/test_api.py`.

## Deploying to Vercel

The project is structured for native deployment to Vercel with serverless Python functions and CDN-hosted static files:

### Architecture

- `public/`: Static frontend assets (`index.html`, `style.css`, `app.js`) served by Vercel's global edge network.
- `api/index.py`: FastAPI serverless function executing Python 3.12 via `@vercel/python`.
- `vercel.json`: Rewrites `/api/(.*)` to `api/index.py`, routing all API calls to FastAPI while preserving static root file serving.
- `requirements.txt`: Installed automatically by Vercel during build.

### Vercel Dashboard Steps

1. Log in to [vercel.com](https://vercel.com).
2. Click **Add New...** > **Project**.
3. Import the GitHub repository: `Zenfox-690/article-summarizer`.
4. Keep the default settings (**Framework Preset:** Other / None).
5. In **Environment Variables**:
   - **Key:** `GEMINI_API_KEY`
   - **Value:** `<your-google-gemini-api-key>`
6. Click **Deploy**.

Vercel will build the serverless functions and host the static frontend on your production URL.
