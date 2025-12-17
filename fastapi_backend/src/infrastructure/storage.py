from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple

from ..config import get_config


class Storage(ABC):
    """Abstract storage interface for saving generated artifacts."""

    # PUBLIC_INTERFACE
    @abstractmethod
    def save_zip(self, job_id: str, data: bytes) -> Tuple[str, str]:
        """Persist an in-memory ZIP and return (absolute_path, relative_download_path).

        Parameters:
          job_id: Unique job identifier used to compute storage key/path.
          data: Raw bytes of the zip archive.

        Returns:
          A tuple of:
            - absolute_path: Full file path on disk where the zip was written.
            - relative_download_path: A relative path that API/clients can use for download links.
        """
        raise NotImplementedError


class LocalStorage(Storage):
    """Local filesystem storage implementation.

    Artifacts are saved under /tmp/generated-sites/{job_id}/site.zip.
    The returned relative path is /downloads/generated-sites/{job_id}/site.zip so that
    API routes (or static file mounts) can serve from a known base path without exposing
    internal filesystem paths.
    """

    def __init__(self, base_tmp_dir: Path | None = None) -> None:
        self.base_tmp_dir = base_tmp_dir or Path("/tmp") / "generated-sites"
        # Ensure base dir exists
        self.base_tmp_dir.mkdir(parents=True, exist_ok=True)

    def _target_paths(self, job_id: str) -> Tuple[Path, str]:
        # Absolute path under /tmp
        job_dir = self.base_tmp_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        abs_path = job_dir / "site.zip"
        # Relative download path intended for URL resolution and static mounting
        rel_path = f"/downloads/generated-sites/{job_id}/site.zip"
        return abs_path, rel_path

    # PUBLIC_INTERFACE
    def save_zip(self, job_id: str, data: bytes) -> Tuple[str, str]:
        """Save zip bytes to local filesystem and provide a relative download path."""
        abs_path, relative = self._target_paths(job_id)
        with open(abs_path, "wb") as f:
            f.write(data)

        # Optionally apply TTL metadata (no-op here; left for future cleanup jobs)
        _ = get_config().storage_ttl_min  # Read to make linter aware it's used

        return str(abs_path), relative


# PUBLIC_INTERFACE
def get_storage() -> Storage:
    """Factory to get a Storage implementation based on configuration.

    Currently supports:
      - "local": LocalStorage

    Returns:
      A Storage instance.
    """
    backend = (get_config().storage_backend or "local").lower()
    if backend == "local":
        return LocalStorage()
    # Future: add other backends (e.g., s3, gcs) based on env config.
    # Fallback to local for unknown backends to keep system functional.
    return LocalStorage()
