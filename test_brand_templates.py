import os
import tempfile
import unittest

from PIL import Image

from engine.brand_service import BrandService
from engine.case_service import CaseService
from engine.image_manager import ImageManager
from engine.image_renderer import ImageCaseRenderer
from engine.project_manager import ProjectManager


class BrandAndTemplateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.previous_directory = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.addCleanup(os.chdir, self.previous_directory)
        self.project_path = ProjectManager().create_project("BMW_G20")
        self.brand_service = BrandService(os.path.join(self.temp_dir.name, "brand"))

    def create_source_image(self):
        source_path = os.path.join(self.temp_dir.name, "vehicle.png")
        Image.new("RGB", (1600, 900), (32, 96, 180)).save(source_path)
        return source_path

    def test_brand_profile_is_saved_and_loaded(self):
        saved = self.brand_service.save_profile(
            {
                "name": "Deaton Performance",
                "subtitle": "European vehicle specialists",
                "primary_color": "#172554",
                "accent_color": "#F97316",
            }
        )

        self.assertEqual(saved["name"], "Deaton Performance")
        self.assertEqual(self.brand_service.load_profile(), saved)

    def test_primary_image_can_generate_all_templates_with_brand_snapshot(self):
        CaseService(self.project_path).save_case_info(
            {
                "brand": "BMW",
                "model": "G20 330i",
                "fault_category": "DME 编程",
                "repair_result": "编程完成，功能正常",
            }
        )
        imported = ImageManager(self.project_path).import_image(
            self.create_source_image(),
            "01 车辆外观",
        )
        CaseService(self.project_path).set_primary_asset(imported.asset["id"])
        self.brand_service.save_profile(
            {"name": "Deaton Performance", "accent_color": "#F97316"}
        )

        renderer = ImageCaseRenderer(self.project_path, self.brand_service)
        outputs = renderer.render_all()

        self.assertEqual(len(outputs), 3)
        self.assertTrue(all(output.success for output in outputs))
        self.assertTrue(all(os.path.isfile(output.output_path) for output in outputs))
        self.assertEqual({output.template_id for output in outputs}, {
            "case_cover",
            "diagnosis_summary",
            "result_card",
        })

        exports = CaseService(self.project_path).list_exports()
        self.assertEqual(len(exports), 3)
        self.assertTrue(all(export["asset_id"] == imported.asset["id"] for export in exports))
        self.assertTrue(all(export["brand"]["name"] == "Deaton Performance" for export in exports))


if __name__ == "__main__":
    unittest.main()
