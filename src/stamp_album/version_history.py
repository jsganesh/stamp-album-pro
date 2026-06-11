"""
Version history storage (P2-15).

Stores snapshots of DSL files as JSON in ~/StampAlbum/.versions/
Each file gets a directory with timestamped snapshots.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

VERSIONS_DIR = Path.home() / "StampAlbum" / ".versions"
MAX_VERSIONS_PER_FILE = 50  # Keep last 50 versions


def _get_file_dir(filename: str) -> Path:
    """Get the version directory for a file."""
    # Hash the filename to avoid filesystem issues
    name_hash = hashlib.md5(filename.encode()).hexdigest()[:12]
    file_dir = VERSIONS_DIR / f"{name_hash}_{filename[:50]}"
    file_dir.mkdir(parents=True, exist_ok=True)
    return file_dir


def save_version(filename: str, dsl: str, comment: str = "") -> dict:
    """Save a new version of a file. Returns the version metadata."""
    file_dir = _get_file_dir(filename)
    timestamp = datetime.now(timezone.utc)
    version_id = timestamp.strftime("%Y%m%d_%H%M%S_%f")

    version = {
        "id": version_id,
        "filename": filename,
        "timestamp": timestamp.isoformat(),
        "comment": comment,
        "dsl_hash": hashlib.sha256(dsl.encode()).hexdigest()[:16],
        "dsl_length": len(dsl),
    }

    # Save metadata
    meta_path = file_dir / f"{version_id}.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(version, f, indent=2)

    # Save DSL content
    content_path = file_dir / f"{version_id}.slbum"
    with open(content_path, "w", encoding="utf-8") as f:
        f.write(dsl)

    # Prune old versions
    _prune_versions(file_dir)

    return version


def get_versions(filename: str) -> list[dict]:
    """Get all versions for a file, newest first."""
    file_dir = _get_file_dir(filename)
    versions = []
    for meta_path in sorted(file_dir.glob("*.json"), reverse=True):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                versions.append(json.load(f))
        except (json.JSONDecodeError, IOError):
            continue
    return versions


def get_version(filename: str, version_id: str) -> Optional[str]:
    """Get the DSL content of a specific version."""
    file_dir = _get_file_dir(filename)
    content_path = file_dir / f"{version_id}.slbum"
    if content_path.exists():
        with open(content_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def delete_version(filename: str, version_id: str) -> bool:
    """Delete a specific version."""
    file_dir = _get_file_dir(filename)
    meta_path = file_dir / f"{version_id}.json"
    content_path = file_dir / f"{version_id}.slbum"
    deleted = False
    if meta_path.exists():
        meta_path.unlink()
        deleted = True
    if content_path.exists():
        content_path.unlink()
        deleted = True
    return deleted


def _prune_versions(file_dir: Path):
    """Remove old versions beyond MAX_VERSIONS_PER_FILE."""
    meta_files = sorted(file_dir.glob("*.json"))
    if len(meta_files) > MAX_VERSIONS_PER_FILE:
        for old_meta in meta_files[:-MAX_VERSIONS_PER_FILE]:
            version_id = old_meta.stem
            old_meta.unlink()
            content_path = file_dir / f"{version_id}.slbum"
            if content_path.exists():
                content_path.unlink()


def get_version_count(filename: str) -> int:
    """Get the number of versions for a file."""
    file_dir = _get_file_dir(filename)
    return len(list(file_dir.glob("*.json")))
