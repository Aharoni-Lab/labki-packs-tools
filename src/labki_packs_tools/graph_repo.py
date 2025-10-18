import json
from datetime import datetime, timezone
from pathlib import Path

from labki_packs_tools.utils import (
    categorize_packs,
    extract_graph,
    load_yaml,
    sanitize_id,
)


def emit_dot(manifest: dict) -> str:
    """Emit a Graphviz DOT graph of packs and pages."""
    pack_ids, page_titles, dep_edges, include_edges = extract_graph(manifest)
    lines: list[str] = []
    lines.append("digraph Manifest {")
    lines.append("  rankdir=LR;")
    lines.append('  graph [bgcolor="white", ranksep="0.7", nodesep="0.5"];\n')
    lines.append(
        '  node [fontname="Helvetica", style=filled, color="#90A4AE", fillcolor="#ECEFF1"];\n'
    )
    lines.append('  edge [fontname="Helvetica", arrowsize=0.8];\n')
    # Clusters
    lines.append("  subgraph cluster_packs {")
    lines.append('    label="Packs"; style=rounded; color="#5C6BC0";')
    pack_styles = {
        "content": ("#E8F0FE", "#5C6BC0"),
        "aggregator": ("#FFF3E0", "#FB8C00"),
        "meta": ("#F3E5F5", "#AB47BC"),
        "other": ("#ECEFF1", "#90A4AE"),
    }
    pack_kinds = categorize_packs(manifest)
    for pid in pack_ids:
        nid = sanitize_id(f"pack_{pid}")
        label = pid.replace('"', '\\"')
        kind = pack_kinds.get(pid, "other")
        fill, border = pack_styles.get(kind, pack_styles["other"])
        lines.append(
            f'    {nid} [label="{label}", shape=box, fillcolor="{fill}", color="{border}"];'
        )
    lines.append("  }")
    lines.append("  subgraph cluster_pages {")
    lines.append('    label="Pages"; style=rounded; color="#43A047";')
    for title in page_titles:
        nid = sanitize_id(f"page_{title}")
        label = title.replace('"', '\\"')
        # Color pages by namespace for better visual grouping
        ns = title.split(":", 1)[0] if ":" in title else "Main"
        ns_styles = {
            "Template": ("#E3F2FD", "#42A5F5"),
            "Form": ("#E8F5E9", "#43A047"),
            "Category": ("#F3E5F5", "#AB47BC"),
            "Property": ("#F1F8E9", "#7CB342"),
            "Module": ("#EDE7F6", "#7E57C2"),
            "Help": ("#FFFDE7", "#FBC02D"),
            "MediaWiki": ("#ECEFF1", "#607D8B"),
            "Main": ("#F5F5F5", "#9E9E9E"),
        }
        fill, border = ns_styles.get(ns, ("#F5F5F5", "#9E9E9E"))
        lines.append(
            f'    {nid} [label="{label}", shape=ellipse, fillcolor="{fill}", color="{border}"];'
        )
    lines.append("  }\n")
    # Edges: depends_on (dep -> pack)
    for pack_id, dep in dep_edges:
        n_pack = sanitize_id(f"pack_{pack_id}")
        n_dep = sanitize_id(f"pack_{dep}")
        # draw from dependency into the dependent pack
        lines.append(
            f"  {n_dep} -> {n_pack} "
            '[color="#90A4AE", style=dashed, penwidth=1.2, label="depends_on", fontsize=10];'
        )
    # Edges: includes (page -> pack)
    for pack_id, title in include_edges:
        n_pack = sanitize_id(f"pack_{pack_id}")
        n_page = sanitize_id(f"page_{title}")
        lines.append(f'  {n_page} -> {n_pack} [color="#64B5F6", penwidth=1.4];')
    lines.append("}")
    return "\n".join(lines) + "\n"


def emit_mermaid(manifest: dict) -> str:
    """Emit a Mermaid graph (for docs/readmes)."""
    pack_ids, page_titles, dep_edges, include_edges = extract_graph(manifest)
    lines: list[str] = []
    lines.append("graph LR")
    # Node style classes
    # Packs
    lines.append("  classDef pack_content fill:#E8F0FE,stroke:#5C6BC0,stroke-width:1px;")
    lines.append("  classDef pack_aggregator fill:#FFF3E0,stroke:#FB8C00,stroke-width:1px;")
    lines.append("  classDef pack_meta fill:#F3E5F5,stroke:#AB47BC,stroke-width:1px;")
    lines.append("  classDef pack_other fill:#ECEFF1,stroke:#90A4AE,stroke-width:1px;")
    # Pages by namespace
    lines.append("  classDef ns_Template fill:#E3F2FD,stroke:#42A5F5,stroke-width:1px;")
    lines.append("  classDef ns_Form fill:#E8F5E9,stroke:#43A047,stroke-width:1px;")
    lines.append("  classDef ns_Category fill:#F3E5F5,stroke:#AB47BC,stroke-width:1px;")
    lines.append("  classDef ns_Property fill:#F1F8E9,stroke:#7CB342,stroke-width:1px;")
    lines.append("  classDef ns_Module fill:#EDE7F6,stroke:#7E57C2,stroke-width:1px;")
    lines.append("  classDef ns_Help fill:#FFFDE7,stroke:#FBC02D,stroke-width:1px;")
    lines.append("  classDef ns_MediaWiki fill:#ECEFF1,stroke:#607D8B,stroke-width:1px;")
    lines.append("  classDef ns_Main fill:#F5F5F5,stroke:#9E9E9E,stroke-width:1px;")
    # Nodes
    pack_kinds = categorize_packs(manifest)
    for pid in pack_ids:
        nid = sanitize_id(f"pack_{pid}")
        label = pid.replace('"', '\\"')
        kind = pack_kinds.get(pid, "other")
        lines.append(f"  {nid}[{label}]")
        lines.append(f"  class {nid} pack_{kind}")
    for title in page_titles:
        nid = sanitize_id(f"page_{title}")
        label = title.replace('"', '\\"')
        ns = title.split(":", 1)[0] if ":" in title else "Main"
        ns_class = f"ns_{ns}"
        lines.append(f"  {nid}(({label}))")
        lines.append(f"  class {nid} {ns_class}")
    # Edges (depends_on: dep --> pack)
    edge_styles: list[tuple[int, str]] = []
    edge_index = 0
    for pack_id, dep in dep_edges:
        n_pack = sanitize_id(f"pack_{pack_id}")
        n_dep = sanitize_id(f"pack_{dep}")
        lines.append(f"  {n_dep} --> {n_pack}")
        edge_styles.append((edge_index, "depends_on"))
        edge_index += 1
    # Edges (includes: page --> pack)
    for pack_id, title in include_edges:
        n_pack = sanitize_id(f"pack_{pack_id}")
        n_page = sanitize_id(f"page_{title}")
        lines.append(f"  {n_page} --> {n_pack}")
        edge_styles.append((edge_index, "includes"))
        edge_index += 1
    # Apply link styles by index
    for idx, etype in edge_styles:
        if etype == "depends_on":
            lines.append(
                f"  linkStyle {idx} stroke:#90A4AE,stroke-width:1.2px,stroke-dasharray:3 3;"
            )
        elif etype == "includes":
            lines.append(f"  linkStyle {idx} stroke:#64B5F6,stroke-width:1.4px;")
    return "\n".join(lines) + "\n"


def emit_json(manifest: dict) -> str:
    """Emit a JSON graph for programmatic consumption (e.g., MediaWiki extension)."""
    pack_ids, page_titles, dep_edges, include_edges = extract_graph(manifest)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    nodes = []
    pack_styles = {
        "content": ("#E8F0FE", "#5C6BC0"),
        "aggregator": ("#FFF3E0", "#FB8C00"),
        "meta": ("#F3E5F5", "#AB47BC"),
        "other": ("#ECEFF1", "#90A4AE"),
    }
    ns_styles = {
        "Template": ("#E3F2FD", "#42A5F5"),
        "Form": ("#E8F5E9", "#43A047"),
        "Category": ("#F3E5F5", "#AB47BC"),
        "Property": ("#F1F8E9", "#7CB342"),
        "Module": ("#EDE7F6", "#7E57C2"),
        "Help": ("#FFFDE7", "#FBC02D"),
        "MediaWiki": ("#ECEFF1", "#607D8B"),
        "Main": ("#F5F5F5", "#9E9E9E"),
    }
    pack_kinds = categorize_packs(manifest)
    for pid in pack_ids:
        fill, border = pack_styles.get(pack_kinds.get(pid, "other"), pack_styles["other"])
        nodes.append(
            {
                "id": f"pack:{pid}",
                "type": "pack",
                "label": pid,
                "style": {"fill": fill, "stroke": border},
            }
        )
    for title in page_titles:
        ns = title.split(":", 1)[0] if ":" in title else "Main"
        fill, border = ns_styles.get(ns, ns_styles["Main"])
        nodes.append(
            {
                "id": f"page:{title}",
                "type": "page",
                "label": title,
                "namespace": ns,
                "style": {"fill": fill, "stroke": border},
            }
        )
    edges = []
    for pack_id, dep in dep_edges:
        edges.append(
            {
                "from": f"pack:{dep}",
                "to": f"pack:{pack_id}",
                "type": "depends_on",
                "style": {"color": "#90A4AE", "dashed": True, "width": 1.2},
            }
        )
    for pack_id, title in include_edges:
        edges.append(
            {
                "from": f"page:{title}",
                "to": f"pack:{pack_id}",
                "type": "includes",
                "style": {"color": "#64B5F6", "dashed": False, "width": 1.4},
            }
        )
    payload = {"nodes": nodes, "edges": edges, "meta": {"generated_at": now}}
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def graph(manifest: Path | str, fmt: str = "dot", output: str | None = None) -> int:
    mpath = Path(manifest)
    try:
        manifest_data = load_yaml(mpath)
    except Exception as e:
        print(f"ERROR: Failed to read manifest for graph generation: {e}")
        return 1
    fmt = (fmt or "dot").lower()
    if fmt == "dot":
        content = emit_dot(manifest_data)
    elif fmt == "mermaid":
        content = emit_mermaid(manifest_data)
    elif fmt == "json":
        content = emit_json(manifest_data)
    else:
        print(f"ERROR: Unsupported graph format '{fmt}'. Supported: dot, mermaid, json")
        return 1
    if not output or output == "-" or str(output).strip() == "":
        print(content, end="")
    else:
        out_path = Path(output)
        out_path.write_text(content, encoding="utf-8")
    return 0
