import os
from pathlib import Path
import subprocess
import sys
import textwrap

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / 'tools' / 'validate_repo.py'
SCHEMA = REPO_ROOT / 'schema' / 'manifest.schema.json'
FIXTURES = REPO_ROOT / 'tests' / 'fixtures' / 'basic_repo'


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def write_tmp(tmp_path: Path, rel: str, content: str):
    out = tmp_path / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding='utf-8')
    return out


def test_validate_ok_uses_fixtures_manifest():
    manifest = (FIXTURES / 'manifest.yml').resolve()
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc == 0, f"expected success, got rc={rc}, out={out}, err={err}"


def test_rejects_underscore_in_page_key(tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        pages:
          Template:Has_Underscore:
            file: pages/Templates/Template_Example.wiki
            version: 1.0.0
        packs:
          example:
            version: 1.0.0
            pages: [Template:Has_Underscore]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'must use spaces, not underscores' in out


def test_rejects_percent_encoding_in_page_key(tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        pages:
          Template:Has%20Encoding:
            file: pages/Templates/Template_Example.wiki
            version: 1.0.0
        packs:
          example:
            version: 1.0.0
            pages: [Template:Has%20Encoding]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'must not contain percent-encoding' in out


def test_allows_main_namespace_title_without_colon(tmp_path):
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 2.0.0
        pages:
          Person:
            file: pages/Templates/Template_Example.wiki
            version: 1.0.0
        packs:
          example:
            version: 1.0.0
            pages: [Person]
        '''
    ).strip() + "\n"
    write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc == 0


def test_validate_missing_page_file(tmp_path):
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
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'Page file not found' in out


def test_validate_dep_cycle(tmp_path):
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
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'Dependency cycle detected' in out


def test_validate_manifest_without_extra_sections_is_ok(tmp_path):
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
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc == 0


def test_validate_invalid_page_version(tmp_path):
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
    tmp_page = write_tmp(tmp_path, 'pages/Templates/Template_Example.wiki', '== Example ==\n')
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'must have semantic version' in out


def test_validate_valid_page_version_passes(tmp_path):
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
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc == 0, f"expected success, got rc={rc}, out={out}, err={err}"


def test_validate_duplicate_page_across_packs_fails(tmp_path):
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
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert "included in multiple packs" in out


def test_validate_warns_on_orphan_files(tmp_path):
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
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    # should still be success (warning only) and include warning text
    assert rc == 0
    assert 'Orphan page file not referenced in manifest:' in out


def test_validate_module_page_rules(tmp_path):
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
    manifest = write_tmp(tmp_path, 'manifest.yml', good_manifest)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
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
    manifest2 = write_tmp(tmp_path, 'manifest.yml', bad_manifest)
    rc2, out2, err2 = run([sys.executable, str(VALIDATOR), 'validate', str(manifest2), str(SCHEMA)])
    assert rc2 == 0


def test_validate_manifest_with_single_pack_valid(tmp_path):
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
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc == 0


def test_pack_with_two_dependencies_but_no_pages_is_valid(tmp_path):
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
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc == 0


def test_pack_with_single_dependency_and_no_pages_is_invalid(tmp_path):
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
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'must include at least one page or depend on at least two packs' in out


def test_pack_with_no_pages_and_no_dependencies_is_invalid(tmp_path):
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
    manifest = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run([sys.executable, str(VALIDATOR), 'validate', str(manifest), str(SCHEMA)])
    assert rc != 0
    assert 'must include at least one page or depend on at least two packs' in out


def test_schema_auto_uses_major_mapping(tmp_path):
    # version 1.2.3 should resolve via index majors → v1 schema
    manifest_yaml = textwrap.dedent(
        '''
        schema_version: 1.2.3
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
    # If major isn't mapped in index and version is valid semver, fall back to latest
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
    assert rc == 0


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
    schema_v1 = REPO_ROOT / 'schema' / 'v1' / 'manifest.schema.json'
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
