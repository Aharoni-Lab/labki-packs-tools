from __future__ import annotations

import os
from pathlib import Path

from .result_types import ValidationResult


def validate_pages(manifest_path: Path, pages: dict) -> tuple[ValidationResult, set[Path]]:
    """
    Validate all pages listed in the manifest.

    Checks:
      • Page titles include namespaces (warn if missing).
      • Each page entry has a 'file' path.
      • Each referenced file exists.
      • Module pages use '.lua' extension and correct directory.
    Returns:
      (ValidationResult, set of referenced absolute file paths)
    """
    result = ValidationResult()
    referenced_abs_paths: set[Path] = set()

    for title, meta in pages.items():
        # Title should normally include a namespace (e.g., Template:, Module:, Form:)
        if ":" not in title:
            result.add_warning(f"Title missing namespace: {title}")

        # File path presence
        file_rel = meta.get("file")
        if not file_rel:
            result.add_error(f"Page '{title}' missing file path")
            continue

        abs_path = (manifest_path.parent / file_rel).resolve()
        referenced_abs_paths.add(abs_path)

        # File existence
        if not abs_path.exists():
            result.add_error(f"Page file not found: {file_rel} (for {title})")

        # Module-specific rules
        inferred_ns = title.split(":", 1)[0] if ":" in title else None
        if inferred_ns == "Module":
            # Must be .lua extension
            if abs_path.suffix != ".lua":
                result.add_warning(f"Module files should use .lua extension: {file_rel}")
            # Must be under pages/Modules/
            if "Modules" not in file_rel.replace("\\", "/"):
                result.add_warning(
                    f"Module files should be stored under pages/Modules/: {file_rel}"
                )

    return result, referenced_abs_paths


def detect_orphans(manifest_path: Path, referenced_abs_paths: set[Path]) -> ValidationResult:
    """
    Detect .wiki or .md page files under 'pages/' that are not referenced in the manifest.

    Returns:
        ValidationResult (warnings only)
    """
    result = ValidationResult()
    pages_dir = (manifest_path.parent / "pages").resolve()
    if not pages_dir.exists():
        return result

    for root, _dirs, files in os.walk(pages_dir):
        for fname in files:
            if not (fname.endswith(".wiki") or fname.endswith(".md")):
                continue
            f_abs = Path(root) / fname
            if f_abs not in referenced_abs_paths:
                rel = os.path.relpath(f_abs, manifest_path.parent)
                result.add_warning(f"Orphan page file not referenced in manifest: {rel}")

    return result
