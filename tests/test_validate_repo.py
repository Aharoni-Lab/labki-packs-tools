import os
from pathlib import Path
import subprocess
import sys
import textwrap

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / 'tools' / 'validate_repo.py'
SCHEMA = REPO_ROOT / 'schema' / 'root-manifest.schema.json'


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def write_tmp(tmp_path: Path, rel: str, content: str):
    out = tmp_path / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding='utf-8')
    return out


def test_validate_root_ok_uses_examples_manifest():
    manifest = (REPO_ROOT / 'examples' / 'manifest.yml').resolve()
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate-root', str(manifest), str(SCHEMA)])
    assert rc == 0, f"expected success, got rc={rc}, out={out}, err={err}"


def test_validate_root_missing_page_file(tmp_path):
    # Build a tiny manifest that references a non-existent file
    manifest_yaml = textwrap.dedent(
        '''
        version: 2.0.0
        last_updated: "2025-09-22"
        pages:
          Template:Example:
            file: pages/Templates/Template_Example.wiki
            type: template
            version: 1.0.0
        packs:
          example:
            version: 1.0.0
            pages: [Template:Example]
            depends_on: []
        '''
    ).strip() + "\n"
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate-root', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'Page file not found' in out


def test_validate_root_dep_cycle(tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        version: 2.0.0
        pages: {}
        packs:
          a:
            version: 1.0.0
            pages: []
            depends_on: [b]
          b:
            version: 1.0.0
            pages: []
            depends_on: [a]
        '''
    ).strip() + "\n"
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate-root', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'Dependency cycle detected' in out


def test_validate_root_bad_group_reference(tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        version: 2.0.0
        pages: {}
        packs:
          a:
            version: 1.0.0
            pages: []
        groups:
          ops:
            packs: [does_not_exist]
        '''
    ).strip() + "\n"
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate-root', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'references unknown pack id' in out


def test_validate_root_invalid_page_version(tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        version: 2.0.0
        pages:
          Template:Example:
            file: pages/Templates/Template_Example.wiki
            type: template
            version: v1
        packs:
          example:
            version: 1.0.0
            pages: [Template:Example]
        '''
    ).strip() + "\n"
    # create the file so only version format triggers error
    tmp_page = write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate-root', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'must have semantic version' in out


def test_validate_root_valid_page_version_passes(tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        version: 2.0.0
        pages:
          Template:Example:
            file: pages/Templates/Template_Example.wiki
            type: template
            version: 2.3.4
        packs:
          example:
            version: 1.0.0
            pages: [Template:Example]
            depends_on: []
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate-root', str(manifest), str(SCHEMA)])
    assert rc == 0, f"expected success, got rc={rc}, out={out}, err={err}"


def test_validate_root_duplicate_page_across_packs_fails(tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        version: 2.0.0
        pages:
          Template:Shared:
            file: pages/Templates/Template_Shared.wiki
            type: template
            version: 1.0.0
        packs:
          a:
            version: 1.0.0
            pages: [Template:Shared]
          b:
            version: 1.0.0
            pages: [Template:Shared]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Shared.wiki', '== Shared ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate-root', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert "included in multiple packs" in out


def test_validate_root_warns_on_orphan_files(tmp_path):
    # manifest has no pages, but file exists under pages/ -> expect WARNING
    manifest_yaml = textwrap.dedent(
        '''
        version: 2.0.0
        pages: {}
        packs: {}
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Orphan.wiki', '== Orphan ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate-root', str(manifest), str(SCHEMA)])
    # should still be success (warning only) and include warning text
    assert rc == 0
    assert 'Orphan page file not referenced in manifest:' in out
