from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Iterable

from PIL import Image


class OpenAIPlanService:
    """Makes explicit, low-volume OpenAI requests for an editable case plan."""

    # Production can still use five case slots, but AI planning is useful with
    # any available amount of evidence. The logo is an additional reference.
    min_images = 1
    max_images = 5
    max_edge = 1280
    jpeg_quality = 72

    def __init__(self, api_key: str | None = None, model: str | None = None):
        # The UI may supply a locally configured key. Environment variables remain
        # supported for command-line use and backwards compatibility.
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("DEATON_OPENAI_MODEL", "gpt-4.1-mini")

    def analyze(
        self,
        information: dict[str, str],
        image_paths: Iterable[Path | str],
        logo_path: Path | str | None = None,
        memory: str = "",
    ) -> str:
        if not self.api_key:
            raise RuntimeError("Set OPENAI_API_KEY before requesting an analysis.")

        selected_paths = [Path(path) for path in image_paths if Path(path).is_file()][: self.max_images]
        if not selected_paths:
            raise ValueError("至少需要 1 张案例图片才能进行 AI 分析。")
        logo = Path(logo_path) if logo_path else None
        content = [{"type": "input_text", "text": self._prompt(information, len(selected_paths), bool(logo and logo.is_file()), memory)}]
        for path in selected_paths:
            content.append({"type": "input_image", "image_url": self._compressed_data_url(path), "detail": "low"})
        if logo and logo.is_file():
            content.append({"type": "input_text", "text": "Reference image below is the official logo. Preserve it exactly; do not redesign or add text over its logo area."})
            content.append({"type": "input_image", "image_url": self._compressed_data_url(logo), "detail": "low"})

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
    def _prompt(information: dict[str, str], image_count: int, has_logo: bool = False, memory: str = "") -> str:
        facts = "\n".join(f"- {label}: {value or 'Not provided'}" for label, value in information.items())
        return f"""You are preparing a factual Deaton Auto remote-programming image case.
Use all {image_count} explicitly selected case images together{', plus the official logo reference' if has_logo else ''}. One to five case images are valid; do not require five images before analyzing. Do not infer vehicle faults, software, diagnosis, or results that are not shown or supplied.

Accumulated project memory (binding rules and lessons from prior runs):
{memory or 'No prior memory yet.'}

Case details:
{facts}

Return concise, editable English copy in exactly these headings:
TITLE
CASE SUMMARY
DIAGNOSIS POINTS
PROGRAMMING POINTS
RESULT
LOCAL DESIGN NOTES

Use 2-4 bullet points beneath each non-title heading. Only describe a completed case suitable for public proof of work. Never output uncertain or unfinished wording such as "pending", "awaiting", "needs further diagnosis", "follow-up recommended", "customer confirmation required", or "to be confirmed". LOCAL DESIGN NOTES must assign content across exactly five output images and describe three genuinely different layout directions for the local renderer. If fewer than five photos are supplied, explicitly mark which output images reuse an available photo or rely on supplied case facts; never invent a missing photo. The logo area must contain only the supplied logo; never add brand text, step labels, STEP, image numbers, case IDs, or placeholder digits. Preserve every source photo without cropping important vehicle or instrument information; use centered, non-cropping placement. Keep the plan factual and inexpensive to execute locally. The plan is an execution input, not a final answer: it will be saved locally and passed to the Pillow renderer to generate the five images."""

