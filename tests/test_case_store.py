import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.case_store import CaseStore


class CaseStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.store = CaseStore(self.root / "cases")
        self.image_a = self.root / "first.jpg"
        self.image_b = self.root / "second.png"
        Image.new("RGB", (32, 20), "red").save(self.image_a)
        Image.new("RGB", (32, 20), "blue").save(self.image_b)

    def test_case_has_six_slots_and_default_logo(self):
        case_dir = self.store.create("BMW G20")
        manifest = self.store.load(case_dir)

        self.assertEqual(set(manifest["assets"]), {"vehicle", "fault", "diagnosis", "programming", "result", "logo"})
        self.assertTrue(self.store.asset_path(case_dir, "logo").is_file())
        self.assertTrue((case_dir / "output").is_dir())

    def test_dropping_new_image_replaces_only_that_fixed_slot(self):
        case_dir = self.store.create("Example")
        self.store.set_asset(case_dir, "vehicle", self.image_a)
        self.store.set_asset(case_dir, "vehicle", self.image_b)

        asset = self.store.asset_path(case_dir, "vehicle")
        self.assertEqual(asset.suffix, ".png")
        self.assertEqual(len(list((case_dir / "assets").glob("vehicle.*"))), 1)

    def test_parameter_file_keeps_local_paths_and_confirmed_plan(self):
        case_dir = self.store.create("Example")
        self.store.set_information(case_dir, {"brand": "BMW", "service": "Remote Programming"})
        self.store.set_ai_plan(case_dir, "TITLE\nBMW REMOTE CASE", True)

        parameter_file = self.store.write_generation_parameters(case_dir)
        payload = json.loads(parameter_file.read_text(encoding="utf-8"))

        self.assertEqual(payload["information"]["brand"], "BMW")
        self.assertTrue(payload["ai_plan"]["confirmed"])
        self.assertTrue(Path(payload["assets"]["logo"]).is_file())
