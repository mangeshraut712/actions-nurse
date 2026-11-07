"""Screenshot diagnosis must not block unrelated requests on the ASGI loop."""
from __future__ import annotations

import asyncio
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from nurse import TriageResult, app


class ImageConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def _check_responsive_during_diagnosis(self, route: str) -> None:
        loop = asyncio.get_running_loop()
        started = asyncio.Event()
        release = threading.Event()
        completed = threading.Event()

        def delayed_gemma(log: str, model: str, image: tuple[str, bytes]) -> TriageResult:
            loop.call_soon_threadsafe(started.set)
            try:
                self.assertEqual(log, "error TS2305: missing export")
                self.assertEqual(model, "fixture-model")
                self.assertEqual(image, ("image/png", b"synthetic image"))
                # A bounded wait makes the unfixed route fail instead of hanging
                # the suite. The fixed route releases this after a second request.
                release.wait(timeout=2)
                return TriageResult(
                    summary="Synthetic screenshot diagnosis",
                    failing_step="TypeScript typecheck",
                    root_cause="Missing TypeScript export",
                    suggested_fix="Check the named export",
                    confidence="high",
                    engine="gemma",
                    model=model,
                )
            finally:
                completed.set()

        with tempfile.TemporaryDirectory() as temp_dir, patch("nurse.RULES_ONLY", False), patch(
            "nurse.hmem_status", return_value={"ready": False, "mode": "setup_required"}
        ), patch("nurse.gemma_triage", side_effect=delayed_gemma), patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "synthetic-test-key",
                "NURSE_ACTIVITY_LOG": str(Path(temp_dir) / "trace.jsonl"),
                "ZETARIS_FIXTURE_MODE": "1",
            },
        ):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                request = asyncio.create_task(client.post(
                    route,
                    data={"log": "error TS2305: missing export", "model": "fixture-model"},
                    files={"image": ("synthetic.png", b"synthetic image", "image/png")},
                ))
                try:
                    await asyncio.wait_for(started.wait(), timeout=5)
                    self.assertFalse(completed.is_set(), "Screenshot diagnosis blocked the event loop")
                    response = await asyncio.wait_for(client.get("/api/fixtures"), timeout=5)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn("npm-typecheck.txt", response.json()["fixtures"])
                    self.assertFalse(completed.is_set())
                finally:
                    release.set()
                    result = await asyncio.wait_for(request, timeout=5)

        self.assertEqual(result.status_code, 200)
        payload = result.json()
        diagnosis = payload["gemma"] if route == "/api/compare-image" else payload
        self.assertEqual(diagnosis["summary"], "Synthetic screenshot diagnosis")
        self.assertEqual(diagnosis["model"], "fixture-model")
        self.assertEqual(diagnosis["validation_status"], "confirmed")
        self.assertEqual(payload["zetaris"]["mode"], "fixture")
        self.assertTrue(payload["activity"]["id"].startswith("act-"))

    async def test_triage_image_keeps_other_requests_responsive(self) -> None:
        await self._check_responsive_during_diagnosis("/api/triage-image")

    async def test_compare_image_keeps_other_requests_responsive(self) -> None:
        await self._check_responsive_during_diagnosis("/api/compare-image")

    async def test_invalid_images_are_rejected_before_diagnosis(self) -> None:
        with patch("nurse.MAX_IMAGE_BYTES", 4), patch(
            "nurse.enriched_triage", side_effect=AssertionError("Invalid image reached diagnosis")
        ), patch(
            "nurse.enriched_compare", side_effect=AssertionError("Invalid image reached diagnosis")
        ):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                for route in ("/api/triage-image", "/api/compare-image"):
                    for raw, status, detail in (
                        (b"", 422, "image is empty"),
                        (b"12345", 413, "image must be 5 MB or smaller"),
                    ):
                        with self.subTest(route=route, status=status):
                            response = await client.post(
                                route, files={"image": ("synthetic.png", raw, "image/png")}
                            )
                            self.assertEqual(response.status_code, status)
                            self.assertEqual(response.json()["detail"], detail)

    async def test_image_at_size_limit_keeps_rules_only_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch("nurse.RULES_ONLY", True), patch(
            "nurse.MAX_IMAGE_BYTES", 4
        ), patch(
            "nurse.hmem_status", return_value={"ready": False, "mode": "setup_required"}
        ), patch("nurse.gemma_triage", side_effect=AssertionError("Rules-only called Gemma")), patch.dict(
            os.environ,
            {
                "NURSE_ACTIVITY_LOG": str(Path(temp_dir) / "trace.jsonl"),
                "ZETARIS_FIXTURE_MODE": "1",
            },
        ):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                for route in ("/api/triage-image", "/api/compare-image"):
                    with self.subTest(route=route):
                        response = await client.post(
                            route,
                            data={"log": "error TS2305: missing export"},
                            files={"image": ("synthetic.png", b"1234", "image/png")},
                        )
                        self.assertEqual(response.status_code, 200)
                        payload = response.json()
                        diagnosis = payload["rules"] if route == "/api/compare-image" else payload
                        self.assertEqual(diagnosis["engine"], "rules")
                        self.assertEqual(diagnosis["failing_step"], "Typecheck / tsc")
                        self.assertEqual(payload["zetaris"]["mode"], "fixture")
                        if route == "/api/compare-image":
                            self.assertIsNone(payload["gemma"])
                        else:
                            self.assertIn("Rules-only mode is enabled", diagnosis["summary"])


if __name__ == "__main__":
    unittest.main()
