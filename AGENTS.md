# Deaton AI Studio AI Development Rules


## Project

Project Name:

Deaton AI Studio


## Purpose

This is a professional Windows desktop software developed for Deaton Auto.

The software is used for automotive remote programming case production.


## Development Rules

- Read existing code before modification.
- Do not randomly change project architecture.
- Do not delete existing functions.
- Keep modules independent.
- Test after changes.
- Maintain clean code structure.


## Technology

Language:

Python


Framework:

PySide6


Target:

Windows Desktop Application


## Architecture

Keep separation:

ui/
User interface

engine/
Business logic

ai/
AI API functions

templates/
Production templates

resources/
Static resources

config/
Configuration


## Important

This is not a demo project.

The final goal is a real daily-use commercial internal tool.

## Current MVP Contracts

- `engine.case_service.CaseService` owns `project.json` metadata for case info, imported assets, and export history while preserving legacy fields.
- `engine.image_manager.ImageManager.import_image()` keeps the existing six image categories and records imported files as assets; retain `save_image()` compatibility.
- `engine.image_renderer.ImageCaseRenderer` is the template boundary. The current MVP supports only the fixed `case_cover` image export; do not add video or AI behavior here.
- Verify the core workflow with: `python -m unittest -v test_project.py test_image_case_mvp.py`.
