from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from core.case_store import CaseStore
from core.local_renderer import generate


class LocalGenerationService:
    """Runs the bundled Pillow renderer and records 15 preview files."""

    def __init__(self, store: CaseStore):
        self.store = store

    def generate(self, case_dir: Path | str) -> list[Path]:
        parameter_path = self.store.write_generation_parameters(case_dir)
        files = generate(parameter_path)
        manifest = self.store.load(case_dir)
        manifest["generation"] = {
            "preview_files": [str(path) for path in files],
            "last_generated_at": datetime.now(timezone.utc).isoformat(),
            "save_path": manifest.get("generation", {}).get("save_path", ""),
        }
        self.store.save(case_dir, manifest)
        return files

    def copy_to(self, case_dir: Path | str, destination: Path | str) -> list[Path]:
        """Save the latest 3 x 5 result into a vehicle-named folder."""
        destination_path = Path(destination)
        destination_path.mkdir(parents=True, exist_ok=True)
        manifest = self.store.load(case_dir)
        data = manifest.get("information", {})
        pieces = [data.get("brand", ""), data.get("model", ""), data.get("year", "")]
        label = " ".join(piece.strip() for piece in pieces if piece.strip()) or manifest.get("title", "vehicle")
        label = re.sub(r'[<>:"/\\|?*]+', "-", label).strip(" .") or "vehicle"
        vehicle_dir = destination_path / label
        vehicle_dir.mkdir(exist_ok=True)
        files = [Path(path) for path in manifest.get("generation", {}).get("preview_files", [])]
        copied = []
        for source in files:
            if not source.is_file():
                continue
            template_name = source.parent.name
            template_dir = vehicle_dir / template_name
            template_dir.mkdir(exist_ok=True)
            target = template_dir / source.name
            shutil.copy2(source, target)
            copied.append(target)
        return copied
