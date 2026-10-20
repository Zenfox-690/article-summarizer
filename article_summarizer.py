"""Summarize an article with the Google Gemini API."""

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types


DEFAULT_MODEL = "gemini-3.8-flash"
REQUEST_TIMEOUT_MS = 60_000


def read_article(file_path: Path | None = None) -> str:
    """Read article text from a UTF-8 file or interactive terminal input."""
    if file_path is not None:
        return file_path.read_text(encoding="utf-8")

    print("Enter or paste the article. Type END on its own line to submit; Ctrl+C cancels.")
    lines = []
    while True:
        line = sys.stdin.readline()
        if not line or line.strip().upper() == "END":
            break
        lines.append(line)
    return "".join(lines)


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
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=REQUEST_TIMEOUT_MS,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )

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


def describe_gemini_error(error: Exception) -> str:
    """Return a safe, actionable message without exposing provider responses."""
    status = getattr(error, "code", None)
    if not isinstance(status, int):
        status = getattr(error, "status_code", None)

    if status == 400:
        detail = str(error).lower()
        if any(
            marker in detail
            for marker in ("api_key_invalid", "api key not valid", "invalid api key")
        ):
            reason = "invalid API key"
        else:
            reason = "invalid request"
    elif status == 401:
        reason = "invalid API key"
    elif status == 403:
        reason = "API key lacks permission for this request"
    elif status == 404:
        reason = "model or endpoint is unavailable"
    elif status == 429:
        reason = "quota or rate limit exceeded"
    elif status in (500, 502, 503, 504):
        reason = "Gemini is temporarily unavailable; retry later"
    elif any(
        marker in type(error).__name__.lower()
        for marker in ("timeout", "network", "connect", "transport")
    ):
        reason = "network connection to Gemini failed; check connectivity and retry"
    else:
        reason = "request failed; check the API key, model, and network connection"

    code = f" (HTTP {status})" if isinstance(status, int) else ""
    return f"Gemini request failed{code}: {reason}."


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
    except KeyboardInterrupt:
        print("Input cancelled. No request was sent.", file=sys.stderr)
        return 130
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
    except KeyboardInterrupt:
        print("Gemini request interrupted. No summary was returned.", file=sys.stderr)
        return 130
    except Exception as error:
        print(describe_gemini_error(error), file=sys.stderr)
        return 1

    print("Summary:\n")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())