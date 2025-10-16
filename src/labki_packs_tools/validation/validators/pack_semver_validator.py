from labki_packs_tools.utils import is_semver
from labki_packs_tools.validation.result_types import ValidationItem
from labki_packs_tools.validation.validators.base import Validator


class PackSemverValidator(Validator):
    code = "pack-semver"
    message = "Pack must have semantic version"
    level = "error"

    def validate(self, *, packs: dict, **kwargs) -> list[ValidationItem]:
        items = []
        for pack_id, meta in (packs or {}).items():
            version = meta.get("version")
            if not is_semver(version):
                items.append(ValidationItem(
                    level=self.level,
                    message=f"Pack '{pack_id}' must have semantic version (MAJOR.MINOR.PATCH)",
                    code=self.code
                ))
        return items
