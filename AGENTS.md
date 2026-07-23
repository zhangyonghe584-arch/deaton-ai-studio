# Deaton Auto Image Case Studio

## Product boundary

This repository is a Windows local image-case application. It opens directly into a four-step workbench: assets, case information, AI plan, and generate/save. The primary purpose is image production, not case browsing or display. Do not add video workflows, complex navigation, bulk asset management, item ordering, state controls, replacement buttons, or automatic AI scanning.

## Core contracts

- `core.case_store.CaseStore` owns a compact local `case.json`, six fixed one-image slots, and the case's `output/` directory.
- A new case seeds the sixth `logo` slot with `resources/branding/deaton_auto_logo.png`; users replace it by dropping a new image into that same slot.
- `config/options.json` contains expandable dropdown suggestions. Every field remains editable and optional.
- `core.ai_plan.OpenAIPlanService` only makes a request when the UI's manual action invokes it. It sends 1–5 explicitly checked case images plus the supplied logo, all compressed locally; API keys come from the UI's local settings or `OPENAI_API_KEY`.
- `core.ai_memory.ProjectMemory` stores a small local set of project rules and bounded confirmed lessons. It is included in future AI planning so the system improves without relying on chat history. Never store API keys or source images in this memory.
- `core.local_renderer` is the bundled Pillow renderer; `scripts/generate_case.py` is its development command-line wrapper. Both receive one generated JSON parameter file and emit five 1080×1920 PNGs to the case output directory.
- `core.generation.LocalGenerationService` invokes the bundled renderer directly so the packaged EXE does not require a Python installation.

## Delivery

- `scripts/build_windows.ps1` creates the `DeatonAutoImageStudio.exe` PyInstaller build.
- `scripts/install_desktop_shortcut.ps1` creates the desktop shortcut.
- Validate the core workflow with `python -m unittest discover -s tests -v`.
- The default Windows data path is `Documents/Deaton Auto Cases`; it can be overridden with `DEATON_PROJECTS_DIR`.

## AI planning rules

- AI analyzes the available 1–5 case images, the logo, and case information; it does not redraw photos or logos. Five output images remain the production target even when fewer source photos are supplied.
- The plan must allocate content across five output images and include three materially different layout directions.
- The logo area is logo-only. Do not add brand text, `STEP`, step labels, image numbers, case IDs, or placeholder digits.
- Source photos are centered and non-cropping so vehicle and instrument details remain visible.
- Keep AI calls manual and low-cost; local Pillow code remains responsible for image generation.
