"""Summarize an article with the Google Gemini API."""

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai


DEFAULT_MODEL = "gemini-3.8-flash"


def read_article(file_path: Path | None = None) -> str:
    """Read article text from a UTF-8 file or standard input."""
    if file_path is not None:
        return file_path.read_text(encoding="utf-8")
    return sys.stdin.read()


def summarize_article(
    article: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    client: Any | None = None,
) -> str:
    """Return a concise summary of article text using Gemini."""
    if not article.strip():
        raise ValueError("Article text cannot be empty.")
    if not api_key.strip():
        raise ValueError("GEMINI_API_KEY is not set.")

    if client is None:
        client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents=(
            "Summarize the following article in clear, readable language. "
            "Keep the key facts and main conclusion.\n\n"
            f"{article}"
        ),
    )
    summary = response.text
    if not summary or not summary.strip():
        raise RuntimeError("Gemini returned an empty summary.")
    return summary.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize article text with the Google Gemini API."
    )
    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        help="UTF-8 text file containing the article (default: read from stdin)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})",
    )
    args = parser.parse_args(argv)

    load_dotenv()

    try:
        article = read_article(args.file)
    except (OSError, UnicodeError) as error:
        print(f"Could not read article: {error}", file=sys.stderr)
        return 1

    if not article.strip():
        print("Article text is empty. Provide text or a non-empty file.", file=sys.stderr)
        return 1

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key.strip():
        print(
            "GEMINI_API_KEY is missing. Add it to your .env file; see .env.example.",
            file=sys.stderr,
        )
        return 1

    try:
        summary = summarize_article(article, api_key, args.model)
    except Exception:
        print(
            "Gemini request failed. Check GEMINI_API_KEY, your network connection, "
            "and the selected model.",
            file=sys.stderr,
        )
        return 1

    print("Summary:\n")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())