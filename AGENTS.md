# Deaton AI Studio Development Rules

## Project Overview

Deaton AI Studio is a local desktop application for Deaton Auto.

Purpose:

- Automotive case image production
- Automotive case video production
- AI assisted content planning
- Local project management


## Development Rules

1. Do not change the overall architecture without approval.

2. Keep modules separated.

Structure:

ui/
    Interface pages

engine/
    File processing and project management

ai/
    AI API related functions

templates/
    Production templates

config/
    Configuration files


## Current Functions

Image Case:

- Six category image upload
- Drag and drop support
- Project based storage


Categories:

01 Vehicle
02 Fault
03 Diagnosis
04 Programming
05 Result
06 Technical


## Future Functions

- Video production
- AI analysis
- AI image generation
- Template management
- Case database


## Coding Requirements

- Python
- PySide6
- Keep code readable
- Avoid unnecessary rewrites
- Do not delete existing functions
- Test before modifying


## Important

This is a commercial internal tool.

Do not create a simple demo.

All features should consider future expansion.