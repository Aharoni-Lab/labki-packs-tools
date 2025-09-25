#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def load_yaml(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)


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
            error(f"Schema validation: {e.message} at path {list(e.path)}")
        rc = 1

    # v2: validate flat pages registry
    pages = manifest.get('pages', {})
    if not isinstance(pages, dict):
        error("'pages' must be a mapping of titles to objects")
        rc = 1
    else:
        for title, meta in pages.items():
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
            page_type = meta.get('type')
            if page_type == 'module':
                if not title.startswith('Module:'):
                    warn(f"Module type should use 'Module:' namespace: {title}")
                if not abs_path.suffix == '.lua':
                    warn(f"Module files should use .lua extension: {file_rel}")
                # recommend Modules directory
                if 'Modules' not in file_rel.replace('\\', '/'):
                    warn(f"Module files should be stored under pages/Modules/: {file_rel}")
            if page_type == 'help':
                if not title.startswith('Help:'):
                    warn(f"Help type should use 'Help:' namespace: {title}")
            if page_type == 'mediawiki':
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

    # v2 packs: flat registry with depends_on
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

    # no groups validation (feature removed)
    return rc


def main():
    parser = argparse.ArgumentParser(description='Validate labki-packs repository')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_root = sub.add_parser('validate', help='Validate manifest')
    p_root.add_argument('manifest', type=str)
    p_root.add_argument('schema', type=str, nargs='?', default='auto', help="Path to schema or 'auto' (default)")

    args = parser.parse_args()

    if args.cmd == 'validate':
        schema_arg = args.schema
        if schema_arg == 'auto':
            manifest_path = Path(args.manifest)
            try:
                manifest_data = load_yaml(manifest_path)
            except Exception as e:
                error(f"Failed to read manifest for auto schema selection: {e}")
                sys.exit(1)
            version_str = str(manifest_data.get('version', '')).strip()
            m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str or '')
            if not m:
                warn("Manifest 'version' missing or not semantic; using latest schema")
                schema_path = Path(__file__).resolve().parents[1] / 'schema' / 'manifest.schema.json'
            else:
                major = m.group(1)
                schema_dir = Path(__file__).resolve().parents[1] / 'schema'
                index_path = schema_dir / 'index.json'
                schema_path = None
                # Try index mapping first
                try:
                    index = load_json(index_path)
                    manifest_index = (index.get('manifest') or {})
                    versions_map = (manifest_index.get('versions') or {})
                    majors_map = (manifest_index.get('majors') or {})
                    if version_str in versions_map:
                        schema_path = schema_dir / versions_map[version_str]
                    elif major in majors_map:
                        schema_path = schema_dir / majors_map[major]
                except Exception:
                    # Ignore index issues; fall back to directory probing
                    pass
                # Fallback to schema/v{major}/manifest.schema.json then latest
                if schema_path is None:
                    candidate = schema_dir / f"v{major}" / 'manifest.schema.json'
                    schema_path = candidate if candidate.exists() else (schema_dir / 'manifest.schema.json')
            return_code = check_manifest(manifest_path, schema_path)
            sys.exit(return_code)
        else:
            sys.exit(check_manifest(Path(args.manifest), Path(schema_arg)))


if __name__ == '__main__':
    main()
