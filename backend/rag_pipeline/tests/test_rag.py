from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.rag_pipeline import app as rag_app


class SimplifiedRAGTests(unittest.TestCase):
    def test_single_advisory_endpoint_exists(self) -> None:
        from backend.rag_pipeline.app import app
        paths = app.openapi()["paths"]
        self.assertIn("/advisory", paths)
        self.assertNotIn("/predict-and-advice", paths)
        self.assertNotIn("/v1/advisory", paths)
        self.assertNotIn("/ready", paths)
        self.assertIn("/health", paths)
        self.assertIn("/diagnostics", paths)

    def test_embedding_model_is_exposed_by_diagnostics(self) -> None:
        from backend.rag_pipeline.app import diagnostics
        payload = diagnostics()
        self.assertEqual(payload["embedding_dimension"], 384)
        self.assertEqual(
            payload["embedding_model"],
            "sentence-transformers/all-MiniLM-L6-v2",
        )

    def test_health_is_demo_status_only(self) -> None:
        from backend.rag_pipeline.app import health
        payload = health()
        self.assertEqual(payload["status"], "ok")
        self.assertNotIn("embedding", payload)

    def test_explicit_ml_output_bypasses_ml_engine(self) -> None:
        with (
            patch("backend.rag_pipeline.app.call_ml_engine") as call_ml,
            patch("backend.rag_pipeline.rag.RAGPipeline") as rag_pipeline,
        ):
            rag_pipeline.return_value.answer.return_value = ("Advice", {})
            rag_pipeline.return_value.last_retrieval = {
                "query": "",
                "matches": [],
                "documents_sent": [],
            }
            result = rag_app.advisory(
                rag_app.AdvisoryRequest(
                    ml_output=1,
                    crop="tomato",
                    question="What should I inspect?",
                )
            )

        call_ml.assert_not_called()
        self.assertEqual(result["ml_output"], 1)
        self.assertEqual(result["ml_prediction"]["source"], "explicit")

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

    def test_risk_label_alias_maps_to_abnormality(self) -> None:
        self.assertEqual(
            rag_app.ml_output({"prediction": {"risk_label": "high", "risk_pct": 72}}, None),
            1,
        )

    def test_backend_ml_envelope_is_accepted(self) -> None:
        payload = {
            "device_id": "ESP32_01",
            "location": {"name": "Vijayawada", "lat": 16.51, "lon": 80.65},
            "target_date": "2026-11-23",
            "current_sensor_data": {
                "temperature": 29.5,
                "humidity": 68.0,
                "soil_moisture": 86.0,
            },
            "weather_data": {
                "rainfall_mm": 26.0,
                "sunlight_wm2": 132.0,
            },
            "ml_response": {
                "schema_version": "1.0",
                "prediction": {
                    "risk_pct": 72,
                    "risk_label": "high",
                    "risk_bands": {"low_max": 20, "moderate_max": 60},
                    "index_type": "weather_based_proxy",
                    "validated": False,
                },
            },
        }
        request = rag_app.AdvisoryRequest.model_validate(payload)

        self.assertEqual(request.location.name, "Vijayawada")
        self.assertEqual(request.current_sensor_data.soil_moisture, 86.0)
        self.assertEqual(request.weather_data.rainfall_mm, 26.0)
        self.assertEqual(
            rag_app.ml_output(request.ml_response, request.ml_output),
            1,
        )

    def test_backend_ml_envelope_reaches_rag_pipeline(self) -> None:
        payload = {
            "device_id": "ESP32_01",
            "location": {"name": "Vijayawada", "lat": 16.51, "lon": 80.65},
            "target_date": "2026-11-23",
            "current_sensor_data": {
                "temperature": 29.5,
                "humidity": 68.0,
                "soil_moisture": 86.0,
            },
            "weather_data": {
                "rainfall_mm": 26.0,
                "sunlight_wm2": 132.0,
            },
            "ml_response": {
                "prediction": {
                    "risk_pct": 72,
                    "risk_label": "high",
                },
            },
        }
        with patch("backend.rag_pipeline.rag.RAGPipeline") as rag_pipeline:
            rag_pipeline.return_value.answer.return_value = ("Advice", {})
            rag_pipeline.return_value.last_retrieval = {
                "query": "",
                "matches": [],
                "documents_sent": [],
            }
            result = rag_app.advisory(rag_app.AdvisoryRequest.model_validate(payload))

        answer_args = rag_pipeline.return_value.answer.call_args.kwargs
        self.assertEqual(result["ml_output"], 1)
        self.assertEqual(answer_args["location"], "Vijayawada")
        self.assertEqual(answer_args["readings"]["temperature_c"], 29.5)
        self.assertEqual(answer_args["readings"]["humidity_pct"], 68.0)
        self.assertEqual(answer_args["readings"]["soil_moisture_pct"], 86.0)
        self.assertEqual(answer_args["readings"]["rainfall_mm"], 26.0)
        self.assertEqual(answer_args["readings"]["sunlight_wm2"], 132.0)

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
