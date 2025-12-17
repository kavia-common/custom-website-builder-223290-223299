"""Validation utilities for generation requests and artifacts."""
from __future__ import annotations

from typing import Dict, Any, List


# PUBLIC_INTERFACE
def validate_site_context(site_ctx: Dict[str, Any]) -> List[str]:
    """Validate global site context fields.

    Checks for presence and type of common fields needed by templates.
    Returns a list of error messages; empty means valid.
    """
    errors: List[str] = []
    if "site_title" not in site_ctx or not isinstance(site_ctx["site_title"], str) or not site_ctx["site_title"].strip():
        errors.append("site_title must be a non-empty string.")
    if "navigation" in site_ctx and not isinstance(site_ctx["navigation"], list):
        errors.append("navigation must be a list when provided.")
    if "footer" in site_ctx and not isinstance(site_ctx["footer"], dict):
        errors.append("footer must be a dict when provided.")
    return errors


# PUBLIC_INTERFACE
def validate_pages(pages: List[Dict[str, Any]]) -> List[str]:
    """Validate page list used for rendering.

    Each page must have a 'name' and a 'title' string.
    """
    errors: List[str] = []
    if not isinstance(pages, list) or not pages:
        return ["pages must be a non-empty list."]

    for idx, page in enumerate(pages):
        if not isinstance(page, dict):
            errors.append(f"page[{idx}] must be an object.")
            continue
        if not page.get("name") or not isinstance(page.get("name"), str):
            errors.append(f"page[{idx}].name must be a non-empty string.")
        if not page.get("title") or not isinstance(page.get("title"), str):
            errors.append(f"page[{idx}].title must be a non-empty string.")
    return errors
