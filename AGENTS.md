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

- `engine.case_service.CaseService` owns `project.json` metadata for case info, imported assets, asset state/order/main-image selection, and export history while preserving legacy fields.
- `engine.image_manager.ImageManager` keeps the existing six image categories and provides import, replacement, and removal; retain `save_image()` compatibility.
- `engine.brand_service.BrandService` stores the reusable publication identity in `config/brand.json`; do not duplicate it as per-case data.
- `engine.image_renderer.ImageCaseRenderer` is the fixed-template boundary. Current templates are `case_cover`, `diagnosis_summary`, and `result_card`; `render_all()` is the low-step publication workflow.
- Verify the workflow with: `python -m unittest -v test_project.py test_image_case_mvp.py test_case_data_assets.py test_brand_templates.py`.
