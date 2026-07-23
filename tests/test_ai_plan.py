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

        self.assertIn("2 explicitly selected reference images", prompt)
        self.assertIn("Do not infer", prompt)
