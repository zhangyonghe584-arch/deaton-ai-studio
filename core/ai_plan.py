from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Iterable

from PIL import Image


class OpenAIPlanService:
    """Makes explicit, low-volume OpenAI requests for an editable case plan."""

    max_images = 3
    max_edge = 1280
    jpeg_quality = 72

    def __init__(self, api_key: str | None = None, model: str | None = None):
        # The UI may supply a locally configured key. Environment variables remain
        # supported for command-line use and backwards compatibility.
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("DEATON_OPENAI_MODEL", "gpt-4.1-mini")

    def analyze(self, information: dict[str, str], image_paths: Iterable[Path | str]) -> str:
        if not self.api_key:
            raise RuntimeError("Set OPENAI_API_KEY before requesting an analysis.")

        selected_paths = [Path(path) for path in image_paths if Path(path).is_file()][: self.max_images]
        content = [{"type": "input_text", "text": self._prompt(information, len(selected_paths))}]
        for path in selected_paths:
            content.append({"type": "input_image", "image_url": self._compressed_data_url(path), "detail": "low"})

        from openai import OpenAI

        response = OpenAI(api_key=self.api_key).responses.create(
            model=self.model,
            input=[{"role": "user", "content": content}],
            max_output_tokens=900,
        )
        return response.output_text.strip()

    def _compressed_data_url(self, image_path: Path) -> str:
        with Image.open(image_path) as image:
            image = image.convert("RGB")
            image.thumbnail((self.max_edge, self.max_edge), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=self.jpeg_quality, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"

    @staticmethod
    def _prompt(information: dict[str, str], image_count: int) -> str:
        facts = "\n".join(f"- {label}: {value or 'Not provided'}" for label, value in information.items())
        return f"""You are preparing a factual Deaton Auto remote-programming image case.\nUse only the case details and {image_count} explicitly selected reference images below. Do not infer vehicle faults, software, diagnosis, or results that are not shown or supplied.\n\nCase details:\n{facts}\n\nReturn concise, editable English copy in exactly these headings:\nTITLE\nCASE SUMMARY\nDIAGNOSIS POINTS\nPROGRAMMING POINTS\nRESULT\nLOCAL DESIGN NOTES\n\nUse 2-4 bullet points beneath each non-title heading. LOCAL DESIGN NOTES must be instructions for a local image layout script, not a request to create an image."""
