from typing import Any

from labki_packs_tools.validation.result_types import ValidationItem
from labki_packs_tools.validation.validators.base import Validator


class PackDependencyValidator(Validator):
    code = "pack-deps"
    message = "All pack dependencies must reference valid pack IDs"
    level = "error"

    def validate(self, *, packs: dict, **kwargs: Any) -> list[ValidationItem]:
        items = []
        for pack_id, meta in (packs or {}).items():
            for dep in meta.get("depends_on", []) or []:
                if dep not in packs:
                    items.append(
                        ValidationItem(
                            level=self.level,
                            message=f"Pack '{pack_id}' depends_on unknown pack id: {dep}",
                            code=self.code,
                        )
                    )
        return items
