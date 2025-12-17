"""Core module to parse free-form requirements text into structured specifications.

This module provides utilities to extract key details from the user's idea and
requirements text. It returns structured objects usable by the template engine
and bundler.
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional
import re

from .models import PageSpec, FeatureSpec, BrandingSpec, StyleOverrides


# PUBLIC_INTERFACE
def parse_requirements_text(
    idea: str,
    requirements_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Parse idea and optional free-form requirements into structured hints.

    The parser is intentionally heuristic and lightweight. It detects:
    - Pages (e.g., 'home', 'about', 'contact', 'blog')
    - Features (contact form, blog, analytics)
    - Branding hints (colors, font)
    - Style overrides (CSS variables in key:value pairs within a 'variables:' block)

    Parameters:
    - idea: Short description of the user's idea for the website.
    - requirements_text: Optional more detailed free-form text.

    Returns:
    Dict with potential keys: pages, features, branding, style_overrides, notes.
    """
    text = f"{idea}\n{requirements_text or ''}".lower()

    pages = _extract_pages(text)
    features = _extract_features(text)
    branding = _extract_branding(text)
    style_overrides = _extract_style_overrides(text)

    result: Dict[str, Any] = {}
    if pages:
        result["pages"] = [PageSpec(name=p, title=p.title()) for p in pages]
    if features:
        result["features"] = [FeatureSpec(name=f, enabled=True) for f in features]
    if branding:
        result["branding"] = BrandingSpec(**branding)
    if style_overrides:
        result["style_overrides"] = StyleOverrides(**style_overrides)

    # Notes may include any extra items we didn't recognize
    result["notes"] = "Parsed heuristics from free-form requirements."
    return result


def _extract_pages(text: str) -> List[str]:
    candidates = ["home", "landing", "about", "contact", "services", "portfolio", "blog", "faq", "pricing"]
    found = {c for c in candidates if re.search(rf"\\b{re.escape(c)}\\b", text)}
    # Normalize 'landing' to 'home'
    pages = [("home" if p == "landing" else p) for p in found]
    # Ensure 'home' always exists as default
    if "home" not in pages:
        pages.insert(0, "home")
    # Keep order deterministic
    return sorted(set(pages), key=pages.index)


def _extract_features(text: str) -> List[str]:
    mapping = {
        "contact form": "contact_form",
        "form": "contact_form",
        "blog": "blog",
        "analytics": "analytics",
        "google analytics": "analytics",
        "newsletter": "newsletter",
        "subscribe": "newsletter",
    }
    found: List[str] = []
    for pattern, key in mapping.items():
        if pattern in text:
            found.append(key)
    # Deduplicate while preserving order
    seen = set()
    ordered = []
    for f in found:
        if f not in seen:
            seen.add(f)
            ordered.append(f)
    return ordered


def _extract_branding(text: str) -> Dict[str, Any]:
    branding: Dict[str, Any] = {}
    color_regex = r"#(?:[0-9a-fA-F]{3}){1,2}\\b"

    # Primary color
    primary_match = re.search(r"primary color[:\\s]+(" + color_regex + r"|[a-zA-Z]+)", text)
    if primary_match:
        branding["primary_color"] = primary_match.group(1)

    # Secondary color
    secondary_match = re.search(r"secondary color[:\\s]+(" + color_regex + r"|[a-zA-Z]+)", text)
    if secondary_match:
        branding["secondary_color"] = secondary_match.group(1)

    # Accent color
    accent_match = re.search(r"accent color[:\\s]+(" + color_regex + r"|[a-zA-Z]+)", text)
    if accent_match:
        branding["accent_color"] = accent_match.group(1)

    # Font
    font_match = re.search(r"font(?: family)?[:\\s]+([a-zA-Z\\-\\s]+)", text)
    if font_match:
        branding["font_family"] = font_match.group(1).strip()

    return branding


def _extract_style_overrides(text: str) -> Dict[str, Any]:
    # Look for a variables block like:
    # variables:
    #   --brand-radius: 8px
    #   --brand-shadow: 0 1px 2px rgba(0,0,0,.1)
    block_match = re.search(r"variables:\\s*(.*)", text, re.DOTALL)
    css_vars: Dict[str, str] = {}
    if block_match:
        # parse key:value lines until a blank line or end
        rest = block_match.group(1)
        for line in rest.splitlines():
            line = line.strip()
            if not line:
                break
            if ":" in line:
                key, val = line.split(":", 1)
                css_vars[key.strip()] = val.strip()
    return {"css_variables": css_vars} if css_vars else {}
