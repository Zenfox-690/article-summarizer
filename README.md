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

### Direct input

Run the CLI, then paste or type the article. On Windows, finish input with `Ctrl+Z`, then `Enter` to submit and return to the terminal:

```powershell
python article_summarizer.py
```

### Text file

Summarize the included sample article:

```powershell
python article_summarizer.py --file examples/sample_article.txt
```

For another UTF-8 text file, replace the path after `--file`.

To select a different Gemini model, pass `--model MODEL_NAME`. The default is `gemini-3.8-flash`.

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
