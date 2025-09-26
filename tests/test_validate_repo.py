import os
from pathlib import Path
import subprocess
import sys
import textwrap

import yaml
import uuid
import pytest
import io
import contextlib

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / 'tools' / 'validate_repo.py'
SCHEMA = REPO_ROOT / 'schema' / 'v1_0_0' / 'manifest.schema.json'
FIXTURES = REPO_ROOT / 'tests' / 'fixtures' / 'basic_repo'


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def write_tmp(tmp_path: Path, rel: str, content: str):
    out = tmp_path / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding='utf-8')
    return out


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


@pytest.fixture
def run_validate():
    # Prefer calling python function directly for speed and debuggability
    from tools.validate_repo import validate as py_validate
    def _run(manifest_path: Path, schema_path: Path = SCHEMA):
        # Capture printed output from validator
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            rc = py_validate(manifest_path, str(schema_path))
        out = stdout.getvalue()
        return rc, out, ""
    return _run

@pytest.fixture
def run_validate_cli():
    def _run(manifest_path: Path, schema_path: Path = SCHEMA):
        return run([sys.executable, str(VALIDATOR), 'validate', str(manifest_path), str(schema_path)])
    return _run

@pytest.fixture
def tmp_page_factory(tmp_path):
    def _make_page(namespace: str = 'Template', name: str | None = None, content: str = '== Page ==\n'):
        if name is None:
            name = uuid.uuid4().hex[:8]
        filename = f"{namespace}_{name}.wiki" if namespace else f"{name}.wiki"
        rel_dir = 'pages/Templates' if namespace == 'Template' else 'pages'
        rel_path = f"{rel_dir}/{filename}"
        write_tmp(tmp_path, rel_path, content)
        return {"file": rel_path, "version": "1.0.0"}
    return _make_page


@pytest.fixture
def manifest(tmp_path):
    def _build(overrides: dict | None = None) -> Path:
        base = {
            'schema_version': '2.0.0',
            'last_updated': '2025-09-22T00:00:00Z',
            'pages': {},
            'packs': {},
        }
        data = _deep_merge(base, overrides or {})
        # write YAML preserving order
        out = tmp_path / 'manifest.yml'
        out.write_text(yaml.safe_dump(data, sort_keys=False), encoding='utf-8')
        return out
    return _build


def test_validate_ok_uses_fixtures_manifest():
    manifest = (FIXTURES / 'manifest.yml').resolve()
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc == 0, f"expected success, got rc={rc}, out={out}, err={err}"


def test_rejects_underscore_in_page_key(manifest, tmp_page_factory, run_validate):
    page = tmp_page_factory()
    mpath = manifest({
        'pages': {
            'Template:Has_Underscore': page,
        },
        'packs': {
            'example': { 'version': '1.0.0', 'pages': ['Template:Has_Underscore'] }
        }
    })
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'must use spaces, not underscores' in out


def test_allows_main_namespace_title_without_colon(manifest, tmp_page_factory, run_validate):
    page = tmp_page_factory(namespace='')
    mpath = manifest({
        'pages': {
            'Person': page,
        },
        'packs': {
            'example': { 'version': '1.0.0', 'pages': ['Person'] }
        }
    })
    rc, out, err = run_validate(mpath)
    assert rc == 0


def test_validate_missing_page_file(manifest, run_validate, tmp_path):
    # Build a tiny manifest that references a non-existent file
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        last_updated: "2025-09-22T00:00:00Z"
        pages:
          Template:Example:
            file: pages/Templates/Template_Example.wiki
            version: 1.0.0
        packs:
          example:
            version: 1.0.0
            pages: [Template:Example]
            depends_on: []
        '''
    ).strip() + "\n"
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'Page file not found' in out


def test_validate_dep_cycle(manifest, run_validate, tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
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
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'Dependency cycle detected' in out


def test_validate_manifest_without_extra_sections_is_ok(manifest, run_validate, tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        pages: {}
        packs:
          a:
            version: 1.0.0
            pages: []
        '''
    ).strip() + "\n"
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath)
    assert rc == 0


def test_validate_invalid_page_version(manifest, run_validate, tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        pages:
          Template:Example:
            file: pages/Templates/Template_Example.wiki
            version: v1
        packs:
          example:
            version: 1.0.0
            pages: [Template:Example]
        '''
    ).strip() + "\n"
    # create the file so only version format triggers error
    tmp_page_path = write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'must have semantic version' in out


def test_validate_valid_page_version_passes(manifest, run_validate, tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        last_updated: "2025-09-22T00:00:00Z"
        pages:
          Template:Example:
            file: pages/Templates/Template_Example.wiki
            version: 2.3.4
        packs:
          example:
            version: 1.0.0
            pages: [Template:Example]
            depends_on: []
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath)
    assert rc == 0, f"expected success, got rc={rc}, out={out}, err={err}"


def test_validate_duplicate_page_across_packs_fails(manifest, run_validate, tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        last_updated: "2025-09-22T00:00:00Z"
        pages:
          Template:Shared:
            file: pages/Templates/Template_Shared.wiki
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
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert "included in multiple packs" in out


def test_validate_warns_on_orphan_files(manifest, run_validate, tmp_path):
    # manifest has no pages, but file exists under pages/ -> expect WARNING
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        last_updated: "2025-09-22T00:00:00Z"
        pages: {}
        packs: {}
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Orphan.wiki', '== Orphan ==\n')
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath)
    # should still be success (warning only) and include warning text
    assert rc == 0
    assert 'Orphan page file not referenced in manifest:' in out


def test_validate_module_page_rules(manifest, run_validate, tmp_path):
    # Proper module: Module:Name, .lua under pages/Modules/
    good_manifest = textwrap.dedent(
        '''
        schema_version: 2.0.0
        last_updated: "2025-09-22T00:00:00Z"
        pages:
          Module:Util:
            file: pages/Modules/Module_Util.lua
            version: 1.0.0
        packs:
          base:
            version: 1.0.0
            pages: [Module:Util]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Modules/Module_Util.lua', '-- lua module\n')
    mpath = write_tmp(tmp_path, 'manifest.yml', good_manifest)
    rc, out, err = run_validate(mpath)
    assert rc == 0

    # Module with mismatched namespace/extension/dir should warn, not fail
    bad_manifest = textwrap.dedent(
        '''
        schema_version: 2.0.0
        last_updated: "2025-09-22T00:00:00Z"
        pages:
          NotModule:Wrong:
            file: pages/Templates/Module_Wrong.txt
            version: 1.0.0
        packs:
          base:
            version: 1.0.0
            pages: [NotModule:Wrong]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Module_Wrong.txt', 'placeholder\n')
    mpath2 = write_tmp(tmp_path, 'manifest.yml', bad_manifest)
    rc2, out2, err2 = run_validate(mpath2)
    assert rc2 == 0


def test_validate_manifest_with_single_pack_valid(manifest, run_validate, tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        last_updated: "2025-09-22T00:00:00Z"
        pages:
          Template:Only:
            file: pages/Templates/Template_Only.wiki
            version: 1.0.0
        packs:
          one:
            version: 1.0.0
            pages: [Template:Only]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Only.wiki', '== Only ==\n')
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath)
    assert rc == 0


def test_pack_with_two_dependencies_but_no_pages_is_valid(manifest, run_validate, tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        pages:
          Template:A:
            file: pages/Templates/A.wiki
            version: 1.0.0
          Template:B:
            file: pages/Templates/B.wiki
            version: 1.0.0
        packs:
          depA:
            version: 1.0.0
            pages: [Template:A]
          depB:
            version: 1.0.0
            pages: [Template:B]
          meta:
            version: 1.0.0
            pages: []
            depends_on: [depA, depB]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/A.wiki', '== A ==\n')
    write_tmp(tmp_path, 'pages/Templates/B.wiki', '== B ==\n')
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath)
    assert rc == 0


def test_pack_with_single_dependency_and_no_pages_is_invalid(manifest, run_validate, tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        pages:
          Template:A:
            file: pages/Templates/A.wiki
            version: 1.0.0
        packs:
          depA:
            version: 1.0.0
            pages: [Template:A]
          meta:
            version: 1.0.0
            pages: []
            depends_on: [depA]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/A.wiki', '== A ==\n')
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'must include at least one page or depend on at least two packs' in out


def test_pack_with_no_pages_and_no_dependencies_is_invalid(manifest, run_validate, tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        pages: {}
        packs:
          meta:
            version: 1.0.0
            pages: []
            depends_on: []
        '''
    ).strip() + "\n"
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'must include at least one page or depend on at least two packs' in out


def test_schema_auto_requires_exact_version(tmp_path):
    # exact version present in index → should succeed
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 1.0.0
        pages:
          Template:Example:
            file: pages/Templates/Template_Example.wiki
            version: 1.0.0
        packs:
          example:
            version: 1.0.0
            pages: [Template:Example]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest)])
    assert rc == 0


def test_schema_auto_falls_back_when_major_unmapped(tmp_path):
    # With strict exact version requirement, unmapped version should fail
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 9.9.9
        last_updated: "2025-09-22T00:00:00Z"
        pages:
          Template:Example:
            file: pages/Templates/Template_Example.wiki
            version: 1.0.0
        packs:
          example:
            version: 1.0.0
            pages: [Template:Example]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest)])
    assert rc != 0
    assert "Schema version '9.9.9' not found in index" in out


def test_explicit_schema_override_path(tmp_path):
    # Explicit schema path should work regardless of manifest version
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 9.9.9
        last_updated: "2025-09-22T00:00:00Z"
        pages:
          Template:Example:
            file: pages/Templates/Template_Example.wiki
            version: 1.0.0
        packs:
          example:
            version: 1.0.0
            pages: [Template:Example]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    schema_v1 = REPO_ROOT / 'schema' / 'v1_0_0' / 'manifest.schema.json'
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(schema_v1)])
    assert rc == 0


def test_tags_accept_slugified_unique(tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        pages:
          Template:Example:
            file: pages/Templates/Template_Example.wiki
            version: 1.0.0
        packs:
          ok:
            version: 1.0.0
            pages: [Template:Example]
            tags: [core, data-tools]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc == 0


def test_tags_reject_uppercase(tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        pages:
          Template:Example:
            file: pages/Templates/Template_Example.wiki
            version: 1.0.0
        packs:
          bad:
            version: 1.0.0
            pages: [Template:Example]
            tags: [Core]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'does not match' in out or 'pattern' in out


def test_tags_reject_duplicates(tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        pages:
          Template:Example:
            file: pages/Templates/Template_Example.wiki
            version: 1.0.0
        packs:
          bad:
            version: 1.0.0
            pages: [Template:Example]
            tags: [core, core]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'non-unique elements' in out
