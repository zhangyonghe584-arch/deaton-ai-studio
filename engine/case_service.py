import json
import os
import tempfile
from datetime import datetime


CASE_INFO_FIELDS = (
    "brand",
    "model",
    "year",
    "region",
    "fault_category",
    "service_type",
    "programming_type",
    "equipment_used",
    "repair_result",
)


class CaseService:
    """Persists image-case metadata in the existing project.json contract."""

    def __init__(self, project_path):
        self.project_path = project_path
        self.metadata_path = os.path.join(project_path, "project.json")

    def load_project(self):
        with open(self.metadata_path, encoding="utf-8") as file:
            project = json.load(file)

        project.setdefault("schema_version", 1)
        project.setdefault("case_info", {})
        project.setdefault("assets", [])
        project.setdefault("exports", [])
        project.setdefault("images", {})
        project.setdefault("videos", [])
        return project

    def save_case_info(self, values):
        project = self.load_project()
        case_info = project["case_info"]

        for field in CASE_INFO_FIELDS:
            if field in values:
                case_info[field] = str(values[field]).strip()

        project["vehicle"] = " ".join(
            value for value in (case_info.get("brand", ""), case_info.get("model", "")) if value
        )
        project["fault"] = case_info.get("fault_category", "")
        project["service"] = case_info.get("service_type", "")
        project["updated"] = datetime.now().isoformat()
        self._write_project(project)
        return case_info.copy()

    def load_case_info(self):
        project = self.load_project()
        return {
            field: project["case_info"].get(field, "")
            for field in CASE_INFO_FIELDS
        }

    def add_asset(self, asset):
        project = self.load_project()
        project["assets"].append(asset)
        project["images"].setdefault(asset["category"], []).append(asset["id"])
        project["updated"] = datetime.now().isoformat()
        self._write_project(project)

    def list_assets(self, category=None):
        assets = self.load_project()["assets"]
        if category is None:
            return list(assets)
        return [asset for asset in assets if asset.get("category") == category]

    def get_asset(self, asset_id):
        for asset in self.load_project()["assets"]:
            if asset.get("id") == asset_id:
                return asset
        return None

    def record_export(self, export):
        project = self.load_project()
        project["exports"].append(export)
        project["updated"] = datetime.now().isoformat()
        self._write_project(project)

    def list_exports(self):
        return list(self.load_project()["exports"])

    def _write_project(self, project):
        directory = os.path.dirname(self.metadata_path)
        file_descriptor, temporary_path = tempfile.mkstemp(
            dir=directory,
            prefix="project-",
            suffix=".json",
        )
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
                json.dump(project, file, ensure_ascii=False, indent=4)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.metadata_path)
        except Exception:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)
            raise
