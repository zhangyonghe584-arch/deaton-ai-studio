import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.case_store import CaseStore
from core.generation import LocalGenerationService


class LocalGenerationTests(unittest.TestCase):
    def test_local_script_generates_five_portrait_preview_images(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CaseStore(Path(directory) / "cases")
            case_dir = store.create("Local output")
            store.set_information(case_dir, {"brand": "BMW", "model": "G20", "service": "Remote Programming"})
            store.set_ai_plan(case_dir, "TITLE\nLOCAL CASE", True)

            files = LocalGenerationService(store).generate(case_dir)

            self.assertEqual(len(files), 15)
            self.assertTrue(all(path.is_file() for path in files))
            with Image.open(files[0]) as first_image:
                self.assertEqual(first_image.size, (1080, 1920))\n            self.assertEqual(files[5].parent.name, "template_2")\n            self.assertEqual(files[10].parent.name, "template_3")
            self.assertEqual([path.name for path in files], [
                "01_case_overview.png", "02_vehicle_fault.png", "03_diagnosis.png",
                "04_programming.png", "05_result.png",
            ])

    def test_command_line_renderer_generates_from_parameter_file(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CaseStore(Path(directory) / "cases")
            case_dir = store.create("CLI output")
            parameter_file = store.write_generation_parameters(case_dir)
            script = Path(__file__).resolve().parents[1] / "scripts" / "generate_case.py"

            completed = subprocess.run(
                [sys.executable, str(script), str(parameter_file)],
                check=True,
                capture_output=True,
                text=True,
            )
            output = json.loads(completed.stdout)

            self.assertEqual(len(output["files"]), 5)
            self.assertTrue(all(Path(path).is_file() for path in output["files"]))
