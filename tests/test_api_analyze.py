from __future__ import annotations

import json
import os
import unittest
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def _make_jpeg_bytes(color: str = "red") -> bytes:
    buf = BytesIO()
    Image.new("RGB", (16, 16), color=color).save(buf, format="JPEG")
    return buf.getvalue()


class AnalyzeEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        os.environ["SIMASTER_API_KEY"] = "simaster-test-key"
        from app.core.config import get_settings

        get_settings.cache_clear()

    def _auth_headers(self) -> dict[str, str]:
        return {"X-API-KEY": "simaster-test-key"}

    def test_missing_x_api_key_returns_401(self) -> None:
        jpeg = _make_jpeg_bytes()
        files = [("files", ("a.jpg", jpeg, "image/jpeg"))]
        r = self.client.post(
            "/api/v1/analyze",
            data={"student_id": "S1"},
            files=files,
        )
        self.assertEqual(r.status_code, 401)

    def test_invalid_x_api_key_returns_403(self) -> None:
        jpeg = _make_jpeg_bytes()
        files = [("files", ("a.jpg", jpeg, "image/jpeg"))]
        r = self.client.post(
            "/api/v1/analyze",
            headers={"X-API-KEY": "wrong"},
            data={"student_id": "S1"},
            files=files,
        )
        self.assertEqual(r.status_code, 403)

    def test_missing_student_id_returns_422(self) -> None:
        jpeg = _make_jpeg_bytes()
        files = [("files", ("a.jpg", jpeg, "image/jpeg"))]
        r = self.client.post("/api/v1/analyze", headers=self._auth_headers(), files=files)
        self.assertEqual(r.status_code, 422)

    def test_unsupported_media_type_returns_415(self) -> None:
        # Ensure OPENAI_API_KEY is set so we reach media type validation
        os.environ["OPENAI_API_KEY"] = "test-key"
        from app.core.config import get_settings

        get_settings.cache_clear()

        files = [("files", ("a.txt", b"hello", "text/plain"))]
        r = self.client.post(
            "/api/v1/analyze",
            headers=self._auth_headers(),
            data={"student_id": "S1"},
            files=files,
        )
        self.assertEqual(r.status_code, 415)

    def test_too_many_images_returns_400_before_api_key_check(self) -> None:
        # Ensure OPENAI_API_KEY is not set (so we can prove count validation happens first)
        os.environ.pop("OPENAI_API_KEY", None)
        from app.core.config import get_settings

        get_settings.cache_clear()

        jpeg = _make_jpeg_bytes()
        files = [("files", (f"{i}.jpg", jpeg, "image/jpeg")) for i in range(6)]
        r = self.client.post(
            "/api/v1/analyze",
            headers=self._auth_headers(),
            data={"student_id": "S1"},
            files=files,
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("Maksimal", r.json().get("detail", ""))

    def test_success_with_multiple_images_mocked_openai(self) -> None:
        # Force settings to think we have an API key, but we will mock the OpenAI call anyway.
        os.environ["OPENAI_API_KEY"] = "test-key"
        from app.core.config import get_settings

        get_settings.cache_clear()

        mocked_json = {
            "house_index_score": 3.7,
            "confidence_level": 0.82,
            "materials": {
                "atap": {"terlihat": True, "kategori": "LAYAK", "kondisi": "C3"},
                "dinding": None,
                "lantai": {"terlihat": True, "kategori": "LAYAK", "kondisi": "C2"},
            },
            "wealth_proxies": {
                "ac_outdoor_terdeteksi": False,
                "garasi_atau_parkir_tertutup": True,
                "plafon_interior_mewah": False,
                "furnitur_berkualitas": False,
                "estimasi_luas_ruang": "sedang",
            },
            "verification_notes": None,
        }

        async def _fake_analyze_images_b64_jpeg(*, settings, jpeg_bytes_list, system_prompt) -> str:
            # Return as plain JSON string (model should output only JSON).
            return json.dumps(mocked_json)

        with patch(
            "app.services.analysis.analyze_images_b64_jpeg",
            new=_fake_analyze_images_b64_jpeg,
        ):
            jpeg1 = _make_jpeg_bytes("red")
            jpeg2 = _make_jpeg_bytes("blue")
            files = [
                ("files", ("a.jpg", jpeg1, "image/jpeg")),
                ("files", ("b.jpg", jpeg2, "image/jpeg")),
            ]
            r = self.client.post(
                "/api/v1/analyze",
                headers=self._auth_headers(),
                data={"student_id": "STU001"},
                files=files,
            )

        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["student_id"], "STU001")
        self.assertAlmostEqual(body["house_index_score"], 3.7)
        self.assertIn("materials", body)
        self.assertIn("wealth_proxies", body)


if __name__ == "__main__":
    unittest.main()

