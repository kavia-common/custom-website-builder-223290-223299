"""Style token utilities to compute CSS variables from theme and branding."""
from __future__ import annotations

from typing import Dict, Any, Optional

DEFAULT_THEME = {
    "name": "Ocean Professional",
    "primary": "#2563EB",   # blue-600
    "secondary": "#F59E0B", # amber-500
    "success": "#10B981",   # emerald-500
    "error": "#EF4444",     # red-500
    "background": "#f9fafb",
    "surface": "#ffffff",
    "text": "#111827",
    "radius": "10px",
    "shadow": "0 1px 2px rgba(0,0,0,.06), 0 1px 1px rgba(0,0,0,.04)",
}


# PUBLIC_INTERFACE
def compute_css_variables(branding: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Compute a map of CSS custom properties for the site based on branding.

    The output can be injected into a :root block or used to render a CSS template.

    Parameters:
    - branding: optional dict with keys like primary_color, secondary_color, accent_color, font_family.

    Returns:
    A dict mapping CSS variable names (with -- prefix) to values.
    """
    branding = branding or {}
    vars_map: Dict[str, str] = {
        "--color-primary": branding.get("primary_color") or DEFAULT_THEME["primary"],
        "--color-secondary": branding.get("secondary_color") or DEFAULT_THEME["secondary"],
        "--color-accent": branding.get("accent_color") or DEFAULT_THEME["secondary"],
        "--color-bg": DEFAULT_THEME["background"],
        "--color-surface": DEFAULT_THEME["surface"],
        "--color-text": DEFAULT_THEME["text"],
        "--radius-md": DEFAULT_THEME["radius"],
        "--elev-1": DEFAULT_THEME["shadow"],
        "--font-family": branding.get("font_family") or "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple Color Emoji', 'Segoe UI Emoji'",
    }
    return vars_map
