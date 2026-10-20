# AI-Powered Article Summarizer

A small command-line application that summarizes article text with the Google Gemini API. It accepts text from standard input or a UTF-8 `.txt` file.

## Requirements

- Python 3.10 or newer
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Setup

Run these commands from the project directory:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder with your API key. Keep `.env` private; it is excluded by `.gitignore`.

## Run

Summarize a text file:

```powershell
python article_summarizer.py --file article.txt
```

Or provide article text directly in the terminal. Finish input with `Ctrl+Z`, then `Enter` on Windows (or `Ctrl+D` on macOS/Linux):

```powershell
python article_summarizer.py
```

To select a different Gemini model, pass `--model MODEL_NAME`. The default is `gemini-2.5-flash`.

## Tests

The tests use Python's standard library and a mocked Gemini client; they do not make paid API calls or require an API key:

```powershell
python -m unittest discover -s tests -v
```

## Private GitHub repository

Create a new **private** repository on GitHub without initializing it with a README, then run the following from this project directory (replace `YOUR-USERNAME`):

```powershell
git init
git add .
git status --short
git commit -m "Build Gemini article summarizer"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/article-summarizer.git
git push -u origin main
```

Review `git status --short` before committing. The `.env` file is ignored; never add API keys to source files or commits.
