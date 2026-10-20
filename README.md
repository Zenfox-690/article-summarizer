# AI-Powered Article Summarizer

A small command-line application that summarizes article text with the Google Gemini API. It accepts text from standard input or a UTF-8 `.txt` file.

## Requirements

- Python 3.10 or newer
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Setup

Run these commands from the project directory. The first command reuses the existing `.venv` when present; dependency installation is safe to repeat if needed:

```powershell
if (-not (Test-Path .venv)) { py -m venv .venv }
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

In Notepad, replace the placeholder value for `GEMINI_API_KEY`. Save and close the file. Never share or commit `.env`; it is excluded by `.gitignore`.

## Run

### Interactive input

Run the CLI, then type or paste the article. Enter `END` on a line by itself to submit the complete multiline article:

```powershell
python article_summarizer.py
```

Example:

```text
The first article paragraph.
The second article paragraph.
END
```

Press `Ctrl+C` to cancel while entering text or while Gemini is responding. On Windows, `Ctrl+Z` then `Enter` also signals end-of-file and submits any text entered so far. If end-of-file arrives with no text, the application exits with an empty-input message.

### Text file

Summarize the included sample article:

```powershell
python article_summarizer.py --file examples/sample_article.txt
```

For another UTF-8 text file, replace the path after `--file`.

To select a different Gemini model, pass `--model MODEL_NAME`. The default is `gemini-3.8-flash`. Each API request has a 60-second timeout and a single attempt, so a slow or unavailable service cannot retry indefinitely.

## Troubleshooting

- `GEMINI_API_KEY is missing`: confirm `.env` is in the project root and contains `GEMINI_API_KEY=...`.
- `invalid API key`: check that the key is active and copied correctly; never paste it into a command or commit it.
- `lacks permission`: verify that the key/project is allowed to use the Gemini API.
- `quota or rate limit exceeded`: check the project's API quota and retry when available.
- `model or endpoint is unavailable`: choose a supported model with `--model MODEL_NAME`.
- `temporarily unavailable`, network errors, or a request timeout: check connectivity and retry later.

Ctrl+C during input or a Gemini request exits cleanly without a traceback.

## Tests

The tests use Python's standard library and a mocked Gemini client; they do not make paid API calls or require an API key:

```powershell
python -m unittest discover -s tests -v
```

## GitHub submission

The project is published at [Zenfox-690/article-summarizer](https://github.com/Zenfox-690/article-summarizer). To publish reviewed documentation or sample changes to the existing `main` branch:

```powershell
git status --short
git add README.md examples/sample_article.txt
git diff --cached
git commit -m "Add manual testing sample and instructions"
git push origin main
```

Review the staged diff before committing. `.env`, `.venv`, and generated caches are ignored; do not force-push or commit credentials.
