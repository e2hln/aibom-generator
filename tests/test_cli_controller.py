import json
import shutil
import unittest
import uuid
from pathlib import Path

from src.controllers.cli_controller import CLIController


def _sample_aibom() -> dict:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": "urn:uuid:12345678-1234-5678-1234-567812345678",
        "version": 1,
        "metadata": {
            "timestamp": "2026-06-10T00:00:00Z",
            "tools": {
                "components": [
                    {"name": "OWASP AIBOM Generator"}
                ]
            },
        },
        "components": [
            {
                "type": "machine-learning-model",
                "name": "local-cli-model",
                "version": "1.0.0",
                "description": "CLI HTML report unicode regression path \u2705",
                "purl": "pkg:huggingface/owner/local-cli-model",
                "licenses": [{"license": {"id": "Apache-2.0"}}],
            }
        ],
        "externalReferences": [
            {"type": "website", "url": "https://huggingface.co/owner/local-cli-model"}
        ],
    }


def _sample_score() -> dict:
    category_details = {
        "required_fields": {"present_fields": 4, "total_fields": 4, "percentage": 100, "max_points": 20},
        "metadata": {"present_fields": 2, "total_fields": 2, "percentage": 100, "max_points": 20},
        "component_basic": {"present_fields": 4, "total_fields": 4, "percentage": 100, "max_points": 20},
        "component_model_card": {"present_fields": 0, "total_fields": 0, "percentage": 0, "max_points": 30},
        "external_references": {"present_fields": 1, "total_fields": 1, "percentage": 100, "max_points": 10},
    }
    section_scores = {
        "required_fields": 20,
        "metadata": 20,
        "component_basic": 20,
        "component_model_card": 0,
        "external_references": 10,
    }
    return {
        "total_score": 70,
        "subtotal_score": 70,
        "completeness_profile": {"name": "Basic", "description": "Regression test profile"},
        "field_checklist": {
            "bomFormat": "\u2714 present",
            "specVersion": "\u2714 present",
            "serialNumber": "\u2714 present",
            "version": "\u2714 present",
        },
        "field_types": {},
        "reference_urls": {},
        "category_details": category_details,
        "category_fields_list": {
            "component_model_card": [],
            "external_references": [],
        },
        "section_scores": section_scores,
        "max_scores": {
            "required_fields": 20,
            "metadata": 20,
            "component_basic": 20,
            "component_model_card": 30,
            "external_references": 10,
        },
        "missing_counts": {"critical": 0, "important": 0, "supplementary": 0},
        "recommendations": [],
        "penalty_applied": False,
        "penalty_percentage": 0,
        "penalty_reason": "",
        "penalty_factor": 1,
        "validation": {"valid": True, "issues": []},
    }


class _FakeService:
    def __init__(self):
        self._aibom = _sample_aibom()
        self._score = _sample_score()

    def generate_aibom(self, model_id, include_inference=False, enable_summarization=False, metadata_overrides=None):
        return self._aibom

    def get_enhancement_report(self):
        return {"final_score": self._score}

    @staticmethod
    def _normalise_model_id(model_id):
        return model_id


class CLIControllerTests(unittest.TestCase):
    def test_generate_creates_parent_directory_for_nested_custom_output(self):
        repo_root = Path(__file__).resolve().parents[1]
        output_dir = repo_root / "sboms" / f"test-cli-controller-nested-{uuid.uuid4().hex}" / "reports"
        try:
            self.assertFalse(output_dir.exists())

            output_file = output_dir / "nested-cli-output.json"
            controller = CLIController()
            controller.service = _FakeService()

            controller.generate(
                "owner/local-cli-model",
                output_file=str(output_file),
            )

            json_1_6 = output_file
            json_1_7 = output_dir / "nested-cli-output_1_7.json"
            html_report = output_dir / "nested-cli-output.html"

            self.assertTrue(output_dir.exists())
            self.assertGreater(json_1_6.stat().st_size, 0)
            self.assertGreater(json_1_7.stat().st_size, 0)
            self.assertTrue(html_report.exists())
            self.assertGreater(html_report.stat().st_size, 0)

            json.loads(json_1_6.read_text(encoding="utf-8"))
            json.loads(json_1_7.read_text(encoding="utf-8"))

            html = html_report.read_text(encoding="utf-8")
            self.assertIn("AIBOM Summary", html)
        finally:
            shutil.rmtree(output_dir.parent, ignore_errors=True)

    def test_generate_writes_non_empty_utf8_html_report(self):
        repo_root = Path(__file__).resolve().parents[1]
        output_dir = repo_root / "sboms" / f"test-cli-controller-{uuid.uuid4().hex}"
        output_dir.mkdir(parents=True)
        try:
            output_file = output_dir / "cli-html-regression.json"
            controller = CLIController()
            controller.service = _FakeService()

            controller.generate(
                "owner/local-cli-model",
                output_file=str(output_file),
            )

            json_1_6 = output_file
            json_1_7 = output_dir / "cli-html-regression_1_7.json"
            html_report = output_dir / "cli-html-regression.html"

            self.assertGreater(json_1_6.stat().st_size, 0)
            self.assertGreater(json_1_7.stat().st_size, 0)
            self.assertTrue(html_report.exists())
            self.assertGreater(html_report.stat().st_size, 0)

            html = html_report.read_text(encoding="utf-8")
            self.assertIn("AIBOM Summary", html)
            self.assertIn("CycloneDX 1.6", html)
            self.assertIn("CLI HTML report unicode regression path \u2705", html)

            json.loads(json_1_6.read_text(encoding="utf-8"))
            json.loads(json_1_7.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
