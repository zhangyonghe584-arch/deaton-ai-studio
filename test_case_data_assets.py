import os
import tempfile
import unittest

from PIL import Image

from engine.case_service import CaseService
from engine.image_manager import ImageManager
from engine.project_manager import ProjectManager


class CaseDataAndAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.previous_directory = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.addCleanup(os.chdir, self.previous_directory)
        self.project_path = ProjectManager().create_project("BMW_G20")
        self.service = CaseService(self.project_path)
        self.manager = ImageManager(self.project_path)

    def create_image(self, name, color):
        path = os.path.join(self.temp_dir.name, name)
        Image.new("RGB", (320, 200), color).save(path)
        return path

    def test_complete_case_information_persists_to_project_json(self):
        values = {
            "customer_name": "Deaton Auto Customer",
            "customer_region": "Shenzhen",
            "brand": "BMW",
            "model": "G20 330i",
            "year": "2021",
            "vin": "WBA00000000000001",
            "license_plate": "粤B12345",
            "mileage": "48,200 km",
            "engine_model": "B48",
            "fault_category": "ECU programming",
            "fault_description": "Module update interrupted",
            "service_type": "Remote programming",
            "programming_type": "DME update",
            "equipment_used": "ICOM Next",
            "repair_result": "Completed and verified",
            "technical_notes": "Battery support connected throughout the update.",
        }

        saved = self.service.save_case_info(values)

        self.assertEqual(saved, values)
        self.assertEqual(self.service.load_case_info(), values)
        project = self.service.load_project()
        self.assertEqual(project["vehicle"], "BMW G20 330i")
        self.assertEqual(project["fault"], "ECU programming")
        self.assertEqual(project["service"], "Remote programming")

    def test_asset_lifecycle_persists_status_order_main_image_replacement_and_removal(self):
        first = self.manager.import_image(
            self.create_image("first.png", (10, 20, 30)),
            "01 车辆外观",
        )
        second = self.manager.import_image(
            self.create_image("second.png", (40, 50, 60)),
            "01 车辆外观",
        )
        self.assertTrue(first.success, first.error)
        self.assertTrue(second.success, second.error)

        self.service.set_asset_status(first.asset["id"], "已审核")
        self.service.set_primary_asset(second.asset["id"])
        self.service.reorder_assets(
            "01 车辆外观",
            [second.asset["id"], first.asset["id"]],
        )

        assets = self.service.list_assets("01 车辆外观")
        self.assertEqual([asset["id"] for asset in assets], [second.asset["id"], first.asset["id"]])
        self.assertTrue(assets[0]["is_primary"])
        self.assertEqual(assets[1]["status"], "已审核")

        replacement_path = self.create_image("replacement.png", (200, 100, 50))
        replaced = self.manager.replace_image(first.asset["id"], replacement_path)
        self.assertTrue(replaced.success, replaced.error)
        replaced_asset = self.service.get_asset(first.asset["id"])
        self.assertEqual(replaced_asset["original_filename"], "replacement.png")
        self.assertEqual(replaced_asset["status"], "已替换")
        with Image.open(os.path.join(self.project_path, replaced_asset["path"])) as image:
            self.assertEqual(image.getpixel((0, 0)), (200, 100, 50))

        removed_path = os.path.join(self.project_path, second.asset["path"])
        self.assertTrue(self.manager.delete_image(second.asset["id"]))
        self.assertFalse(os.path.exists(removed_path))
        self.assertEqual(len(self.service.list_assets("01 车辆外观")), 1)


if __name__ == "__main__":
    unittest.main()
