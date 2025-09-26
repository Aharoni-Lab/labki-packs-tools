#!/usr/bin/env python3
import argparse
import os
import re
from pathlib import Path

import yaml


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that raises on duplicate mapping keys to prevent silent overrides."""

    def construct_mapping(self, node, deep=False):
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


def _sanitize_id(raw: str) -> str:
    """Sanitize a string into a DOT-safe identifier (letters, digits, underscore)."""
    return re.sub(r"[^A-Za-z0-9_]", "_", raw)


def _extract_graph(manifest: dict):
    """Extract nodes and edges from manifest for graphing.

    Returns:
      packs: list[str] pack ids
      pages: list[str] page titles
      dep_edges: list[tuple[str,str]] (from_pack -> to_pack)
      include_edges: list[tuple[str,str]] (from_pack -> to_page)
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


def emit_dot(manifest: dict) -> str:
    """Emit a Graphviz DOT graph of packs and pages."""
    pack_ids, page_titles, dep_edges, include_edges = _extract_graph(manifest)
    lines: list[str] = []
    lines.append("digraph Manifest {")
    lines.append("  rankdir=LR;")
    lines.append("  node [fontname=\"Helvetica\"];\n")
    # Clusters
    lines.append("  subgraph cluster_packs {")
    lines.append("    label=\"Packs\"; style=rounded;")
    for pid in pack_ids:
        nid = _sanitize_id(f"pack_{pid}")
        label = pid.replace('"', '\\"')
        lines.append(f"    {nid} [label=\"{label}\", shape=box];")
    lines.append("  }")
    lines.append("  subgraph cluster_pages {")
    lines.append("    label=\"Pages\"; style=rounded;")
    for title in page_titles:
        nid = _sanitize_id(f"page_{title}")
        label = title.replace('"', '\\"')
        lines.append(f"    {nid} [label=\"{label}\", shape=ellipse];")
    lines.append("  }\n")
    # Edges: depends_on (pack -> pack)
    for a, b in dep_edges:
        na = _sanitize_id(f"pack_{a}")
        nb = _sanitize_id(f"pack_{b}")
        lines.append(f"  {na} -> {nb};")
    # Edges: includes (pack -> page)
    for a, title in include_edges:
        na = _sanitize_id(f"pack_{a}")
        nb = _sanitize_id(f"page_{title}")
        lines.append(f"  {na} -> {nb};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def graph(manifest: Path | str, fmt: str = 'dot', output: str | None = None) -> int:
    mpath = Path(manifest)
    try:
        manifest_data = load_yaml(mpath)
    except Exception as e:
        print(f"ERROR: Failed to read manifest for graph generation: {e}")
        return 1
    fmt = (fmt or 'dot').lower()
    if fmt != 'dot':
        print(f"ERROR: Unsupported graph format '{fmt}'. Supported: dot")
        return 1
    content = emit_dot(manifest_data)
    if not output or output == '-' or str(output).strip() == '':
        print(content, end='')
    else:
        out_path = Path(output)
        out_path.write_text(content, encoding='utf-8')
    return 0


def main():
    parser = argparse.ArgumentParser(description='Generate packs/pages graph from manifest')
    parser.add_argument('manifest', type=str)
    parser.add_argument('--format', dest='format', type=str, default='dot')
    parser.add_argument('--output', dest='output', type=str, default='-')
    args = parser.parse_args()
    rc = graph(args.manifest, fmt=args.format, output=args.output)
    raise SystemExit(rc)


if __name__ == '__main__':
    main()


