import os
import tempfile
import unittest

from PIL import Image

from engine.case_service import CaseService
from engine.image_manager import ImageManager
from engine.image_renderer import ImageCaseRenderer
from engine.project_manager import ProjectManager


class ImageCaseMvpTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.previous_directory = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.addCleanup(os.chdir, self.previous_directory)
        self.project_path = ProjectManager().create_project("BMW_G20")

    def create_source_image(self, name="vehicle.png", color=(32, 96, 180)):
        source_path = os.path.join(self.temp_dir.name, name)
        Image.new("RGB", (1600, 900), color).save(source_path)
        return source_path

    def test_case_information_is_saved_in_project_metadata(self):
        service = CaseService(self.project_path)

        saved = service.save_case_info(
            {
                "brand": "BMW",
                "model": "G20 330i",
                "year": "2021",
                "region": "Europe",
                "fault_category": "ECU programming",
                "service_type": "Remote programming",
                "programming_type": "DME update",
                "equipment_used": "ICOM",
                "repair_result": "Completed",
            }
        )

        self.assertEqual(saved["brand"], "BMW")
        self.assertEqual(service.load_case_info()["model"], "G20 330i")
        self.assertEqual(service.load_project()["vehicle"], "BMW G20 330i")

    def test_imported_image_is_categorized_and_persisted(self):
        source_path = self.create_source_image()

        result = ImageManager(self.project_path).import_image(
            source_path,
            "01 车辆外观",
        )

        self.assertTrue(result.success, result.error)
        self.assertTrue(os.path.isfile(result.target_path))
        self.assertNotEqual(result.target_path, source_path)

        assets = CaseService(self.project_path).list_assets("01 车辆外观")
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]["id"], result.asset["id"])
        self.assertEqual(assets[0]["original_filename"], "vehicle.png")

    def test_case_cover_export_records_output_history(self):
        case_service = CaseService(self.project_path)
        case_service.save_case_info(
            {"brand": "BMW", "model": "G20", "fault_category": "ECU programming"}
        )
        imported = ImageManager(self.project_path).import_image(
            self.create_source_image(),
            "01 车辆外观",
        )

        result = ImageCaseRenderer(self.project_path).render(
            "case_cover",
            imported.asset["id"],
        )

        self.assertTrue(result.success, result.error)
        self.assertTrue(os.path.isfile(result.output_path))
        with Image.open(result.output_path) as image:
            self.assertEqual(image.size, (1080, 1350))

        exports = case_service.list_exports()
        self.assertEqual(len(exports), 1)
        self.assertEqual(exports[0]["template_id"], "case_cover")
        self.assertEqual(exports[0]["asset_id"], imported.asset["id"])

    def test_rendering_requires_an_existing_imported_asset(self):
        result = ImageCaseRenderer(self.project_path).render("case_cover", "missing")

        self.assertFalse(result.success)
        self.assertIn("素材", result.error)

    def test_creating_a_same_named_case_preserves_existing_case(self):
        CaseService(self.project_path).save_case_info({"brand": "BMW"})

        another_project_path = ProjectManager().create_project("BMW_G20")

        self.assertNotEqual(another_project_path, self.project_path)
        self.assertEqual(CaseService(self.project_path).load_case_info()["brand"], "BMW")
        self.assertTrue(os.path.isfile(os.path.join(another_project_path, "project.json")))



if __name__ == "__main__":
    unittest.main()
