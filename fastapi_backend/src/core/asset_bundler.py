"""Asset bundler to assemble generated artifacts into a deliverable structure.

This module doesn't write to disk; it returns an in-memory bundle that later
routes can compress or stream to clients.
"""
from __future__ import annotations

from typing import Dict, Any
import io
import zipfile
import datetime as dt


# PUBLIC_INTERFACE
def create_bundle(artifacts: Dict[str, str]) -> Dict[str, Any]:
    """Create an in-memory ZIP bundle from the provided artifacts.

    Parameters:
    - artifacts: map of relative path -> file content (text)

    Returns:
    Dict with:
      - filename: default bundle name
      - bytes: raw bytes of the zip
      - file_count: number of files
      - created_at: ISO timestamp
    """
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, content in artifacts.items():
            zf.writestr(path, content)
    mem.seek(0)
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat()
    return {
        "filename": "site_bundle.zip",
        "bytes": mem.getvalue(),
        "file_count": len(artifacts),
        "created_at": now,
    }
