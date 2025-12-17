# OpenAPI Additions and Schema Notes

## Overview
This FastAPI backend exposes a small set of endpoints to generate static website artifacts from user input. The service defines structured request/response models and centralizes styling through the Ocean Professional design theme. This document complements the generated OpenAPI with schema details and guidance on how to use the style system effectively.

## Endpoints Summary
- GET "/" — Health check
- GET "/api/v1/styles" — Retrieve default theme tokens and the allowed CSS variable override keys
- POST "/api/v1/generate" — Generate a multi‑page site bundle, optionally persisted as a ZIP, and return inline assets
- POST "/api/v1/preview" — Render a single‑page preview and return inline artifacts

For the full machine-readable specification, see interfaces/openapi.json or the live /openapi.json and /docs endpoints when the server is running.

## Schemas

### GenerationRequest
Represents a site generation request combining a short idea, optional free‑form requirements, and optional structured configuration.

Fields:
- idea: string (required) — Short description of the website concept.
- requirements: string (optional) — Free‑form requirements. Heuristics extract pages, features, and branding hints.
- pages: PageSpec[] (optional) — Explicit page definitions; take precedence over parsed pages.
- features: FeatureSpec[] (optional) — Feature toggles such as "contact_form" or "blog".
- branding: BrandingSpec (optional) — Primary brand attributes (colors, font, logo).
- style_overrides: StyleOverrides (optional) — Fine‑grained styling control (CSS variables, global CSS, per‑component styles).
- target_stack: string (optional) — Desired output stack; current implementation renders static HTML/CSS/JS.

Model source: fastapi_backend/src/core/models.py (GenerationRequest)

### PageSpec
Defines a single page in the site.

Fields:
- name: string (required) — Slug like "home", "about".
- title: string (optional) — Display title. Defaults to title‑cased name.
- route: string (optional) — Route path; defaults to "/{name}".
- sections: string[] (optional) — Section identifiers for future templating expansion.
- components: string[] (optional) — Component identifiers for future templating expansion.
- data: object (optional) — Arbitrary page‑specific data; commonly supports "subtitle" and "content" which are used by base templates.

Model source: fastapi_backend/src/core/models.py (PageSpec)

### FeatureSpec
Fields:
- name: string (required) — e.g., "contact_form", "blog", "analytics".
- enabled: boolean (default: true)
- options: object (optional)

Model source: fastapi_backend/src/core/models.py (FeatureSpec)

### BrandingSpec
Fields:
- primary_color: string (optional) — Color in hex or CSS format.
- secondary_color: string (optional)
- accent_color: string (optional)
- font_family: string (optional)
- logo_url: string (optional)

Model source: fastapi_backend/src/core/models.py (BrandingSpec)

### StyleOverrides
Fields:
- css_variables: object<string,string> (optional) — Direct CSS custom property overrides such as "--color-primary".
- global_css: string (optional) — Additional global CSS appended to the end of assets/styles.css.
- component_styles: object (optional) — Reserved for future per‑component styling snippets.

Model source: fastapi_backend/src/core/models.py (StyleOverrides)

### GenerateResponseModel
Returned from POST /api/v1/generate.

Fields:
- meta: GenerationMeta — Includes request_id, status, timestamps, message.
- zipUrl: string|null — Download link when persistence is enabled.
- assets: array<{ path: string, content: string }> — Inline artifacts for immediate preview.
- warnings: string[]|null — Non‑fatal validation or parsing notes.

Source: fastapi_backend/src/api/routes/generation.py (GenerateResponseModel)

### PreviewRequest and PreviewResponseModel
- PreviewRequest: { title: string, subtitle?: string, content_html?: string, branding?: object, style_overrides?: object<string,string> }
- PreviewResponseModel: { request_id: string, available: boolean, preview: object<string,string>, warnings?: string[] }

Source: fastapi_backend/src/api/routes/generation.py

## Styling and Ocean Professional Theme

### Default Theme
The system ships with the Ocean Professional theme:

- Name: "Ocean Professional"
- Primary: #2563EB (blue‑600)
- Secondary: #F59E0B (amber‑500)
- Success: #10B981
- Error: #EF4444
- Background: #f9fafb
- Surface: #ffffff
- Text: #111827
- Radius: 10px
- Shadow: 0 1px 2px rgba(0,0,0,.06), 0 1px 1px rgba(0,0,0,.04)

Source: fastapi_backend/src/core/style_tokens.py (DEFAULT_THEME)

### Computed CSS Variables
Branding and theme produce CSS variables via compute_css_variables:

- --color-primary
- --color-secondary
- --color-accent
- --color-bg
- --color-surface
- --color-text
- --radius-md
- --elev-1
- --font-family

These are injected into assets/styles.css from templates/base/styles/ocean.css.j2. The GET /api/v1/styles endpoint returns the current default map and the allowedOverrideKeys you may set through style_overrides.css_variables.

### How Overrides Are Applied
- BrandingSpec influences the computed variables.
- style_overrides.css_variables directly overrides any computed variables by name.
- style_overrides.global_css is appended verbatim to the end of assets/styles.css for custom rules.
- Preview endpoint accepts a simple style_overrides object mapping variable names to values.

Template sources:
- fastapi_backend/templates/base/styles/ocean.css.j2
- fastapi_backend/templates/base/page.html
- fastapi_backend/templates/base/components/*.html

## Error Model and Request Correlation
All error responses follow a uniform envelope and include X‑Request‑ID:

Payload:
{
  "error": {
    "code": string,
    "message": string,
    "details": object|null,
    "requestId": string
  }
}

Global handlers and envelope definitions live in fastapi_backend/src/api/errors.py. The request ID is also returned via the X‑Request‑ID response header.

## Environment and Download URLs
- STORAGE_BACKEND: "local" (default)
- STORAGE_TTL_MIN: "60" (default)
- BASE_URL: when set, zip download URLs in responses are made absolute by prefixing BASE_URL.

URL resolution is implemented in fastapi_backend/src/config.py (resolve_download_url).

## Notes on Capabilities
- /api/v1/generate produces a consistent in‑memory bundle and optionally persists it as a ZIP using LocalStorage under /tmp. An alias URL under /downloads/generated-sites/{job_id}/site.zip is returned (absolute if BASE_URL is configured).
- /api/v1/preview renders a single page using the base templates and the computed style variables but does not persist artifacts.

Sources:
- fastapi_backend/src/core/models.py
- fastapi_backend/src/api/routes/generation.py
- fastapi_backend/src/core/style_tokens.py
- fastapi_backend/src/core/template_engine.py
- fastapi_backend/src/config.py
- fastapi_backend/src/api/errors.py
- fastapi_backend/interfaces/openapi.json
