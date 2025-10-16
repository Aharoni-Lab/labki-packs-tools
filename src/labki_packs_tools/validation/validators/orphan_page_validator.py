import os
from pathlib import Path

from labki_packs_tools.validation.result_types import ValidationItem
from labki_packs_tools.validation.validators.base import Validator


class OrphanPageValidator(Validator):
    code = "page-orphan"
    message = "Detect orphan page files not listed in manifest"
    level = "warning"

    def validate(self, *, manifest_path: Path, pages: dict, **kwargs) -> list[ValidationItem]:
        items = []
        referenced_abs_paths: set[Path] = set()

        for meta in pages.values():
            file_rel = meta.get("file")
            if not file_rel:
                continue
            abs_path = (manifest_path.parent / file_rel).resolve()
            referenced_abs_paths.add(abs_path)

        pages_dir = (manifest_path.parent / "pages").resolve()
        if not pages_dir.exists():
            return items

        for root, _dirs, files in os.walk(pages_dir):
            for fname in files:
                if not (fname.endswith(".wiki") or fname.endswith(".md")):
                    continue
                f_abs = Path(root) / fname
                if f_abs not in referenced_abs_paths:
                    rel = os.path.relpath(f_abs, manifest_path.parent)
                    items.append(
                        ValidationItem(
                            level=self.level,
                            message=f"Orphan page file not referenced in manifest: {rel}",
                            code=self.code,
                        )
                    )

        return items
