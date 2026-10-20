import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import article_summarizer


class ReadArticleTests(unittest.TestCase):
    def test_reads_file_as_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            article_file = Path(directory) / "article.txt"
            article_file.write_text("Caf\u00e9 article", encoding="utf-8")

            self.assertEqual(article_summarizer.read_article(article_file), "Caf\u00e9 article")

    def test_reads_standard_input(self):
        with patch.object(article_summarizer.sys, "stdin", io.StringIO("Article text")):
            self.assertEqual(article_summarizer.read_article(), "Article text")


class SummarizeArticleTests(unittest.TestCase):
    def test_sends_article_to_gemini_and_returns_trimmed_summary(self):
        client = Mock()
        client.models.generate_content.return_value.text = "  A concise summary.  "

        summary = article_summarizer.summarize_article(
            "The article text", "test-key", client=client
        )

        self.assertEqual(summary, "A concise summary.")
        client.models.generate_content.assert_called_once()
        self.assertEqual(
            client.models.generate_content.call_args.kwargs["model"],
            article_summarizer.DEFAULT_MODEL,
        )
        self.assertIn(
            "The article text",
            client.models.generate_content.call_args.kwargs["contents"],
        )

    def test_rejects_empty_article_without_calling_gemini(self):
        client = Mock()

        with self.assertRaisesRegex(ValueError, "Article text cannot be empty"):
            article_summarizer.summarize_article("  \n", "test-key", client=client)

        client.models.generate_content.assert_not_called()

    def test_rejects_missing_api_key(self):
        with self.assertRaisesRegex(ValueError, "GEMINI_API_KEY is not set"):
            article_summarizer.summarize_article("Article text", " ", client=Mock())

    def test_rejects_empty_gemini_response(self):
        client = Mock()
        client.models.generate_content.return_value.text = "  "

        with self.assertRaisesRegex(RuntimeError, "empty summary"):
            article_summarizer.summarize_article("Article text", "test-key", client=client)


class MainTests(unittest.TestCase):
    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    @patch.object(article_summarizer, "load_dotenv")
    @patch.object(article_summarizer, "summarize_article", return_value="A readable summary.")
    def test_summarizes_direct_input(self, summarize, _load_dotenv):
        with patch.object(article_summarizer.sys, "stdin", io.StringIO("Article text")):
            with patch("sys.stdout", new_callable=io.StringIO) as output:
                result = article_summarizer.main([])

        self.assertEqual(result, 0)
        summarize.assert_called_once_with("Article text", "test-key", article_summarizer.DEFAULT_MODEL)
        self.assertIn("Summary:\n\nA readable summary.", output.getvalue())

    @patch.dict("os.environ", {}, clear=True)
    @patch.object(article_summarizer, "load_dotenv")
    def test_reports_missing_api_key(self, _load_dotenv):
        with patch.object(article_summarizer.sys, "stdin", io.StringIO("Article text")):
            with patch("sys.stderr", new_callable=io.StringIO) as error_output:
                result = article_summarizer.main([])

        self.assertEqual(result, 1)
        self.assertIn("GEMINI_API_KEY is missing", error_output.getvalue())

    @patch.object(article_summarizer, "load_dotenv")
    def test_reports_missing_file(self, _load_dotenv):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("sys.stderr", new_callable=io.StringIO) as error_output:
                result = article_summarizer.main(["--file", "missing-article.txt"])

        self.assertEqual(result, 1)
        self.assertIn("Could not read article", error_output.getvalue())

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    @patch.object(article_summarizer, "load_dotenv")
    def test_reports_empty_input(self, _load_dotenv):
        with patch.object(article_summarizer.sys, "stdin", io.StringIO("  \n")):
            with patch("sys.stderr", new_callable=io.StringIO) as error_output:
                result = article_summarizer.main([])

        self.assertEqual(result, 1)
        self.assertIn("Article text is empty", error_output.getvalue())

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    @patch.object(article_summarizer, "load_dotenv")
    @patch.object(article_summarizer, "summarize_article", side_effect=RuntimeError("API error"))
    def test_reports_gemini_api_failure(self, _summarize, _load_dotenv):
        with patch.object(article_summarizer.sys, "stdin", io.StringIO("Article text")):
            with patch("sys.stderr", new_callable=io.StringIO) as error_output:
                result = article_summarizer.main([])

        self.assertEqual(result, 1)
        self.assertIn("Gemini request failed", error_output.getvalue())


if __name__ == "__main__":
    unittest.main()