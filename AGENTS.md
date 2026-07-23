# Deaton Auto Image Case Studio

## Product boundary

This repository is a Windows local image-case application. It has a single home screen and a single four-step workbench: assets, case information, AI plan, and generate/save. Do not add video workflows, complex navigation, bulk asset management, item ordering, state controls, replacement buttons, or automatic AI scanning.

## Core contracts

- `core.case_store.CaseStore` owns a compact local `case.json`, six fixed one-image slots, and the case's `output/` directory.
- A new case seeds the sixth `logo` slot with `resources/branding/deaton_auto_logo.png`; users replace it by dropping a new image into that same slot.
- `config/options.json` contains expandable dropdown suggestions. Every field remains editable and optional.
- `core.ai_plan.OpenAIPlanService` only makes a request when the UI's manual action invokes it. It may send at most three explicitly checked images, compressed locally; API keys come only from `OPENAI_API_KEY`.
- `core.local_renderer` is the bundled Pillow renderer; `scripts/generate_case.py` is its development command-line wrapper. Both receive one generated JSON parameter file and emit six 1080×1920 PNGs to the case output directory.
- `core.generation.LocalGenerationService` invokes the bundled renderer directly so the packaged EXE does not require a Python installation.

## Delivery

- `scripts/build_windows.ps1` creates the `DeatonAutoImageStudio.exe` PyInstaller build.
- `scripts/install_desktop_shortcut.ps1` creates the desktop shortcut.
- Validate the core workflow with `python -m unittest discover -s tests -v`.
- The default Windows data path is `Documents/Deaton Auto Cases`; it can be overridden with `DEATON_PROJECTS_DIR`.
