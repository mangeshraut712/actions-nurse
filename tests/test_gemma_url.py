import sys
import types
import unittest
from unittest.mock import patch

import nurse


class _Response:
    status_code = 404

    def json(self):
        return {}


class GemmaUrlTests(unittest.TestCase):
    def test_model_name_is_encoded_as_one_path_segment(self):
        urls = []

        def post(url, **kwargs):
            urls.append(url)
            return _Response()

        fake_httpx = types.SimpleNamespace(post=post, TimeoutException=TimeoutError)
        with patch.dict(sys.modules, {"httpx": fake_httpx}), patch.dict(
            "os.environ", {"GEMINI_API_KEY": "test-key"}
        ):
            self.assertIsNone(nurse.gemma_triage("error: boom", "../../v1/files?x"))

        self.assertEqual(
            urls,
            [
                "https://generativelanguage.googleapis.com/v1beta/models/"
                "..%2F..%2Fv1%2Ffiles%3Fx:generateContent"
            ],
        )


class GemmaDiagnosisTests(unittest.TestCase):
    def test_json_without_diagnosis_fields_falls_back(self):
        import json

        class _Ok:
            status_code = 200

            def json(self):
                text = json.dumps({"error": "quota exceeded"})
                return {"candidates": [{"content": {"parts": [{"text": text}]}}]}

        fake_httpx = types.SimpleNamespace(post=lambda url, **kwargs: _Ok(), TimeoutException=TimeoutError)
        with patch.dict(sys.modules, {"httpx": fake_httpx}), patch.dict(
            "os.environ", {"GEMINI_API_KEY": "test-key"}
        ):
            self.assertIsNone(nurse.gemma_triage("error: boom", "gemma-test"))


if __name__ == "__main__":
    unittest.main()
