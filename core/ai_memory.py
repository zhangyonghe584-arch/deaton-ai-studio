from __future__ import annotations

import json
from pathlib import Path


DEFAULT_RULES = [
    "Use any available 1-5 case images plus the supplied logo for AI preview and planning; never block analysis only because fewer than five photos exist.",
    "The logo area contains only the supplied logo; no added brand text, step labels, numbers, or placeholders.",
    "Keep source photos centered and non-cropped so vehicle exterior and instrument details are not hidden.",
    "Generate three genuinely different layout directions, not the same skeleton with changed colors.",
    "AI analyzes and writes an execution plan; the local Pillow code must consume that saved plan and generate the images. Never stop at a written proposal.",
]


class ProjectMemory:
    """Small local memory: reusable rules plus a bounded history of confirmed plans."""

    def __init__(self, projects_dir: Path | str):
        self.path = Path(projects_dir) / ".deaton_ai_memory.json"

    def read(self) -> dict:
        if not self.path.is_file():
            return {"rules": DEFAULT_RULES[:], "history": []}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return {"rules": value.get("rules", DEFAULT_RULES[:]), "history": value.get("history", [])}
        except (OSError, ValueError, TypeError):
            return {"rules": DEFAULT_RULES[:], "history": []}

    def context(self, max_chars: int = 5000) -> str:
        value = self.read()
        rules = "\n".join(f"- {item}" for item in value["rules"])
        history = "\n".join(f"- {item}" for item in value["history"][-3:])
        result = rules + (f"\nRecent confirmed lessons:\n{history}" if history else "")
        return result[:max_chars]

    def record(self, note: str) -> None:
        if not note.strip():
            return
        value = self.read()
        value["history"] = (value["history"] + [note.strip()])[-10:]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
