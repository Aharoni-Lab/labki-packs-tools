#!/usr/bin/env python3
import argparse
import os
import re
from pathlib import Path

from tools.utils import load_yaml, UniqueKeyLoader, sanitize_id, extract_graph
import yaml


# YAML loader is provided by tools.common (UniqueKeyLoader)


 


def emit_dot(manifest: dict) -> str:
    """Emit a Graphviz DOT graph of packs and pages."""
    pack_ids, page_titles, dep_edges, include_edges = extract_graph(manifest)
    lines: list[str] = []
    lines.append("digraph Manifest {")
    lines.append("  rankdir=LR;")
    lines.append("  graph [bgcolor=\"white\", ranksep=\"0.7\", nodesep=\"0.5\"];\n")
    lines.append("  node [fontname=\"Helvetica\", style=filled, color=\"#90A4AE\", fillcolor=\"#ECEFF1\"];\n")
    lines.append("  edge [fontname=\"Helvetica\", arrowsize=0.8];\n")
    # Clusters
    lines.append("  subgraph cluster_packs {")
    lines.append("    label=\"Packs\"; style=rounded; color=\"#5C6BC0\";")
    for pid in pack_ids:
        nid = sanitize_id(f"pack_{pid}")
        label = pid.replace('"', '\\"')
        lines.append(f"    {nid} [label=\"{label}\", shape=box, fillcolor=\"#E8F0FE\", color=\"#5C6BC0\"];")
    lines.append("  }")
    lines.append("  subgraph cluster_pages {")
    lines.append("    label=\"Pages\"; style=rounded; color=\"#43A047\";")
    for title in page_titles:
        nid = sanitize_id(f"page_{title}")
        label = title.replace('"', '\\"')
        lines.append(f"    {nid} [label=\"{label}\", shape=ellipse, fillcolor=\"#E8F5E9\", color=\"#43A047\"];")
    lines.append("  }\n")
    # Edges: depends_on (dep -> pack)
    for pack_id, dep in dep_edges:
        n_pack = sanitize_id(f"pack_{pack_id}")
        n_dep = sanitize_id(f"pack_{dep}")
        # draw from dependency into the dependent pack
        lines.append(f"  {n_dep} -> {n_pack} [color=\"#90A4AE\", style=dashed, penwidth=1.2, label=\"depends_on\", fontsize=10];")
    # Edges: includes (page -> pack)
    for pack_id, title in include_edges:
        n_pack = sanitize_id(f"pack_{pack_id}")
        n_page = sanitize_id(f"page_{title}")
        lines.append(f"  {n_page} -> {n_pack} [color=\"#64B5F6\", penwidth=1.4];")
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


