from collections import defaultdict, deque
from typing import Any

from labki_packs_tools.validation.result_types import ValidationItem
from labki_packs_tools.validation.validators.base import Validator


class PackCycleValidator(Validator):
    code = "pack-cycles"
    message = "Packs must not form dependency cycles"
    level = "error"

    def validate(self, *, packs: dict, **kwargs: Any) -> list[ValidationItem]:
        items = []
        if not packs:
            return items

        # Build graph
        indeg = defaultdict(int)
        graph = defaultdict(list)
        for pid in packs:
            indeg[pid] = 0
        for pack_id, meta in packs.items():
            for dep in meta.get("depends_on", []) or []:
                graph[dep].append(pack_id)
                indeg[pack_id] += 1

        # Kahn's algorithm
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
            items.append(
                ValidationItem(
                    level=self.level,
                    message="Dependency cycle detected among packs",
                    code=self.code,
                )
            )
        return items
