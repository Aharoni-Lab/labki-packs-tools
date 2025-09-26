from __future__ import annotations

import json
from pathlib import Path
import yaml


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that raises on duplicate mapping keys to prevent silent overrides."""

    def construct_mapping(self, node, deep: bool = False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key: {key}",
                    key_node.start_mark,
                )
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


def load_yaml(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return yaml.load(f, Loader=UniqueKeyLoader)


def load_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


