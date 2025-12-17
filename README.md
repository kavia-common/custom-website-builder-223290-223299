# custom-website-builder-223290-223299

FastAPI backend exposes:

- GET / -> health
- GET /api/v1/styles -> default style tokens and allowed override keys
- POST /api/v1/generate -> generate website artifacts, persist ZIP optionally
- POST /api/v1/preview -> render a single-page preview

See /docs for OpenAPI details. Configure BASE_URL, STORAGE_BACKEND, STORAGE_TTL_MIN via environment if needed.