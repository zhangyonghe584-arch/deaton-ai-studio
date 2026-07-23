# Single-workbench image MVP plan

## Goal

Deliver a Windows desktop application that opens from a desktop shortcut and converts one local automotive programming case into a six-image, 9:16 PNG set.

## Fixed scope

- Home screen: create or open one local case.
- One four-step workbench: assets, case information, AI plan, generate/save.
- Six fixed single-image slots; empty slots are valid and the same slot accepts a replacement drag-and-drop image.
- Optional, editable dropdown case information.
- Manually initiated, bounded OpenAI analysis only.
- Local Pillow script generation, in-app preview, case-local output, and user-selected copy destination.
- PyInstaller EXE and desktop shortcut scripts.

## Explicit exclusions

No video features, multi-page navigation, image ordering, asset states, replacement/status controls, automatic uploads, automatic asset scanning, AI image generation, AI video generation, or API-key persistence.
