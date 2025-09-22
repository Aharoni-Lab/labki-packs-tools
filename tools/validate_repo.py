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


def check_root_manifest(manifest_path: Path, schema_path: Path) -> int:
    rc = 0
    try:
        manifest = load_yaml(manifest_path)
    except Exception as e:
        error(f"Failed to read root manifest {manifest_path}: {e}")
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

    def recurse(node_map):
        nonlocal rc
        if not isinstance(node_map, dict):
            error("packs must be a mapping")
            rc = 1
            return
        for key, node in node_map.items():
            pages_list = node.get('pages', [])
            if pages_list and not isinstance(pages_list, list):
                error(f"Node '{key}' pages must be an array")
                rc = 1
            for title in pages_list or []:
                if title not in pages:
                    error(f"Node '{key}' references unknown page title: {title}")
                    rc = 1
            children = node.get('children')
            if children is not None:
                recurse(children)

    recurse(manifest.get('packs', {}))
    return rc


TITLE_COMMENT_RE = re.compile(r"^\s*<!--\s*Title:\s*(.+?)\s*-->\s*$")


def derive_title_from_filename(filename: str):
    base = os.path.basename(filename)
    name, _sep, _ext = base.partition('.')
    for ns in ['Template_', 'Form_', 'Category_', 'Property_']:
        if name.startswith(ns):
            rest = name[len(ns):]
            rest = rest.replace('_', ' ')
            return f"{ns[:-1]}:{rest}"
    # default: just use filename without extension
    return name.replace('_', ' ')


def resolve_title(entry, file_path: Path):
    if isinstance(entry, dict):
        if 'title' in entry and entry['title']:
            return entry['title'], []
        if entry.get('namespace') and entry.get('name'):
            return f"{entry['namespace']}:{entry['name']}", []
    # Try file comment
    try:
        with file_path.open('r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            m = TITLE_COMMENT_RE.match(first_line)
            if m:
                return m.group(1), []
    except Exception:
        pass
    # Fallback to heuristic, warn
    return derive_title_from_filename(file_path.name), [f"Heuristic title used for {file_path}"]


def validate_packs(packs_root: Path, schema_path: Path) -> int:
    rc = 0
    schema = load_json(schema_path)

    pack_files = list(packs_root.rglob('pack.yml'))
    if not pack_files:
        warn(f"No pack.yml found under {packs_root}")

    for pack_file in pack_files:
        try:
            pack = load_yaml(pack_file)
        except Exception as e:
            error(f"Failed to read {pack_file}: {e}")
            rc = 1
            continue
        schema_errors = validate_with_schema(pack, schema)
        if schema_errors:
            for e in schema_errors:
                error(f"Schema {pack_file}: {e.message} at path {list(e.path)}")
            rc = 1
            continue
        pack_dir = pack_file.parent
        pages = pack.get('pages', [])
        for entry in pages:
            if isinstance(entry, str):
                rel = entry
            elif isinstance(entry, dict):
                rel = entry.get('file')
                if not rel:
                    error(f"{pack_file}: page object missing 'file'")
                    rc = 1
                    continue
            else:
                error(f"{pack_file}: invalid page entry type {type(entry)}")
                rc = 1
                continue

            if ':' in os.path.basename(rel):
                error(f"Filename must not contain colon: {rel} in {pack_file}")
                rc = 1
                continue
            if not rel.replace('\\', '/').startswith('pages/'):
                error(f"Page path must be under 'pages/': {rel} in {pack_file}")
                rc = 1
                continue

            abs_path = (pack_dir / rel).resolve()
            if not abs_path.exists():
                error(f"Referenced page not found: {rel} (in {pack_file})")
                rc = 1
                continue

            title, warnings = resolve_title(entry, abs_path)
            for w in warnings:
                warn(w)

            # Additional semantic checks
            if title.startswith('Property:'):
                content = abs_path.read_text(encoding='utf-8', errors='ignore')
                if '[[Has type::' not in content:
                    warn(f"Property page without explicit type: {abs_path}")

    return rc


def main():
    parser = argparse.ArgumentParser(description='Validate labki-packs repository')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_root = sub.add_parser('validate-root', help='Validate root manifest')
    p_root.add_argument('manifest', type=str)
    p_root.add_argument('schema', type=str)

    p_packs = sub.add_parser('validate-packs', help='Validate pack manifests and pages')
    p_packs.add_argument('packs_root', type=str)
    p_packs.add_argument('schema', type=str)

    args = parser.parse_args()

    if args.cmd == 'validate-root':
        sys.exit(check_root_manifest(Path(args.manifest), Path(args.schema)))
    if args.cmd == 'validate-packs':
        sys.exit(validate_packs(Path(args.packs_root), Path(args.schema)))


if __name__ == '__main__':
    main()
