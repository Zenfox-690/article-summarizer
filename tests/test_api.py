import os
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api.index import MAX_ARTICLE_CHARACTERS, app


class FastAPIApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoints(self):
        """Test health endpoints return 200 OK across multiple path variations."""
        for path in ("/api/health", "/health", "/api", "/api/index.py", "/index.py"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"status": "ok"})

    def test_root_endpoint_serves_html(self):
        """Test root endpoint serves the HTML frontend."""
        for path in ("/", "/index.html"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("text/html", response.headers.get("content-type", ""))
                self.assertIn("AI Article Summarizer", response.text)

    def test_static_assets_served(self):
        """Test style.css and app.js are served correctly."""
        css_res = self.client.get("/style.css")
        self.assertEqual(css_res.status_code, 200)
        self.assertIn("text/css", css_res.headers.get("content-type", ""))

        js_res = self.client.get("/app.js")
        self.assertEqual(js_res.status_code, 200)
        self.assertIn("javascript", js_res.headers.get("content-type", ""))

    def test_vercel_path_normalizer_middleware(self):
        """Test that Vercel x-matched-path headers correctly normalize rewritten paths."""
        # When Vercel rewrites /api/health to /api/index.py with x-matched-path
        response = self.client.get(
            "/api/index.py",
            headers={"x-matched-path": "/api/health"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

        # With query parameter fallback
        query_response = self.client.get("/api/index.py?path=/api/health")
        self.assertEqual(query_response.status_code, 200)
        self.assertEqual(query_response.json(), {"status": "ok"})

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"})
    @patch("api.index.article_summarizer.summarize_article", return_value="A high quality summary.")
    def test_successful_summarization_mocked_gemini(self, mock_summarize):
        """Test successful summarization returns 200 across /api/summarize and /summarize."""
        for path in ("/api/summarize", "/summarize"):
            with self.subTest(path=path):
                response = self.client.post(
                    path,
                    json={"article": "This is a detailed article about urban gardens."},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"summary": "A high quality summary."})

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"})
    @patch("api.index.article_summarizer.summarize_article", return_value="Vercel rewritten summary.")
    def test_vercel_summarize_path_rewritten(self, mock_summarize):
        """Test POST /api/index.py with x-matched-path routes to summarize."""
        response = self.client.post(
            "/api/index.py",
            headers={"x-matched-path": "/api/summarize"},
            json={"article": "Sample article for Vercel rewrite test."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"summary": "Vercel rewritten summary."})

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"})
    @patch("api.index.article_summarizer.summarize_article", return_value="Verified summary structure.")
    def test_correct_api_response_format(self, _mock_summarize):
        """Test response JSON format matches { 'summary': string }."""
        response = self.client.post(
            "/api/summarize",
            json={"article": "Valid article content for formatting test."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get("content-type", "").startswith("application/json"))
        data = response.json()
        self.assertEqual(list(data.keys()), ["summary"])
        self.assertIsInstance(data["summary"], str)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"})
    def test_empty_article_validation(self):
        """Test empty and whitespace-only articles are rejected with 400 Bad Request."""
        empty_cases = [
            {"article": ""},
            {"article": "   "},
            {"article": "\n\t  \n"},
        ]
        for payload in empty_cases:
            with self.subTest(payload=payload):
                response = self.client.post("/api/summarize", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn("cannot be empty", response.json().get("detail", ""))

        # Missing 'article' field entirely
        response_missing = self.client.post("/api/summarize", json={})
        self.assertEqual(response_missing.status_code, 400)
        self.assertIn("article", response_missing.json().get("detail", "").lower())

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"})
    def test_oversized_input_validation(self):
        """Test articles exceeding character limit are rejected with 400 Bad Request."""
        oversized_article = "A" * (MAX_ARTICLE_CHARACTERS + 1)
        response = self.client.post(
            "/api/summarize",
            json={"article": oversized_article},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("exceeds maximum allowed length", response.json().get("detail", ""))

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_server_api_key(self):
        """Test 500 error when GEMINI_API_KEY is not configured on the server."""
        response = self.client.post(
            "/api/summarize",
            json={"article": "Sample text to summarize."},
        )
        self.assertEqual(response.status_code, 500)
        self.assertIn("GEMINI_API_KEY is not configured", response.json().get("detail", ""))

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"})
    def test_gemini_authentication_failure(self):
        """Test authentication error mapping (401/403/invalid key) returns 500 without leaking credentials."""
        auth_error_401 = RuntimeError("Unauthorized")
        auth_error_401.code = 401

        auth_error_403 = RuntimeError("Forbidden")
        auth_error_403.code = 403

        auth_error_key = RuntimeError("API_KEY_INVALID: API key not valid")
        auth_error_key.code = 400

        for error in (auth_error_401, auth_error_403, auth_error_key):
            with self.subTest(error=error):
                with patch("api.index.article_summarizer.summarize_article", side_effect=error):
                    response = self.client.post(
                        "/api/summarize",
                        json={"article": "Sample article."},
                    )
                    self.assertEqual(response.status_code, 500)
                    detail = response.json().get("detail", "")
                    self.assertIn("authentication failed", detail.lower())
                    self.assertNotIn("test-key-12345", detail)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"})
    def test_gemini_timeout(self):
        """Test Gemini timeout maps to 504 Gateway Timeout."""
        with patch(
            "api.index.article_summarizer.summarize_article",
            side_effect=TimeoutError("Request timed out after 60s"),
        ):
            response = self.client.post(
                "/api/summarize",
                json={"article": "Sample article."},
            )
            self.assertEqual(response.status_code, 504)
            self.assertIn("timed out", response.json().get("detail", "").lower())

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"})
    def test_gemini_503_504_failure(self):
        """Test Gemini upstream service unavailable / gateway failures."""
        err_503 = RuntimeError("Service Unavailable")
        err_503.code = 503
        with patch("api.index.article_summarizer.summarize_article", side_effect=err_503):
            response = self.client.post("/api/summarize", json={"article": "Sample article."})
            self.assertEqual(response.status_code, 503)
            self.assertIn("temporarily unavailable", response.json().get("detail", "").lower())

        err_504 = RuntimeError("Gateway Timeout")
        err_504.code = 504
        with patch("api.index.article_summarizer.summarize_article", side_effect=err_504):
            response = self.client.post("/api/summarize", json={"article": "Sample article."})
            self.assertEqual(response.status_code, 504)
            self.assertIn("timed out", response.json().get("detail", "").lower())

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"})
    def test_retry_exhaustion(self):
        """Test retry exhaustion error returns 503 Service Unavailable."""
        exhaustion_error = RuntimeError("Gemini request retries exhausted after multiple attempts")
        with patch(
            "api.index.article_summarizer.summarize_article",
            side_effect=exhaustion_error,
        ):
            response = self.client.post(
                "/api/summarize",
                json={"article": "Sample article."},
            )
            self.assertEqual(response.status_code, 503)
            self.assertIn("retries exhausted", response.json().get("detail", "").lower())

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"})
    def test_gemini_rate_limit_429(self):
        """Test rate limit / quota exhaustion returns 429 Too Many Requests."""
        err_429 = RuntimeError("Resource exhausted: quota exceeded")
        err_429.code = 429
        with patch("api.index.article_summarizer.summarize_article", side_effect=err_429):
            response = self.client.post("/api/summarize", json={"article": "Sample article."})
            self.assertEqual(response.status_code, 429)
            self.assertIn("rate limit or quota exceeded", response.json().get("detail", "").lower())

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"})
    @patch("api.index.article_summarizer.genai.Client")
    def test_end_to_end_summarization_with_mocked_gemini_client(self, client_factory):
        """Test end-to-end summarization through article_summarizer using a mocked genai.Client."""
        mock_response = Mock()
        mock_response.text = "This is a full end-to-end summarized article."
        client_factory.return_value.models.generate_content.return_value = mock_response

        response = self.client.post(
            "/api/summarize",
            json={"article": "A lengthy paragraph that needs end-to-end summarizing."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"summary": "This is a full end-to-end summarized article."},
        )


if __name__ == "__main__":
    unittest.main()
