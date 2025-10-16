from labki_packs_tools.validation.result_types import ValidationItem
from labki_packs_tools.validation.validators.base import Validator


class PackPagesValidator(Validator):
    code = "pack-pages"
    message = "Pages referenced in packs must be valid"
    level = "error"

    def validate(self, *, packs: dict, pages: dict, **kwargs) -> list[ValidationItem]:
        items = []
        seen_page_to_pack = {}

        for pack_id, meta in (packs or {}).items():
            pages_list = meta.get("pages", [])
            if pages_list and not isinstance(pages_list, list):
                items.append(
                    ValidationItem(
                        level=self.level,
                        message=f"Pack '{pack_id}' pages must be an array",
                        code=self.code,
                    )
                )
                continue

            for title in pages_list or []:
                if title not in pages:
                    items.append(
                        ValidationItem(
                            level=self.level,
                            message=f"Pack '{pack_id}' references unknown page title: {title}",
                            code=self.code,
                        )
                    )
                elif title in seen_page_to_pack and seen_page_to_pack[title] != pack_id:
                    other = seen_page_to_pack[title]
                    items.append(
                        ValidationItem(
                            level=self.level,
                            message=(
                                f"Page title '{title}' included in multiple packs ('{other}' and '{pack_id}'). "
                                "Move to a shared dependency pack."
                            ),
                            code=self.code,
                        )
                    )
                else:
                    seen_page_to_pack[title] = pack_id
        return items
