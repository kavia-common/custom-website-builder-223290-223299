from __future__ import annotations

import os
from typing import Optional, Dict


class _Config:
    """Simple configuration loader with environment variable overrides.

    Defaults:
      - STORAGE_BACKEND: "local"
      - STORAGE_TTL_MIN: 60
      - BASE_URL: optional; if set, used to form absolute URLs for downloads.

    Environment variables:
      STORAGE_BACKEND, STORAGE_TTL_MIN, BASE_URL
    """

    def __init__(self) -> None:
        # Defaults
        self._data: Dict[str, str] = {
            "STORAGE_BACKEND": "local",
            "STORAGE_TTL_MIN": "60",
        }
        # Load overrides from environment (do not crash on invalid values)
        if os.getenv("STORAGE_BACKEND"):
            self._data["STORAGE_BACKEND"] = os.getenv("STORAGE_BACKEND", "local")
        if os.getenv("STORAGE_TTL_MIN"):
            ttl_val = os.getenv("STORAGE_TTL_MIN", "60")
            # Keep as string internally; convert on access if needed
            self._data["STORAGE_TTL_MIN"] = ttl_val
        if os.getenv("BASE_URL"):
            self._data["BASE_URL"] = os.getenv("BASE_URL", "").rstrip("/")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a config value as string with an optional default."""
        return self._data.get(key, default)

    def get_int(self, key: str, default: int) -> int:
        """Get a config value parsed as int with fallback to default on errors."""
        raw = self._data.get(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    @property
    def storage_backend(self) -> str:
        return self.get("STORAGE_BACKEND", "local") or "local"

    @property
    def storage_ttl_min(self) -> int:
        return self.get_int("STORAGE_TTL_MIN", 60)

    @property
    def base_url(self) -> Optional[str]:
        v = self.get("BASE_URL")
        return v if v else None


_config_singleton = _Config()


# PUBLIC_INTERFACE
def get_config() -> _Config:
    """Return the global configuration accessor.

    Use this to read configuration values across the application. Values are
    read once from environment at import time to keep behavior deterministic
    within a process lifetime.
    """
    return _config_singleton


# PUBLIC_INTERFACE
def resolve_download_url(relative_path: str) -> str:
    """Resolve a download URL for a stored artifact.

    If BASE_URL is configured, return an absolute URL by joining BASE_URL and the
    relative path (ensuring exactly one slash joins them). Otherwise, return the
    relative path unchanged so upstream code can serve it directly or mount static routes.

    Parameters:
      relative_path: e.g., "/downloads/generated-sites/<job_id>/site.zip"

    Returns:
      A URL string suitable for clients.
    """
    base = _config_singleton.base_url
    if not base:
        return relative_path
    if not relative_path.startswith("/"):
        relative_path = "/" + relative_path
    return f"{base}{relative_path}"
