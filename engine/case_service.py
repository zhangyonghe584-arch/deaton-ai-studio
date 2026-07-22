import json
import os
import tempfile
from datetime import datetime


CASE_INFO_FIELDS = (
    "customer_name",
    "customer_region",
    "brand",
    "model",
    "year",
    "vin",
    "license_plate",
    "mileage",
    "engine_model",
    "fault_category",
    "fault_description",
    "service_type",
    "programming_type",
    "equipment_used",
    "repair_result",
    "technical_notes",
)

ASSET_STATUSES = ("待整理", "已审核", "已替换")


class CaseService:
    """Persists case details and image asset lifecycle metadata in project.json."""

    def __init__(self, project_path):
        self.project_path = project_path
        self.metadata_path = os.path.join(project_path, "project.json")

    def load_project(self):
        with open(self.metadata_path, encoding="utf-8") as file:
            project = json.load(file)

        project.setdefault("schema_version", 2)
        project.setdefault("case_info", {})
        project.setdefault("assets", [])
        project.setdefault("exports", [])
        project.setdefault("images", {})
        project.setdefault("videos", [])
        self._normalize_assets(project["assets"])
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
        return self.load_case_info()

    def load_case_info(self):
        project = self.load_project()
        return {
            field: project["case_info"].get(field, "")
            for field in CASE_INFO_FIELDS
        }

    def add_asset(self, asset):
        project = self.load_project()
        category_assets = [
            item for item in project["assets"] if item.get("category") == asset["category"]
        ]
        asset.setdefault("status", "待整理")
        asset.setdefault("sort_order", len(category_assets))
        asset.setdefault("is_primary", False)
        project["assets"].append(asset)
        project["images"].setdefault(asset["category"], []).append(asset["id"])
        project["updated"] = datetime.now().isoformat()
        self._write_project(project)

    def list_assets(self, category=None):
        assets = self.load_project()["assets"]
        if category is not None:
            assets = [asset for asset in assets if asset.get("category") == category]
        return sorted(assets, key=lambda asset: (asset.get("sort_order", 0), asset.get("created", "")))

    def get_asset(self, asset_id):
        for asset in self.load_project()["assets"]:
            if asset.get("id") == asset_id:
                return asset
        return None

    def set_asset_status(self, asset_id, status):
        if status not in ASSET_STATUSES:
            raise ValueError("未知的素材状态")
        return self.update_asset(asset_id, {"status": status})

    def set_primary_asset(self, asset_id):
        project = self.load_project()
        selected = self._find_asset(project, asset_id)
        if selected is None:
            raise ValueError("未找到素材")

        for asset in project["assets"]:
            asset["is_primary"] = asset["id"] == asset_id
        selected["updated"] = datetime.now().isoformat()
        project["updated"] = datetime.now().isoformat()
        self._write_project(project)
        return selected

    def reorder_assets(self, category, asset_ids):
        project = self.load_project()
        category_assets = [asset for asset in project["assets"] if asset.get("category") == category]
        by_id = {asset["id"]: asset for asset in category_assets}
        ordered = [by_id.pop(asset_id) for asset_id in asset_ids if asset_id in by_id]
        ordered.extend(sorted(by_id.values(), key=lambda asset: asset.get("sort_order", 0)))

        for order, asset in enumerate(ordered):
            asset["sort_order"] = order
            asset["updated"] = datetime.now().isoformat()
        project["updated"] = datetime.now().isoformat()
        self._write_project(project)
        return ordered

    def update_asset(self, asset_id, values):
        project = self.load_project()
        asset = self._find_asset(project, asset_id)
        if asset is None:
            raise ValueError("未找到素材")

        for field in ("path", "original_filename", "status"):
            if field in values:
                asset[field] = values[field]
        asset["updated"] = datetime.now().isoformat()
        project["updated"] = datetime.now().isoformat()
        self._write_project(project)
        return asset

    def remove_asset(self, asset_id):
        project = self.load_project()
        asset = self._find_asset(project, asset_id)
        if asset is None:
            return None

        project["assets"] = [item for item in project["assets"] if item["id"] != asset_id]
        category_ids = project["images"].get(asset["category"], [])
        project["images"][asset["category"]] = [item for item in category_ids if item != asset_id]
        if asset.get("is_primary"):
            category_assets = [
                item for item in project["assets"] if item.get("category") == asset["category"]
            ]
            if category_assets:
                category_assets[0]["is_primary"] = True
        project["updated"] = datetime.now().isoformat()
        self._write_project(project)
        return asset

    def record_export(self, export):
        project = self.load_project()
        project["exports"].append(export)
        project["updated"] = datetime.now().isoformat()
        self._write_project(project)

    def list_exports(self):
        return list(self.load_project()["exports"])

    @staticmethod
    def _find_asset(project, asset_id):
        for asset in project["assets"]:
            if asset.get("id") == asset_id:
                return asset
        return None

    @staticmethod
    def _normalize_assets(assets):
        for order, asset in enumerate(assets):
            asset.setdefault("status", "待整理")
            asset.setdefault("sort_order", order)
            asset.setdefault("is_primary", False)

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
