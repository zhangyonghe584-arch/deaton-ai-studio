from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.constants import CASE_FIELDS, DEFAULT_LOGO, DEFAULT_OPTIONS, IMAGE_EXTENSIONS, PROJECTS_DIR, RESOURCE_DIR, SLOT_SPECS


class CaseStore:
    """Owns the small, local-on-disk case format used by the workbench."""

    manifest_name = "case.json"

    def __init__(self, projects_dir: Path | str = PROJECTS_DIR, options_file: Path | str | None = None):
        self.projects_dir = Path(projects_dir)
        self.options_file = Path(options_file) if options_file else RESOURCE_DIR / "config" / "options.json"

    def create(self, title: str) -> Path:
        slug = self._slug(title) or "untitled-case"
        case_dir = self._available_case_dir(slug)
        assets_dir = case_dir / "assets"
        assets_dir.mkdir(parents=True)
        (case_dir / "output").mkdir()
        manifest = self._default_manifest(title.strip() or "Untitled case")
        if DEFAULT_LOGO.is_file():
            logo_path = assets_dir / "logo.png"
            shutil.copy2(DEFAULT_LOGO, logo_path)
            manifest["assets"]["logo"] = logo_path.relative_to(case_dir).as_posix()
        self._write_manifest(case_dir, manifest)
        return case_dir

    def load(self, case_dir: Path | str) -> dict[str, Any]:
        path = self._manifest_path(case_dir)
        with path.open(encoding="utf-8") as file:
            stored = json.load(file)
        manifest = self._default_manifest(stored.get("title", "Untitled case"))
        manifest.update(stored)
        manifest["assets"] = {key: manifest.get("assets", {}).get(key, "") for key, _ in SLOT_SPECS}
        manifest["information"] = {key: manifest.get("information", {}).get(key, "") for key, _ in CASE_FIELDS}
        return manifest

    def save(self, case_dir: Path | str, manifest: dict[str, Any]) -> None:
        manifest["updated_at"] = self._timestamp()
        self._write_manifest(Path(case_dir), manifest)

    def set_information(self, case_dir: Path | str, values: dict[str, str]) -> dict[str, Any]:
        manifest = self.load(case_dir)
        manifest["information"].update({key: str(values.get(key, "")).strip() for key, _ in CASE_FIELDS})
        self.save(case_dir, manifest)
        return manifest

    def set_ai_plan(self, case_dir: Path | str, plan: str, confirmed: bool) -> dict[str, Any]:
        manifest = self.load(case_dir)
        manifest["ai_plan"] = {"content": plan.strip(), "confirmed": bool(confirmed), "updated_at": self._timestamp()}
        self.save(case_dir, manifest)
        return manifest

    def set_save_path(self, case_dir: Path | str, save_path: Path | str) -> dict[str, Any]:
        manifest = self.load(case_dir)
        manifest.setdefault("generation", {})["save_path"] = str(Path(save_path).resolve())
        self.save(case_dir, manifest)
        return manifest

    def set_asset(self, case_dir: Path | str, slot: str, source: Path | str) -> dict[str, Any]:
        if slot not in dict(SLOT_SPECS):
            raise ValueError(f"Unknown asset slot: {slot}")
        source_path = Path(source)
        if not source_path.is_file() or source_path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError("Choose a supported local image file")
        case_path = Path(case_dir)
        target = case_path / "assets" / f"{slot}{source_path.suffix.lower()}"
        for existing in (case_path / "assets").glob(f"{slot}.*"):
            existing.unlink()
        shutil.copy2(source_path, target)
        manifest = self.load(case_path)
        manifest["assets"][slot] = target.relative_to(case_path).as_posix()
        self.save(case_path, manifest)
        return manifest

    def asset_path(self, case_dir: Path | str, slot: str) -> Path | None:
        relative_path = self.load(case_dir)["assets"].get(slot, "")
        path = Path(case_dir) / relative_path if relative_path else None
        return path if path and path.is_file() else None

    def write_generation_parameters(self, case_dir: Path | str) -> Path:
        case_path = Path(case_dir)
        manifest = self.load(case_path)
        parameter_path = case_path / "generation-parameters.json"
        payload = {
            "case_dir": str(case_path.resolve()),
            "information": manifest["information"],
            "assets": {key: str((case_path / value).resolve()) if value else "" for key, value in manifest["assets"].items()},
            "ai_plan": manifest["ai_plan"],
            "use_ai": bool(manifest.get("use_ai", False)),
        }
        parameter_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return parameter_path

    def options(self) -> dict[str, list[str]]:
        options = {key: list(values) for key, values in DEFAULT_OPTIONS.items()}
        if self.options_file.is_file():
            with self.options_file.open(encoding="utf-8") as file:
                configured = json.load(file)
            for key, values in configured.items():
                if key in options and isinstance(values, list):
                    options[key] = [str(value).strip() for value in values if str(value).strip()]
        return options

    def model_options(self) -> dict[str, list[str]]:
        """Return the bilingual-brand keyed model catalog, if configured."""
        if not self.options_file.is_file():
            return {}
        with self.options_file.open(encoding="utf-8") as file:
            configured = json.load(file)
        models = configured.get("models_by_brand", {})
        return {str(key): [str(value) for value in values if str(value).strip()]
                for key, values in models.items() if isinstance(values, list)}

    def country_options(self) -> dict[str, list[str]]:
        """Return countries grouped by the selectable geographic region."""
        if not self.options_file.is_file():
            return {}
        with self.options_file.open(encoding="utf-8") as file:
            configured = json.load(file)
        countries = configured.get("countries_by_region", {})
        return {str(key): [str(value) for value in values if str(value).strip()]
                for key, values in countries.items() if isinstance(values, list)}

    def _default_manifest(self, title: str) -> dict[str, Any]:
        now = self._timestamp()
        return {
            "format_version": 1,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "assets": {key: "" for key, _ in SLOT_SPECS},
            "information": {key: "" for key, _ in CASE_FIELDS},
            "ai_plan": {"content": "", "confirmed": False, "updated_at": ""},
            "use_ai": False,
            "generation": {"preview_files": [], "last_generated_at": "", "save_path": ""},
        }

    def _available_case_dir(self, slug: str) -> Path:
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        candidate = self.projects_dir / slug
        number = 2
        while candidate.exists():
            candidate = self.projects_dir / f"{slug}-{number}"
            number += 1
        return candidate

    def _manifest_path(self, case_dir: Path | str) -> Path:
        path = Path(case_dir) / self.manifest_name
        if not path.is_file():
            raise FileNotFoundError(f"Not a Deaton case: {case_dir}")
        return path

    @staticmethod
    def _slug(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _write_manifest(self, case_dir: Path, manifest: dict[str, Any]) -> None:
        temporary_path = case_dir / f".{self.manifest_name}.tmp"
        temporary_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary_path.replace(case_dir / self.manifest_name)
