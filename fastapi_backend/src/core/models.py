from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class PageSpec(BaseModel):
    """Specification for an individual page in the generated website."""

    name: str = Field(..., description="Unique name/slug for the page, e.g., 'home' or 'about'.")
    title: Optional[str] = Field(None, description="Human-readable page title shown in the document head or header.")
    route: Optional[str] = Field(None, description="Explicit route path. Defaults to '/{name}' if not provided.")
    sections: Optional[List[str]] = Field(
        default=None,
        description="List of section identifiers or templates to include on the page."
    )
    components: Optional[List[str]] = Field(
        default=None,
        description="Optional list of component identifiers to include or prioritize."
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Arbitrary data payload for templating this page."
    )


# PUBLIC_INTERFACE
class FeatureSpec(BaseModel):
    """Functional features to enable in the generated site (e.g., contact form, blog)."""

    name: str = Field(..., description="Feature name, e.g., 'contact_form', 'blog', 'analytics'.")
    enabled: bool = Field(True, description="Whether the feature should be enabled.")
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional feature configuration options."
    )


# PUBLIC_INTERFACE
class BrandingSpec(BaseModel):
    """Branding specification for colors, typography, and basic assets."""

    primary_color: Optional[str] = Field(None, description="Primary brand color in hex or CSS color format.")
    secondary_color: Optional[str] = Field(None, description="Secondary brand color in hex or CSS color format.")
    accent_color: Optional[str] = Field(None, description="Accent color for emphasis elements.")
    font_family: Optional[str] = Field(None, description="Preferred font family.")
    logo_url: Optional[str] = Field(None, description="URL to a logo image to incorporate into the site.")


# PUBLIC_INTERFACE
class StyleOverrides(BaseModel):
    """Fine-grained style overrides to apply to the generated site."""

    css_variables: Optional[Dict[str, str]] = Field(
        default=None,
        description="Map of CSS variable names to values to inject."
    )
    global_css: Optional[str] = Field(
        default=None,
        description="Raw CSS string to append globally."
    )
    component_styles: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Per-component style configuration or CSS snippets."
    )


# PUBLIC_INTERFACE
class GenerationRequest(BaseModel):
    """Request payload for initiating a website generation run."""

    idea: str = Field(..., description="Short description of the user's idea for the website.")
    requirements: Optional[str] = Field(
        default=None,
        description="Detailed project requirements, constraints, and goals."
    )
    pages: Optional[List[PageSpec]] = Field(
        default=None,
        description="List of page specifications to include."
    )
    features: Optional[List[FeatureSpec]] = Field(
        default=None,
        description="List of features/capabilities to enable."
    )
    branding: Optional[BrandingSpec] = Field(
        default=None,
        description="Branding color palette and typography."
    )
    style_overrides: Optional[StyleOverrides] = Field(
        default=None,
        description="Optional fine-grained style overrides."
    )
    target_stack: Optional[str] = Field(
        default=None,
        description="Desired output technology stack (e.g., 'react', 'nextjs', 'static-html')."
    )


# PUBLIC_INTERFACE
class GenerationMeta(BaseModel):
    """Metadata describing a generation job."""

    request_id: str = Field(..., description="Unique identifier for the generation request.")
    status: str = Field(..., description="Current status of the generation job (e.g., 'pending', 'running', 'done', 'error').")
    started_at: Optional[str] = Field(None, description="ISO8601 timestamp when generation started.")
    finished_at: Optional[str] = Field(None, description="ISO8601 timestamp when generation completed.")
    message: Optional[str] = Field(None, description="Optional status message or error detail.")


# PUBLIC_INTERFACE
class GenerationResponse(BaseModel):
    """Response returned upon accepting a generation request."""

    meta: GenerationMeta = Field(..., description="Metadata about the generation job.")
    preview_url: Optional[str] = Field(
        default=None,
        description="If available, a URL to preview the generated site."
    )
    download_url: Optional[str] = Field(
        default=None,
        description="If available, a URL to download the generated artifact (e.g., zip)."
    )


# PUBLIC_INTERFACE
class PreviewResponse(BaseModel):
    """Response for preview details of a generation run."""

    request_id: str = Field(..., description="Unique identifier for the generation request.")
    available: bool = Field(..., description="Whether the preview is currently available.")
    preview_url: Optional[str] = Field(
        default=None,
        description="A URL to the preview if available."
    )
    expires_at: Optional[str] = Field(
        default=None,
        description="ISO8601 expiration time for the preview link, if applicable."
    )
