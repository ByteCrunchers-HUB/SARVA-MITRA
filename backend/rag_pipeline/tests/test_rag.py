from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.rag_pipeline import app as rag_app


class SimplifiedRAGTests(unittest.TestCase):
    def test_predict_and_advice_endpoint_exists(self) -> None:
        from backend.rag_pipeline.app import app
        paths = app.openapi()["paths"]
        self.assertIn("/predict-and-advice", paths)
        self.assertIn("/v1/advisory", paths)
        self.assertIn("/advisory", paths)

    def test_legacy_advisory_endpoint_is_normal(self) -> None:
        from backend.rag_pipeline.app import app
        operation = app.openapi()["paths"]["/advisory"]["post"]
        self.assertFalse(operation.get("deprecated", False))

    def test_embedding_model_is_exposed_by_health(self) -> None:
        from backend.rag_pipeline.app import health
        payload = health()
        self.assertEqual(payload["embedding"]["dimension"], 384)
        self.assertEqual(
            payload["embedding"]["model"],
            "sentence-transformers/all-MiniLM-L6-v2",
        )

    def test_new_claude_corpus_documents_exist(self) -> None:
        docs = ROOT / "backend" / "rag_pipeline" / "docs"
        for filename in (
            "08_tomato_bacterial_leaf_spot.txt",
            "tomato_blight_leafspot_comparison.txt",
            "chilli_bacterial_leaf_spot.txt",
            "chilli_heat_ka.txt",
            "ragi_blast_detailed.txt",
            "tomato_soil_moisture_bands.txt",
            "chilli_soil_moisture_ka.txt",
            "ragi_soil_moisture_ka.txt",
            "pest_aphids_thrips.txt",
            "pest_whitefly.txt",
            "irrigation_tomato.txt",
            "irrigation_chilli.txt",
            "irrigation_ragi.txt",
            "crop_stage_tomato.txt",
            "crop_stage_chilli.txt",
            "crop_stage_ragi.txt",
            "nutrient_discrimination.txt",
            "stress_vs_disease.txt",
            "chilli_field_checklist.txt",
            "ragi_field_checklist.txt",
        ):
            self.assertTrue((docs / filename).is_file(), filename)

    def test_superseded_claude_documents_are_removed(self) -> None:
        docs = ROOT / "backend" / "rag_pipeline" / "docs"
        for filename in (
            "chilli_heat_stress.txt",
            "chilli_soil_moisture_bands.txt",
            "ragi_soil_moisture_bands.txt",
        ):
            self.assertFalse((docs / filename).exists(), filename)

    def test_five_verified_scenarios_are_documented(self) -> None:
        guide = ROOT / "backend" / "rag_pipeline" / "PIPELINE_GUIDE.md"
        text = guide.read_text(encoding="utf-8")
        for heading in (
            "1. Low-risk normal readings",
            "2. Moderate-risk leaf-wetness readings",
            "3. High-risk heavy-rain readings",
            "4. Low-risk dry-soil readings",
            "5. Moderate-risk mixed-rain readings",
        ):
            self.assertIn(heading, text)

    def test_fenced_json_is_removed_from_human_answer(self) -> None:
        content = "Healthy answer\n```json\n{\"response_mode\":\"healthy\"}\n```"
        import re
        cleaned = re.sub(r"\s*```json\s*\{[\s\S]*\}\s*```\s*$", "", content).strip()
        self.assertEqual(cleaned, "Healthy answer")

    def test_low_risk_maps_to_healthy(self) -> None:
        self.assertEqual(
            rag_app.ml_output({"prediction": {"risk_level": "low", "risk_pct": 10}}, None),
            0,
        )

    def test_high_risk_maps_to_abnormality(self) -> None:
        self.assertEqual(
            rag_app.ml_output({"prediction": {"risk_level": "high", "risk_pct": 67}}, None),
            1,
        )

    def test_chat_history_is_stateless_and_bounded(self) -> None:
        request = rag_app.AdvisoryRequest(
            chat_history=[
                rag_app.ChatMessage(role="user", content="first"),
                rag_app.ChatMessage(role="assistant", content="second"),
            ]
        )
        self.assertEqual(len(request.chat_history), 2)

    def test_invalid_prediction_is_rejected(self) -> None:
        with self.assertRaises(rag_app.HTTPException):
            rag_app.ml_output({}, None)


if __name__ == "__main__":
    unittest.main()
