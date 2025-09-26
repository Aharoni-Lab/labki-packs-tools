#!/usr/bin/env python3
import argparse
import os
import re
from pathlib import Path
import json
from datetime import datetime, timezone

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
        # Color pages by namespace for better visual grouping
        if ':' in title:
            ns = title.split(':', 1)[0]
        else:
            ns = 'Main'
        ns_styles = {
            'Template': ("#E3F2FD", "#42A5F5"),
            'Form': ("#E8F5E9", "#43A047"),
            'Category': ("#F3E5F5", "#AB47BC"),
            'Property': ("#F1F8E9", "#7CB342"),
            'Module': ("#EDE7F6", "#7E57C2"),
            'Help': ("#FFFDE7", "#FBC02D"),
            'MediaWiki': ("#ECEFF1", "#607D8B"),
            'Main': ("#F5F5F5", "#9E9E9E"),
        }
        fill, border = ns_styles.get(ns, ("#F5F5F5", "#9E9E9E"))
        lines.append(f"    {nid} [label=\"{label}\", shape=ellipse, fillcolor=\"{fill}\", color=\"{border}\"];")
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


def emit_mermaid(manifest: dict) -> str:
    """Emit a Mermaid graph (for docs/readmes)."""
    pack_ids, page_titles, dep_edges, include_edges = extract_graph(manifest)
    lines: list[str] = []
    lines.append("graph LR")
    # Node style classes
    lines.append("  classDef pack fill:#E8F0FE,stroke:#5C6BC0,stroke-width:1px;")
    lines.append("  classDef page fill:#F5F5F5,stroke:#9E9E9E,stroke-width:1px;")
    # Nodes
    for pid in pack_ids:
        nid = sanitize_id(f"pack_{pid}")
        label = pid.replace('"', '\\"')
        lines.append(f"  {nid}[{label}]:::pack")
    for title in page_titles:
        nid = sanitize_id(f"page_{title}")
        label = title.replace('"', '\\"')
        lines.append(f"  {nid}(({label})):::page")
    # Edges (depends_on: dep --> pack)
    for pack_id, dep in dep_edges:
        n_pack = sanitize_id(f"pack_{pack_id}")
        n_dep = sanitize_id(f"pack_{dep}")
        lines.append(f"  {n_dep} --> {n_pack}")
    # Edges (includes: page --> pack)
    for pack_id, title in include_edges:
        n_pack = sanitize_id(f"pack_{pack_id}")
        n_page = sanitize_id(f"page_{title}")
        lines.append(f"  {n_page} --> {n_pack}")
    return "\n".join(lines) + "\n"


def emit_json(manifest: dict) -> str:
    """Emit a JSON graph for programmatic consumption (e.g., MediaWiki extension)."""
    pack_ids, page_titles, dep_edges, include_edges = extract_graph(manifest)
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    nodes = []
    for pid in pack_ids:
        nodes.append({
            "id": f"pack:{pid}",
            "type": "pack",
            "label": pid,
        })
    for title in page_titles:
        ns = title.split(':', 1)[0] if ':' in title else 'Main'
        nodes.append({
            "id": f"page:{title}",
            "type": "page",
            "label": title,
            "namespace": ns,
        })
    edges = []
    for pack_id, dep in dep_edges:
        edges.append({
            "from": f"pack:{dep}",
            "to": f"pack:{pack_id}",
            "type": "depends_on",
        })
    for pack_id, title in include_edges:
        edges.append({
            "from": f"page:{title}",
            "to": f"pack:{pack_id}",
            "type": "includes",
        })
    payload = {"nodes": nodes, "edges": edges, "meta": {"generated_at": now}}
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def graph(manifest: Path | str, fmt: str = 'dot', output: str | None = None) -> int:
    mpath = Path(manifest)
    try:
        manifest_data = load_yaml(mpath)
    except Exception as e:
        print(f"ERROR: Failed to read manifest for graph generation: {e}")
        return 1
    fmt = (fmt or 'dot').lower()
    if fmt == 'dot':
        content = emit_dot(manifest_data)
    elif fmt == 'mermaid':
        content = emit_mermaid(manifest_data)
    elif fmt == 'json':
        content = emit_json(manifest_data)
    else:
        print(f"ERROR: Unsupported graph format '{fmt}'. Supported: dot, mermaid, json")
        return 1
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


