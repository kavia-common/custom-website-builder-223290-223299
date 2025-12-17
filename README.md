# custom-website-builder-223290-223299

## Overview
This repository contains a FastAPI backend that receives user input and requirements to generate a custom static website based on the user's idea and project details. It renders HTML/CSS/JS from Jinja2 templates and can optionally persist a ZIP bundle for download.

## Endpoints
- GET / — Health check
- GET /api/v1/styles — Returns default Ocean Professional theme tokens, computed CSS variables, and the allowed override keys
- POST /api/v1/generate — Validates input, renders pages, bundles assets, optionally persists a ZIP, and returns inline assets plus an optional zipUrl
- POST /api/v1/preview — Renders a single-page preview and returns inline artifacts

Browse /docs for interactive Swagger UI and /openapi.json for the raw OpenAPI spec.

## Quickstart
1) Install dependencies:
   - Python >= 3.11
   - pip install -r fastapi_backend/requirements.txt

2) Run the server (example with uvicorn):
   - uvicorn fastapi_backend.src.api.main:app --host 0.0.0.0 --port 3001 --reload

3) Open the docs:
   - http://localhost:3001/docs

## Configuration
Environment variables:
- BASE_URL — Optional. If set (e.g., https://example.com), download URLs in responses are absolute.
- STORAGE_BACKEND — Default: local. Currently only "local" is implemented.
- STORAGE_TTL_MIN — Default: 60. Reserved for future cleanup jobs.

## Examples
- Example payloads: fastapi_backend/examples/sample_request.json
- OpenAPI spec: fastapi_backend/interfaces/openapi.json
- Additional schema and styling notes: fastapi_backend/interfaces/openapi_additions.md

## Styling
The default theme is "Ocean Professional". The GET /api/v1/styles endpoint returns:
- theme metadata
- computed cssVariables
- allowedOverrideKeys usable via GenerationRequest.style_overrides.css_variables

Global CSS may also be appended via GenerationRequest.style_overrides.global_css.

## Error Handling
All error responses are wrapped in an error envelope and include an X-Request-ID for correlation. See handlers in fastapi_backend/src/api/errors.py.