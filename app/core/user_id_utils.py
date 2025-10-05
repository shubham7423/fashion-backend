import re
from fastapi import HTTPException
from pathlib import Path


def normalize_user_id(user_id: str, base_dir: str = None) -> str:
    """
    Normalize and validate a user_id for safe filesystem usage.
    - Strips whitespace
    - Replaces /, \, .., and other disallowed chars with _
    - Rejects absolute paths or traversal attempts
    - Optionally checks that the resolved path is a descendant of base_dir
    """
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(
            status_code=400, detail="User ID is required and must be a string."
        )
    user_id = user_id.strip()
    # Disallow path traversal and absolute paths
    if user_id.startswith(("/", "\\")) or ".." in user_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID: path traversal or absolute path not allowed.",
        )
    # Only allow alphanumerics, dash, underscore, and dot
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]", "_", user_id)
    if not safe_id:
        raise HTTPException(
            status_code=400, detail="User ID is empty after normalization."
        )
    if base_dir:
        # Ensure the resolved path is a descendant of base_dir
        base = Path(base_dir).resolve()
        candidate = (base / safe_id).resolve()
        if not str(candidate).startswith(str(base)):
            raise HTTPException(
                status_code=400, detail="User ID resolves outside allowed directory."
            )
    return safe_id
