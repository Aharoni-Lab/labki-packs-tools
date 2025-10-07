from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
from collections import defaultdict, deque

from labki_packs_tools.utils import is_semver
from .result_types import ValidationResult


def validate_packs(pages: dict, packs: dict) -> tuple[ValidationResult, list[tuple[str, str]]]:
    """
    Validate packs mapping and return (ValidationResult, dependency_edges).

    Checks:
      • Each pack has a valid semantic version.
      • All referenced pages exist in the global pages registry.
      • Each page appears in at most one pack.
      • Dependencies reference existing packs.
    """
    result = ValidationResult()
    edges: list[tuple[str, str]] = []  # (dependency, pack_id)
    seen_page_to_pack: dict[str, str] = {}

    for pack_id, meta in packs.items():
        version = meta.get("version")
        if not is_semver(version):
            result.add_error(f"Pack '{pack_id}' must have semantic version (MAJOR.MINOR.PATCH)")

        pages_list = meta.get("pages", [])
        if pages_list and not isinstance(pages_list, list):
            result.add_error(f"Pack '{pack_id}' pages must be an array")

        # Validate page references
        for title in pages_list or []:
            if title not in pages:
                result.add_error(f"Pack '{pack_id}' references unknown page title: {title}")
            if title in seen_page_to_pack and seen_page_to_pack[title] != pack_id:
                other = seen_page_to_pack[title]
                result.add_error(
                    f"Page title '{title}' included in multiple packs ('{other}' and '{pack_id}'). "
                    "Move to a shared dependency pack."
                )
            else:
                seen_page_to_pack[title] = pack_id

        # Validate dependencies
        for dep in meta.get("depends_on", []) or []:
            if dep not in packs:
                result.add_error(f"Pack '{pack_id}' depends_on unknown pack id: {dep}")
            else:
                edges.append((dep, pack_id))

    return result, edges


def detect_cycles(packs: dict, edges: list[tuple[str, str]]) -> ValidationResult:
    """
    Detect dependency cycles among packs using Kahn's algorithm.
    Returns:
        ValidationResult (errors only)
    """
    result = ValidationResult()
    if not packs:
        return result

    indeg = defaultdict(int)
    graph = defaultdict(list)
    for pid in packs:
        indeg[pid] = 0
    for dep, pack in edges:
        graph[dep].append(pack)
        indeg[pack] += 1

    q = deque([pid for pid in packs if indeg[pid] == 0])
    visited = 0
    while q:
        current = q.popleft()
        visited += 1
        for neighbor in graph[current]:
            indeg[neighbor] -= 1
            if indeg[neighbor] == 0:
                q.append(neighbor)

    if visited != len(packs):
        result.add_error("Dependency cycle detected among packs")

    return result
