from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, status
from pydantic import BaseModel, Field

from ...config import resolve_download_url
from ...core.asset_bundler import create_bundle
from ...core.models import (
    GenerationRequest,
    GenerationMeta,
)
from ...core.requirements_parser import parse_requirements_text
from ...core.style_tokens import DEFAULT_THEME, compute_css_variables
from ...core.template_engine import render_site
from ...core.validators import validate_pages, validate_site_context
from ...infrastructure.storage import get_storage


class _InlineAsset(BaseModel):
    path: str = Field(..., description="Relative path of the asset in the bundle.")
    content: str = Field(..., description="Raw text content of the asset.")


# PUBLIC_INTERFACE
def get_router() -> APIRouter:
    """Return the APIRouter for generation endpoints.

    Routes
    - POST /api/v1/generation/generate and POST /api/v1/generate
    - GET /api/v1/generation/styles and GET /api/v1/styles
    - POST /api/v1/generation/preview and POST /api/v1/preview

    The router is created lazily to avoid import side effects in app startup.
    """
    router = APIRouter(prefix="/generation", tags=["Generation"])

    @router.get(
        "/",
        summary="List generation capabilities",
        description="List available generation capabilities and API contract.",
        operation_id="generation_list_capabilities",
        responses={200: {"description": "Successful Response"}},
    )
    def list_capabilities():
        """Return a description of generation capabilities and key endpoints."""
        return {
            "message": "Generation API surface is available.",
            "endpoints": [
                "POST /api/v1/generate",
                "GET /api/v1/styles",
                "POST /api/v1/preview",
            ],
        }

    # PUBLIC_INTERFACE
    @router.get(
        "/styles",
        summary="Get default style tokens",
        description="Return the default Ocean Professional theme tokens and allowed override keys.",
        operation_id="generation_get_styles",
    )
    def get_styles():
        """Provide clients with default theme tokens and override guidance."""
        default_vars = compute_css_variables({})
        allowed_override_keys = sorted(list(default_vars.keys()))
        return {
            "theme": DEFAULT_THEME,
            "cssVariables": default_vars,
            "allowedOverrideKeys": allowed_override_keys,
        }

    class GenerateOptions(BaseModel):
        persist_zip: bool = Field(
            default=True,
            description="If true, persist the generated ZIP and return a download URL.",
        )

    class GenerateResponseModel(BaseModel):
        meta: GenerationMeta
        zipUrl: Optional[str] = Field(
            default=None, description="Optional URL for downloading the generated ZIP."
        )
        assets: List[_InlineAsset] = Field(
            default_factory=list,
            description="Inline artifact listing for quick client-side preview.",
        )
        warnings: Optional[List[str]] = Field(
            default=None, description="Non-fatal warnings encountered during processing."
        )

    # PUBLIC_INTERFACE
    @router.post(
        "/generate",
        summary="Generate website artifacts",
        description=(
            "Validate GenerationRequest, parse requirements, merge style tokens, render templates, "
            "bundle assets, optionally persist the zip using LocalStorage, and return inline assets with an optional zipUrl."
        ),
        operation_id="generation_generate",
        response_model=GenerateResponseModel,
        status_code=status.HTTP_200_OK,
    )
    def generate_site(
        request: GenerationRequest = Body(
            ...,
            description="User idea, requirements, and optional structured specs.",
        ),
        options: GenerateOptions = Body(
            default=GenerateOptions(),
            description="Generation options controlling persistence and other behavior.",
        ),
    ):
        """Process a website generation request and return artifacts and optional download link."""
        warnings: List[str] = []

        # Step 1: Parse free-form requirements into hints
        parsed = parse_requirements_text(request.idea, request.requirements)

        # Merge pages: explicit pages override parsed hints if provided
        pages_ctx: List[Dict[str, Any]] = []
        if request.pages:
            for p in request.pages:
                pages_ctx.append(
                    {
                        "name": p.name,
                        "title": p.title or p.name.title(),
                        "route": p.route or f"/{p.name}",
                        "sections": p.sections or [],
                        "components": p.components or [],
                        "content": (p.data or {}).get("content"),
                        "subtitle": (p.data or {}).get("subtitle"),
                    }
                )
        elif parsed.get("pages"):
            for p in parsed["pages"]:
                pages_ctx.append(
                    {
                        "name": p.name,
                        "title": p.title or p.name.title(),
                        "route": p.route or f"/{p.name}",
                        "sections": [],
                        "components": [],
                    }
                )
        else:
            # Default to a home page
            pages_ctx = [{"name": "home", "title": "Home", "route": "/"}]

        # Site/global context
        site_ctx: Dict[str, Any] = {
            "site_title": request.idea.strip()[:80] if request.idea else "My Site",
            "navigation": [{"label": "Home", "href": "index.html"}]
            + [
                {
                    "label": p.get("title") or p.get("name", "Page").title(),
                    "href": "index.html" if p.get("name") == "home" else f"{p.get('name')}.html",
                }
                for p in pages_ctx
                if p.get("name") != "home"
            ],
            "footer": {
                "links": [
                    {"label": "Privacy", "href": "#"},
                    {"label": "Terms", "href": "#"},
                ]
            },
            "year": dt.datetime.utcnow().year,
        }

        # Basic validation
        site_errors = validate_site_context(site_ctx)
        page_errors = validate_pages(pages_ctx)
        warnings.extend([f"site: {e}" for e in site_errors])
        warnings.extend([f"pages: {e}" for e in page_errors])
        if page_errors:
            # Cannot proceed without valid pages
            raise HTTPException(
                status_code=422,
                detail={"message": "Invalid pages", "errors": page_errors},
            )

        # Branding/style merge: request.branding overrides parsed branding
        branding_dict: Dict[str, Any] = {}
        if parsed.get("branding"):
            branding_dict.update(parsed["branding"].model_dump())
        if request.branding:
            branding_dict.update(request.branding.model_dump(exclude_none=True))

        # Compute CSS variables and allow fine-grained overrides
        css_vars = compute_css_variables(branding_dict)
        if request.style_overrides and request.style_overrides.css_variables:
            css_vars.update(request.style_overrides.css_variables)

        # Render templates into artifacts
        artifacts = render_site(site_ctx, pages_ctx, branding_dict)

        # If global CSS override provided, append at end of main stylesheet
        if request.style_overrides and request.style_overrides.global_css:
            key = "assets/styles.css"
            artifacts[key] = artifacts.get(key, "") + "\n\n/* user overrides */\n" + request.style_overrides.global_css

        # Bundle to zip (in-memory)
        bundle = create_bundle(artifacts)

        # Optionally persist
        zip_url: Optional[str] = None
        if options.persist_zip:
            # Create deterministic-ish job_id from request content + timestamp
            req_fingerprint = hashlib.sha256(
                json.dumps(request.model_dump(mode="json", exclude_none=True), sort_keys=True).encode("utf-8")
            ).hexdigest()[:10]
            ts = dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")
            job_id = f"job-{ts}-{req_fingerprint}"

            storage = get_storage()
            _, rel_path = storage.save_zip(job_id, bundle["bytes"])
            zip_url = resolve_download_url(rel_path)

        # Prepare response model
        meta = GenerationMeta(
            request_id=hashlib.sha1(bundle["bytes"]).hexdigest(),  # lightweight unique-ish id
            status="done",
            started_at=bundle["created_at"],
            finished_at=dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat(),
            message="Generation completed",
        )

        inline_assets = [
            _InlineAsset(path=p, content=c) for p, c in artifacts.items() if len(c) <= 200_000
        ]  # prevent massive payloads

        resp = {
            "meta": meta,
            "zipUrl": zip_url,
            "assets": inline_assets,
        }
        if warnings:
            resp["warnings"] = warnings
        return resp

    class PreviewRequest(BaseModel):
        title: str = Field(..., description="Title for the preview page.")
        subtitle: Optional[str] = Field(None, description="Optional subtitle for the preview page.")
        content_html: Optional[str] = Field(
            None, description="Optional HTML content to embed within the preview content section."
        )
        branding: Optional[Dict[str, Any]] = Field(
            default=None, description="Optional branding overrides for the preview."
        )
        style_overrides: Optional[Dict[str, str]] = Field(
            default=None, description="Optional CSS variable overrides for preview."
        )

    class PreviewResponseModel(BaseModel):
        request_id: str
        available: bool
        preview: Dict[str, str] = Field(
            ..., description="Inline preview assets with keys: index.html, assets/styles.css, assets/main.js"
        )
        warnings: Optional[List[str]] = None

    # PUBLIC_INTERFACE
    @router.post(
        "/preview",
        summary="Render a single-page preview",
        description="Render a one-page preview with inline CSS and JS, returning artifacts and any parser/validation warnings.",
        operation_id="generation_preview",
        response_model=PreviewResponseModel,
    )
    def preview(req: PreviewRequest):
        """Render a preview using the base templates and provided content."""
        warnings: List[str] = []

        page = {
            "name": "home",
            "title": req.title.strip() if req.title else "Preview",
            "subtitle": req.subtitle,
            "content": req.content_html,
        }
        pages_ctx = [page]

        site_ctx: Dict[str, Any] = {
            "site_title": page["title"],
            "navigation": [{"label": "Home", "href": "index.html"}],
            "footer": {"links": []},
            "year": dt.datetime.utcnow().year,
        }

        # Validation
        site_errors = validate_site_context(site_ctx)
        page_errors = validate_pages(pages_ctx)
        warnings.extend([f"site: {e}" for e in site_errors])
        warnings.extend([f"pages: {e}" for e in page_errors])
        if page_errors:
            raise HTTPException(
                status_code=422,
                detail={"message": "Invalid preview page", "errors": page_errors},
            )

        branding = req.branding or {}
        css_vars = compute_css_variables(branding)
        if req.style_overrides:
            css_vars.update(req.style_overrides)

        # Render artifacts
        artifacts = render_site(site_ctx, pages_ctx, branding)

        request_id = hashlib.md5(
            json.dumps(
                {
                    "title": req.title,
                    "subtitle": req.subtitle,
                    "branding": branding,
                    "style_overrides": req.style_overrides,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

        return PreviewResponseModel(
            request_id=request_id,
            available=True,
            preview=artifacts,
            warnings=warnings or None,
        )

    # Additionally expose the endpoints at the API root (/api/v1) by registering aliases.
    # These "no-prefix" routes will be mounted by the main API router at /api/v1.
    public_router = APIRouter(tags=["Generation"])

    # PUBLIC_INTERFACE
    @public_router.get(
        "/styles",
        summary="Get default style tokens",
        description="Return the default Ocean Professional theme tokens and allowed override keys.",
        operation_id="styles_get",
    )
    def public_get_styles():
        return get_styles()  # reuse logic

    # PUBLIC_INTERFACE
    @public_router.post(
        "/generate",
        summary="Generate website artifacts",
        description="Generate artifacts and optionally persist a ZIP, returning inline assets and an optional zipUrl.",
        operation_id="generate_post",
        response_model=GenerateResponseModel,
        status_code=status.HTTP_200_OK,
    )
    def public_generate(
        request: GenerationRequest = Body(
            ...,
            description="User idea, requirements, and optional structured specs.",
        ),
        options: GenerateOptions = Body(
            default=GenerateOptions(),
            description="Generation options controlling persistence and other behavior.",
        ),
    ):
        return generate_site(request=request, options=options)

    # PUBLIC_INTERFACE
    @public_router.post(
        "/preview",
        summary="Render a single-page preview",
        description="Render a one-page preview with inline CSS and JS.",
        operation_id="preview_post",
        response_model=PreviewResponseModel,
    )
    def public_preview(req: "PreviewRequest"):
        return preview(req)

    # Attach the public router without prefix when included upstream
    router.include_router(public_router, prefix="")

    return router


# Expose router instance for easy import in app
router = get_router()
