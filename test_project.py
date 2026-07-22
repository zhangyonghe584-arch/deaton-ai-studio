import json
import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from engine.current_project import CurrentProject
from engine.project_manager import ProjectManager

try:
    from PySide6.QtWidgets import QApplication
    from ui.main_window import MainWindow
except ImportError:
    QApplication = None
    MainWindow = None


class ProjectManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication is not None:
            cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.previous_directory = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.addCleanup(os.chdir, self.previous_directory)
        CurrentProject.set_project(None)
        self.addCleanup(CurrentProject.set_project, None)

    def test_create_project_initializes_case_structure_and_metadata(self):
        project_path = ProjectManager().create_project("BMW_G20")

        self.assertIsNotNone(project_path)
        self.assertTrue(os.path.isdir(project_path))
        for folder in (
            "images/01_vehicle",
            "images/02_fault",
            "images/03_diagnosis",
            "images/04_programming",
            "images/05_result",
            "images/06_technical",
            "videos",
            "ai",
            "output",
        ):
            self.assertTrue(os.path.isdir(os.path.join(project_path, folder)))

        with open(os.path.join(project_path, "project.json"), encoding="utf-8") as file:
            metadata = json.load(file)

        self.assertEqual(metadata["project_name"], os.path.basename(project_path))
        self.assertEqual(metadata["images"], {})
        self.assertEqual(metadata["videos"], [])

    def test_new_case_can_be_registered_as_current_project(self):
        project_path = ProjectManager().create_new_case()
        CurrentProject.set_project(project_path)

        self.assertEqual(CurrentProject.get_project(), project_path)
        self.assertTrue(os.path.isdir(project_path))

    @unittest.skipIf(MainWindow is None, "Qt runtime dependencies are unavailable")
    def test_main_window_creates_and_registers_current_case(self):
        window = MainWindow()
        self.addCleanup(window.close)
        self.addCleanup(window.deleteLater)

        project_path = CurrentProject.get_project()

        self.assertIsNotNone(project_path)
        self.assertTrue(os.path.isdir(project_path))
        self.assertTrue(os.path.isfile(os.path.join(project_path, "project.json")))



if __name__ == "__main__":
    unittest.main()
