"""Jinja2-based template engine for generating HTML/CSS/JS artifacts."""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .style_tokens import compute_css_variables


TEMPLATES_BASE_DIR = Path(__file__).resolve().parents[2] / "templates"


def _build_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_BASE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # You may add globals/filters here if needed
    return env


# PUBLIC_INTERFACE
def render_site(
    site_ctx: Dict[str, Any],
    pages: List[Dict[str, Any]],
    theme_branding: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """Render the complete site into a dictionary of path->content strings.

    Parameters:
    - site_ctx: global context with site_title, navigation, footer, etc.
    - pages: list of page contexts, each with name, title, and content data.
    - theme_branding: optional branding dict to derive CSS variables.

    Returns:
    Dict mapping output relative paths (e.g., 'index.html', 'assets/styles.css') to file content.
    """
    env = _build_env()

    # Compute CSS variables for style layer
    css_variables = compute_css_variables(theme_branding)
    site_ctx = dict(site_ctx)
    site_ctx["css_variables"] = css_variables

    artifacts: Dict[str, str] = {}

    # Stylesheet
    styles_tpl = env.get_template("base/styles/ocean.css.j2")
    artifacts["assets/styles.css"] = styles_tpl.render(css_vars=css_variables, site=site_ctx)

    # Script
    script_tpl = env.get_template("base/scripts/main.js.j2")
    artifacts["assets/main.js"] = script_tpl.render(site=site_ctx)

    # HTML pages
    base_tpl = env.get_template("base/page.html")
    for page in pages:
        page_ctx = dict(site_ctx)
        page_ctx["page"] = page

        html = base_tpl.render(site=page_ctx)
        out_name = "index.html" if page.get("name") in ("home", "index") else f"{page.get('name')}.html"
        artifacts[out_name] = html

    return artifacts
