from __future__ import annotations

import json
import re
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


# ---- Generic helpers ----

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def is_semver(value: object) -> bool:
    return isinstance(value, str) and bool(SEMVER_RE.match(value or ""))


def sanitize_id(raw: str) -> str:
    """Sanitize a string into a DOT-safe identifier (letters, digits, underscore)."""
    return re.sub(r"[^A-Za-z0-9_]", "_", raw)


def extract_graph(manifest: dict):
    """Extract nodes and edges from manifest for graphing.

    Returns tuple: (pack_ids, page_titles, dep_edges, include_edges)
    - dep_edges: (from_pack, to_pack) as recorded in manifest (depends_on)
    - include_edges: (pack, page)
    """
    packs_dict = manifest.get('packs') or {}
    pages_dict = manifest.get('pages') or {}
    pack_ids = list(packs_dict.keys())
    page_titles = list(pages_dict.keys())
    dep_edges: list[tuple[str, str]] = []
    include_edges: list[tuple[str, str]] = []
    for pid, meta in packs_dict.items():
        for dep in meta.get('depends_on', []) or []:
            if dep in packs_dict:
                dep_edges.append((pid, dep))
        for title in meta.get('pages', []) or []:
            if title in pages_dict:
                include_edges.append((pid, title))
    return pack_ids, page_titles, dep_edges, include_edges


def categorize_packs(manifest: dict) -> dict[str, str]:
    """Categorize packs by simple heuristics for styling.

    - meta:        no pages, depends_on >= 2
    - aggregator:  pages > 0 and depends_on >= 1
    - content:     pages > 0 and depends_on == 0
    - other:       everything else
    """
    packs = manifest.get('packs') or {}
    categories: dict[str, str] = {}
    for pid, meta in packs.items():
        pages_count = len(meta.get('pages') or [])
        deps_count = len(meta.get('depends_on') or [])
        if pages_count == 0 and deps_count >= 2:
            categories[pid] = 'meta'
        elif pages_count > 0 and deps_count >= 1:
            categories[pid] = 'aggregator'
        elif pages_count > 0 and deps_count == 0:
            categories[pid] = 'content'
        else:
            categories[pid] = 'other'
    return categories


