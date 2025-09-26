#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


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


def load_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def validate_with_schema(data, schema):
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    return errors


def error(msg):
    print(f"ERROR: {msg}")


def warn(msg):
    print(f"WARNING: {msg}")


def _format_schema_error(e) -> list[str]:
    """Return friendly, contextualized messages for common schema errors.

    Always preserve the raw jsonschema message elsewhere so tests and users
    can see the exact validator detail. This function only adds extra hints.
    """
    try:
        path_list = list(e.path)
    except Exception:
        path_list = []

    msgs: list[str] = []
    # Packs content rule handled elsewhere (anyOf)
    if e.validator == 'pattern':
        # Packs tags slug pattern
        if len(path_list) >= 4 and path_list[0] == 'packs' and path_list[2] == 'tags':
            pack_id = path_list[1]
            tag_value = getattr(e, 'instance', None)
            msgs.append(
                f"Schema validation: Pack '{pack_id}' has tag '{tag_value}' that must be slugified (lowercase letters, digits, hyphens)"
            )
        # Pack version pattern
        if len(path_list) >= 3 and path_list[0] == 'packs' and path_list[2] == 'version':
            pack_id = path_list[1]
            msgs.append(
                f"Schema validation: Pack '{pack_id}' must have semantic version (MAJOR.MINOR.PATCH)"
            )
        # Page version pattern
        if len(path_list) >= 3 and path_list[0] == 'pages' and path_list[2] == 'version':
            page_title = path_list[1]
            msgs.append(
                f"Schema validation: Page '{page_title}' must have semantic version (MAJOR.MINOR.PATCH)"
            )
        # last_updated timestamp pattern
        if path_list == ['last_updated']:
            msgs.append(
                "Schema validation: 'last_updated' must match YYYY-MM-DDThh:mm:ssZ"
            )
        # file path (no colon) — only if schema adds this pattern in future
        if len(path_list) >= 3 and path_list[0] == 'pages' and path_list[2] == 'file':
            page_title = path_list[1]
            msgs.append(
                f"Schema validation: Page '{page_title}' file path must not contain ':'"
            )

    if e.validator == 'uniqueItems':
        if len(path_list) >= 3 and path_list[0] == 'packs':
            pack_id = path_list[1]
            field = path_list[2]
            if field == 'tags':
                msgs.append(f"Schema validation: Pack '{pack_id}' has duplicate tags")
            if field == 'pages':
                msgs.append(f"Schema validation: Pack '{pack_id}' has duplicate page titles in 'pages'")

    if e.validator == 'additionalProperties':
        if len(path_list) >= 2 and path_list[0] == 'pages':
            page_title = path_list[1]
            msgs.append(f"Schema validation: Page '{page_title}' contains unknown field(s)")
        if len(path_list) >= 2 and path_list[0] == 'packs':
            pack_id = path_list[1]
            msgs.append(f"Schema validation: Pack '{pack_id}' contains unknown field(s)")

    if e.validator == 'type':
        # Pack pages must be an array
        if len(path_list) >= 3 and path_list[0] == 'packs' and path_list[2] == 'pages':
            pack_id = path_list[1]
            msgs.append(f"Schema validation: Pack '{pack_id}' pages must be an array")

    if e.validator == 'required':
        if len(path_list) >= 2 and path_list[0] == 'pages':
            page_title = path_list[1]
            msgs.append(f"Schema validation: Page '{page_title}' is missing required field(s)")
        if len(path_list) >= 2 and path_list[0] == 'packs':
            pack_id = path_list[1]
            msgs.append(f"Schema validation: Pack '{pack_id}' is missing required field(s)")

    return msgs


def check_manifest(manifest_path: Path, schema_path: Path) -> int:
    rc = 0
    try:
        manifest = load_yaml(manifest_path)
    except Exception as e:
        error(f"Failed to read manifest {manifest_path}: {e}")
        return 1

    try:
        schema = load_json(schema_path)
    except Exception as e:
        error(f"Failed to read schema {schema_path}: {e}")
        return 1

    schema_errors = validate_with_schema(manifest, schema)
    if schema_errors:
        for e in schema_errors:
            # Provide clearer message for anyOf failures on packs content rule
            if e.validator == 'anyOf':
                path_list = list(e.path)
                if len(path_list) >= 2 and path_list[0] == 'packs':
                    pack_id = path_list[1]
                    error(
                        f"Schema validation: Pack '{pack_id}' must include at least one page or depend on at least two packs"
                    )
                    # fall through to also print raw message for completeness
            # Extra friendly hints
            for msg in _format_schema_error(e):
                error(msg)
            # Always include the raw jsonschema message
            error(f"Schema validation: {e.message} at path {list(e.path)}")
        rc = 1

    # v1: validate flat pages registry
    pages = manifest.get('pages', {})
    if not isinstance(pages, dict):
        error("'pages' must be a mapping of titles to objects")
        rc = 1
    else:
        for title, meta in pages.items():
            # Enforce canonical title key format: spaces not underscores
            if '_' in title:
                error(f"Page title must use spaces, not underscores: {title}")
                rc = 1
            if ':' not in title:
                warn(f"Title missing namespace: {title}")
            file_rel = meta.get('file')
            if not file_rel:
                error(f"Page '{title}' missing file path")
                rc = 1
                continue
            if ':' in os.path.basename(file_rel):
                error(f"Filename must not contain colon: {file_rel} (for {title})")
                rc = 1
            abs_path = (manifest_path.parent / file_rel).resolve()
            if not abs_path.exists():
                error(f"Page file not found: {file_rel} (for {title})")
                rc = 1
            page_version = meta.get('version')
            if not isinstance(page_version, str) or not re.match(r"^\d+\.\d+\.\d+$", page_version or ""):
                error(f"Page '{title}' must have semantic version (MAJOR.MINOR.PATCH)")
                rc = 1
            # Additional type-specific checks
            # Infer namespace from title key, e.g., 'Module:Name'
            inferred_ns = None
            if ':' in title:
                inferred_ns = title.split(':', 1)[0]
            if inferred_ns == 'Module':
                if not title.startswith('Module:'):
                    warn(f"Module type should use 'Module:' namespace: {title}")
                if not abs_path.suffix == '.lua':
                    warn(f"Module files should use .lua extension: {file_rel}")
                # recommend Modules directory
                if 'Modules' not in file_rel.replace('\\', '/'):
                    warn(f"Module files should be stored under pages/Modules/: {file_rel}")
            if inferred_ns == 'Help':
                if not title.startswith('Help:'):
                    warn(f"Help type should use 'Help:' namespace: {title}")
            if inferred_ns == 'MediaWiki':
                if not title.startswith('MediaWiki:'):
                    warn(f"MediaWiki type should use 'MediaWiki:' namespace: {title}")

        # Orphan file detection: find files under pages/ not referenced in manifest
        referenced_abs_paths = set()
        for meta in pages.values():
            file_rel = meta.get('file')
            if file_rel:
                referenced_abs_paths.add((manifest_path.parent / file_rel).resolve())
        pages_dir = (manifest_path.parent / 'pages').resolve()
        if pages_dir.exists():
            for root, _dirs, files in os.walk(pages_dir):
                for fname in files:
                    if not (fname.endswith('.wiki') or fname.endswith('.md')):
                        continue
                    f_abs = Path(root) / fname
                    if f_abs not in referenced_abs_paths:
                        rel = os.path.relpath(f_abs, manifest_path.parent)
                        warn(f"Orphan page file not referenced in manifest: {rel}")

    # v1 packs: flat registry with depends_on
    packs = manifest.get('packs', {})
    if not isinstance(packs, dict):
        error("'packs' must be a mapping of pack_id to metadata")
        rc = 1
        packs = {}
    # basic validation and edges
    edges = []
    seen_page_to_pack = {}
    for pack_id, meta in packs.items():
        version = meta.get('version')
        if not isinstance(version, str) or not re.match(r"^\d+\.\d+\.\d+$", version):
            error(f"Pack '{pack_id}' must have semantic version (MAJOR.MINOR.PATCH)")
            rc = 1
        pages_list = meta.get('pages', [])
        if pages_list and not isinstance(pages_list, list):
            error(f"Pack '{pack_id}' pages must be an array")
            rc = 1
        for title in pages_list or []:
            if title not in pages:
                error(f"Pack '{pack_id}' references unknown page title: {title}")
                rc = 1
            # detect duplicate page in multiple packs
            if title in seen_page_to_pack and seen_page_to_pack[title] != pack_id:
                other = seen_page_to_pack[title]
                error(f"Page title '{title}' included in multiple packs ('{other}' and '{pack_id}'). Move to a shared dependency pack.")
                rc = 1
            else:
                seen_page_to_pack[title] = pack_id
        for dep in meta.get('depends_on', []) or []:
            if dep not in packs:
                error(f"Pack '{pack_id}' depends_on unknown pack id: {dep}")
                rc = 1
            else:
                edges.append((dep, pack_id))  # dep -> pack_id

    # cycle detection (Kahn's algorithm)
    if packs:
        from collections import defaultdict, deque
        indeg = defaultdict(int)
        graph = defaultdict(list)
        for a, b in edges:
            graph[a].append(b)
            indeg[b] += 1
            if a not in indeg:
                indeg[a] = indeg[a]  # ensure key exists
        q = deque([n for n in packs.keys() if indeg[n] == 0])
        visited = 0
        while q:
            n = q.popleft()
            visited += 1
            for m in graph[n]:
                indeg[m] -= 1
                if indeg[m] == 0:
                    q.append(m)
        if visited != len(packs):
            error("Dependency cycle detected among packs")
            rc = 1

    return rc


def validate(manifest: Path | str, schema_arg: Path | str = 'auto') -> int:
    manifest_path = Path(manifest)
    if schema_arg == 'auto':
        try:
            manifest_data = load_yaml(manifest_path)
        except Exception as e:
            error(f"Failed to read manifest for auto schema selection: {e}")
            return 1
        # Allow explicit schema override via $schema in the manifest
        explicit_schema = manifest_data.get('$schema')
        if isinstance(explicit_schema, str) and explicit_schema.strip():
            schema_path = Path(explicit_schema)
            if not schema_path.is_absolute():
                schema_path = (manifest_path.parent / schema_path).resolve()
            return check_manifest(manifest_path, schema_path)

        version_str = str(manifest_data.get('schema_version') or '').strip()
        m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str or '')
        schema_dir = Path(__file__).resolve().parents[1] / 'schema'
        if not m:
            error("Manifest 'schema_version' must be a semantic version (MAJOR.MINOR.PATCH)")
            return 1
        index_path = schema_dir / 'index.json'
        schema_path = None
        # Require exact mapping in index
        try:
            index = load_json(index_path)
            manifest_map = (index.get('manifest') or {})
            if version_str not in manifest_map:
                error(f"Schema version '{version_str}' not found in index. Available: {', '.join(sorted([k for k in manifest_map.keys() if k != 'latest']))}")
                return 1
            rel = manifest_map[version_str]
            schema_path = schema_dir / rel
        except Exception as e:
            error(f"Failed to read schema index: {e}")
            return 1
        if not schema_path.exists():
            error(f"Resolved schema path does not exist: {schema_path}")
            return 1
        return check_manifest(manifest_path, schema_path)
    else:
        schema_path = Path(schema_arg)
        return check_manifest(manifest_path, schema_path)


def main():
    parser = argparse.ArgumentParser(description='Validate labki-packs repository')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_root = sub.add_parser('validate', help='Validate manifest')
    p_root.add_argument('manifest', type=str)
    p_root.add_argument('schema', type=str, nargs='?', default='auto', help="Path to schema or 'auto' (default)")


    args = parser.parse_args()

    if args.cmd == 'validate':
        rc = validate(args.manifest, args.schema)
        sys.exit(rc)


if __name__ == '__main__':
    main()
