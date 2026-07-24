from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.case_store import CaseStore
from core.local_renderer import generate


class LocalGenerationService:
    """Runs the bundled Pillow script and records its local preview files."""

    def __init__(self, store: CaseStore):
        self.store = store

    def generate(self, case_dir: Path | str) -> list[Path]:
        manifest = self.store.load(case_dir)
        if manifest.get("use_ai", False) and (
            not manifest["ai_plan"].get("content", "").strip()
            or not manifest["ai_plan"].get("confirmed", False)
        ):
            raise ValueError("No confirmed local AI plan is available; confirm the plan before generating images.")
        parameter_path = self.store.write_generation_parameters(case_dir)
        files = generate(parameter_path)
        manifest = self.store.load(case_dir)
        manifest["generation"] = {
            "preview_files": [str(path) for path in files],
            "last_generated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.save(case_dir, manifest)
        return files

    def copy_to(self, case_dir: Path | str, destination: Path | str) -> list[Path]:
        import shutil

        destination_path = Path(destination)
        destination_path.mkdir(parents=True, exist_ok=True)
        preview_files = [Path(path) for path in self.store.load(case_dir)["generation"]["preview_files"]]
        copied = []
        for source in preview_files:
            if source.is_file():
                target = destination_path / source.name
                shutil.copy2(source, target)
                copied.append(target)
        return copied
