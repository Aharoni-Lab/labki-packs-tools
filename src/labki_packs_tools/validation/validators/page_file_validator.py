from pathlib import Path

from labki_packs_tools.validation.result_types import ValidationItem
from labki_packs_tools.validation.validators.base import Validator


class PageFileValidator(Validator):
    code = "page-file"
    message = "Validate page file presence and module placement"
    level = "error"

    def validate(self, *, manifest_path: Path, pages: dict, **kwargs) -> list[ValidationItem]:
        items = []

        for title, meta in pages.items():
            file_rel = meta.get("file")
            if not file_rel:
                items.append(
                    ValidationItem(
                        level="error",
                        message=f"Page '{title}' is missing a 'file' path",
                        code=self.code,
                    )
                )
                continue

            abs_path = (manifest_path.parent / file_rel).resolve()

            # File must exist
            if not abs_path.exists():
                items.append(
                    ValidationItem(
                        level="error",
                        message=f"Page file not found: {file_rel} (for {title})",
                        code=self.code,
                    )
                )

            # Module-specific conventions
            inferred_ns = title.split(":", 1)[0] if ":" in title else None
            if inferred_ns == "Module":
                if abs_path.suffix != ".lua":
                    items.append(
                        ValidationItem(
                            level="warning",
                            message=f"Module files should use .lua extension: {file_rel}",
                            code=self.code,
                        )
                    )
                if "Modules" not in file_rel.replace("\\", "/"):
                    items.append(
                        ValidationItem(
                            level="warning",
                            message=f"Module files should be under pages/Modules/: {file_rel}",
                            code=self.code,
                        )
                    )

        return items
