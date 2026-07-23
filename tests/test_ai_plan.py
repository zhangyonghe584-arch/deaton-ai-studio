import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.ai_plan import OpenAIPlanService


class OpenAIPlanServiceTests(unittest.TestCase):
    def test_selected_image_is_compressed_to_a_jpeg_data_url(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "source.png"
            Image.new("RGB", (2400, 1600), "green").save(image_path)

            data_url = OpenAIPlanService()._compressed_data_url(image_path)

            self.assertTrue(data_url.startswith("data:image/jpeg;base64,"))

    def test_prompt_limits_scope_to_explicit_case_facts(self):
        prompt = OpenAIPlanService._prompt({"brand": "BMW", "fault_category": "ECU"}, 2)

        self.assertIn("2 explicitly selected case images", prompt)
        self.assertIn("Do not infer", prompt)

    def test_prompt_allows_one_to_five_source_images(self):
        prompt = OpenAIPlanService._prompt({}, 1)
        self.assertIn("One to five case images are valid", prompt)
        self.assertIn("not a final answer", prompt)

    def test_prompt_preserves_logo_and_five_output_rules(self):
        prompt = OpenAIPlanService._prompt({}, 5, True, "keep source photos centered")
        self.assertIn("official logo reference", prompt)
        self.assertIn("exactly five output images", prompt)
        self.assertIn("step labels", prompt)
