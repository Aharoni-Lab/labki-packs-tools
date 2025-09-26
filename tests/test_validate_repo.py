import os
from pathlib import Path
import subprocess
import sys

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


# ---- Basic validation (fixtures manifest) ----
def test_validate_ok_uses_fixtures_manifest(run_validate):
    manifest = (FIXTURES / 'manifest.yml').resolve()
    rc, out, err = run_validate(manifest, SCHEMA)
    assert rc == 0, f"expected success, got rc={rc}, out={out}, err={err}"


# ---- Page rules ----
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
    mpath = manifest({
        'pages': {
            'Template:Example': {
                'file': 'pages/Templates/Template_Example.wiki',
                'version': '1.0.0',
            }
        },
        'packs': {
            'example': {
                'version': '1.0.0',
                'pages': ['Template:Example'],
                'depends_on': [],
            }
        }
    })
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'Page file not found' in out


# ---- Pack / dependency rules ----
def test_validate_dep_cycle(manifest, run_validate, tmp_path):
    mpath = manifest({
        'pages': {},
        'packs': {
            'a': {'version': '1.0.0', 'pages': [], 'depends_on': ['b']},
            'b': {'version': '1.0.0', 'pages': [], 'depends_on': ['a']},
        }
    })
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'Dependency cycle detected' in out


def test_validate_manifest_without_extra_sections_is_ok(manifest, run_validate, tmp_path):
    mpath = manifest({
        'pages': {},
        'packs': {
            'a': {'version': '1.0.0', 'pages': []}
        }
    })
    rc, out, err = run_validate(mpath)
    assert rc == 0


def test_validate_invalid_page_version(manifest, run_validate, tmp_path, tmp_page_factory):
    # create the file so only version format triggers error
    page = tmp_page_factory(name='Example')
    page['version'] = 'v1'
    mpath = manifest({
        'pages': {
            'Template:Example': page
        },
        'packs': {
            'example': {'version': '1.0.0', 'pages': ['Template:Example']}
        }
    })
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'must have semantic version' in out


def test_validate_valid_page_version_passes(manifest, run_validate, tmp_path, tmp_page_factory):
    page = tmp_page_factory(name='Example')
    page['version'] = '2.3.4'
    mpath = manifest({
        'pages': {'Template:Example': page},
        'packs': {'example': {'version': '1.0.0', 'pages': ['Template:Example'], 'depends_on': []}},
    })
    rc, out, err = run_validate(mpath)
    assert rc == 0, f"expected success, got rc={rc}, out={out}, err={err}"


def test_validate_duplicate_page_across_packs_fails(manifest, run_validate, tmp_path, tmp_page_factory):
    page = tmp_page_factory(name='Shared')
    mpath = manifest({
        'pages': {'Template:Shared': page},
        'packs': {
            'a': {'version': '1.0.0', 'pages': ['Template:Shared']},
            'b': {'version': '1.0.0', 'pages': ['Template:Shared']},
        },
    })
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert "included in multiple packs" in out


def test_validate_warns_on_orphan_files(manifest, run_validate, tmp_path):
    # manifest has no pages, but file exists under pages/ -> expect WARNING
    write_tmp(tmp_path, 'pages/Templates/Template_Orphan.wiki', '== Orphan ==\n')
    mpath = manifest({'pages': {}, 'packs': {}})
    rc, out, err = run_validate(mpath)
    # should still be success (warning only) and include warning text
    assert rc == 0
    assert 'Orphan page file not referenced in manifest:' in out


# ---- Module page rules ----
def test_validate_module_page_rules(manifest, run_validate, tmp_path):
    # Proper module: Module:Name, .lua under pages/Modules/
    good_manifest = {
        'pages': {
            'Module:Util': {'file': 'pages/Modules/Module_Util.lua', 'version': '1.0.0'}
        },
        'packs': {'base': {'version': '1.0.0', 'pages': ['Module:Util']}},
    }
    write_tmp(tmp_path, 'pages/Modules/Module_Util.lua', '-- lua module\n')
    mpath = manifest(good_manifest)
    rc, out, err = run_validate(mpath)
    assert rc == 0

    # Module with mismatched namespace/extension/dir should warn, not fail
    bad_manifest = {
        'pages': {
            'NotModule:Wrong': {'file': 'pages/Templates/Module_Wrong.txt', 'version': '1.0.0'}
        },
        'packs': {'base': {'version': '1.0.0', 'pages': ['NotModule:Wrong']}},
    }
    write_tmp(tmp_path, 'pages/Templates/Module_Wrong.txt', 'placeholder\n')
    mpath2 = manifest(bad_manifest)
    rc2, out2, err2 = run_validate(mpath2)
    assert rc2 == 0


# ---- Pack composition matrix ----
@pytest.mark.parametrize(
    "case_id, packs_builder, expect_ok",
    [
        (
            "pages_present",
            lambda pages: {
                'one': {'version': '1.0.0', 'pages': ['Template:A']},
            },
            True,
        ),
        (
            "two_deps",
            lambda pages: {
                'depA': {'version': '1.0.0', 'pages': ['Template:A']},
                'depB': {'version': '1.0.0', 'pages': ['Template:B']},
                'meta': {'version': '1.0.0', 'pages': [], 'depends_on': ['depA', 'depB']},
            },
            True,
        ),
        (
            "one_dep_only",
            lambda pages: {
                'depA': {'version': '1.0.0', 'pages': ['Template:A']},
                'meta': {'version': '1.0.0', 'pages': [], 'depends_on': ['depA']},
            },
            False,
        ),
        (
            "neither_pages_nor_deps",
            lambda pages: {
                'meta': {'version': '1.0.0', 'pages': [], 'depends_on': []},
            },
            False,
        ),
    ],
)
def test_pack_pages_or_two_deps(manifest, run_validate, tmp_page_factory, case_id, packs_builder, expect_ok):
    # Prepare two pages for dependency packs to be valid
    page_a = tmp_page_factory(name='A')
    page_b = tmp_page_factory(name='B')
    pages = {'Template:A': page_a, 'Template:B': page_b}
    packs = packs_builder(pages)
    mpath = manifest({'pages': pages, 'packs': packs})
    rc, out, err = run_validate(mpath)
    if expect_ok:
        assert rc == 0, f"{case_id} should pass, got rc={rc}, out={out}"
    else:
        assert rc != 0, f"{case_id} should fail, got rc=0"
        assert 'must include at least one page or depend on at least two packs' in out


# ---- Schema selection ----
def test_schema_auto_requires_exact_version(tmp_path, run_validate, tmp_page_factory, manifest):
    # exact version present in index → should succeed
    page = tmp_page_factory(name='Example')
    mpath = manifest({
        'schema_version': '1.0.0',
        'pages': {'Template:Example': page},
        'packs': {'example': {'version': '1.0.0', 'pages': ['Template:Example']}},
    })
    rc, out, err = run_validate(mpath, 'auto')
    assert rc == 0


def test_schema_auto_falls_back_when_major_unmapped(tmp_path, run_validate, tmp_page_factory, manifest):
    # With strict exact version requirement, unmapped version should fail
    page = tmp_page_factory(name='Example')
    mpath = manifest({
        'schema_version': '9.9.9',
        'pages': {'Template:Example': page},
        'packs': {'example': {'version': '1.0.0', 'pages': ['Template:Example']}},
    })
    rc, out, err = run_validate(mpath, 'auto')
    assert rc != 0
    assert "Schema version '9.9.9' not found in index" in out


def test_explicit_schema_override_path(tmp_path, run_validate, tmp_page_factory, manifest):
    # Explicit schema path should work regardless of manifest version
    page = tmp_page_factory(name='Example')
    mpath = manifest({
        'schema_version': '9.9.9',
        'pages': {'Template:Example': page},
        'packs': {'example': {'version': '1.0.0', 'pages': ['Template:Example']}},
    })
    schema_v1 = REPO_ROOT / 'schema' / 'v1_0_0' / 'manifest.schema.json'
    rc, out, err = run_validate(mpath, schema_v1)
    assert rc == 0


# ---- Tags rules ----
@pytest.mark.parametrize(
    "tags, expect_ok, expect_msg_any",
    [
        (['core', 'data-tools'], True, []),
        (['Core'], False, ['pattern', 'does not match']),
        (['core', 'core'], False, ['non-unique elements']),
    ],
)
def test_pack_tags_variants(tmp_path, run_validate, tmp_page_factory, manifest, tags, expect_ok, expect_msg_any):
    page = tmp_page_factory(name='Example')
    mpath = manifest({
        'pages': {'Template:Example': page},
        'packs': {'t': {'version': '1.0.0', 'pages': ['Template:Example'], 'tags': tags}},
    })
    rc, out, err = run_validate(mpath, SCHEMA)
    if expect_ok:
        assert rc == 0
    else:
        assert rc != 0
        assert any(s in out for s in expect_msg_any)


# ---- CLI parity ----
@pytest.mark.parametrize("runner_fixture", ["run_validate", "run_validate_cli"])
def test_cli_and_function_parity(request, tmp_path, runner_fixture):
    run_fn = request.getfixturevalue(runner_fixture)
    write_tmp(tmp_path, 'pages/Templates/T.wiki', '== T ==\n')
    m = {
        'schema_version': '1.0.0',
        'pages': {
            'Template:T': {
                'file': 'pages/Templates/T.wiki',
                'version': '1.0.0',
            }
        },
        'packs': {
            'p': {
                'version': '1.0.0',
                'pages': ['Template:T'],
            }
        }
    }
    mpath = write_tmp(tmp_path, 'manifest.yml', yaml.safe_dump(m, sort_keys=False))
    rc, out, err = run_fn(mpath)
    assert rc == 0, f"expected success, got rc={rc}, out={out}, err={err}"


def test_schema_override_via_dollar_schema_field(tmp_path, run_validate, manifest, tmp_page_factory):
    page = tmp_page_factory(name='X')
    # Use relative path to schema v1; schema_version here should be ignored by auto selection
    rel_schema = REPO_ROOT / 'schema' / 'v1_0_0' / 'manifest.schema.json'
    mpath = manifest({
        '$schema': str(rel_schema),
        'schema_version': '9.9.9',
        'pages': {'Template:X': page},
        'packs': {'p': {'version': '1.0.0', 'pages': ['Template:X']}},
    })
    rc, out, err = run_validate(mpath, 'auto')
    assert rc == 0


def test_schema_version_requires_strict_semver_in_auto(tmp_path, run_validate, manifest, tmp_page_factory):
    page = tmp_page_factory(name='X')
    mpath = manifest({
        'schema_version': '1.0',  # invalid for auto mode strict semver
        'pages': {'Template:X': page},
        'packs': {'p': {'version': '1.0.0', 'pages': ['Template:X']}},
    })
    rc, out, err = run_validate(mpath, 'auto')
    assert rc != 0
    assert 'must be a semantic version (MAJOR.MINOR.PATCH)' in out


def test_rejects_colon_in_filename(manifest, run_validate, tmp_path):
    # Create a file with a colon in its filename to trigger error
    write_tmp(tmp_path, 'pages/Templates/Template:Bad.wiki', '== Bad ==\n')
    mpath = manifest({
        'pages': {'Template:Bad': {'file': 'pages/Templates/Template:Bad.wiki', 'version': '1.0.0'}},
        'packs': {'p': {'version': '1.0.0', 'pages': ['Template:Bad']}},
    })
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'Filename must not contain colon' in out


def test_pack_pages_must_be_array(manifest, run_validate, tmp_page_factory):
    page = tmp_page_factory(name='T')
    mpath = manifest({
        'pages': {'Template:T': page},
        'packs': {'p': {'version': '1.0.0', 'pages': 'Template:T'}},
    })
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert "pages must be an array" in out


def test_pack_references_unknown_page(manifest, run_validate):
    mpath = manifest({
        'pages': {},
        'packs': {'p': {'version': '1.0.0', 'pages': ['Template:Missing']}},
    })
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'references unknown page title' in out


def test_depends_on_unknown_pack_id(manifest, run_validate):
    mpath = manifest({
        'pages': {},
        'packs': {'p': {'version': '1.0.0', 'pages': [], 'depends_on': ['q']}},
    })
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'depends_on unknown pack id' in out


def test_pack_version_must_be_semver(manifest, run_validate):
    mpath = manifest({
        'pages': {},
        'packs': {'p': {'version': 'v1', 'pages': []}},
    })
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'must have semantic version' in out


def test_pack_pages_unique_items(manifest, run_validate, tmp_page_factory):
    page = tmp_page_factory(name='T')
    mpath = manifest({
        'pages': {'Template:T': page},
        'packs': {'p': {'version': '1.0.0', 'pages': ['Template:T', 'Template:T']}},
    })
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'non-unique elements' in out or 'uniqueItems' in out


# ---- Schema properties and structure validations ----
def test_pages_reject_unknown_field(run_validate, manifest, tmp_page_factory):
    page = tmp_page_factory(name='T')
    # Inject unknown field into page meta
    page['extra'] = 'x'
    mpath = manifest({'pages': {'Template:T': page}, 'packs': {}})
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'Additional properties are not allowed' in out


def test_packs_reject_unknown_field(run_validate, manifest):
    mpath = manifest({'pages': {}, 'packs': {'p': {'version': '1.0.0', 'unknown': 1}}})
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'Additional properties are not allowed' in out


def test_last_updated_format(run_validate, manifest):
    mpath = manifest({'last_updated': '2025-09-22', 'pages': {}, 'packs': {}})
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert 'does not match' in out or 'pattern' in out


def test_warns_on_title_missing_namespace(manifest, run_validate, tmp_page_factory):
    page = tmp_page_factory(namespace='')
    mpath = manifest({'pages': {'Person': page}, 'packs': {'ex': {'version': '1.0.0', 'pages': ['Person']}}})
    rc, out, err = run_validate(mpath)
    assert rc == 0
    assert 'Title missing namespace: Person' in out


def test_module_warnings_wrong_extension_and_dir(manifest, run_validate, tmp_path):
    write_tmp(tmp_path, 'pages/Templates/Module_Wrong.txt', 'x\n')
    mpath = manifest({
        'pages': {'Module:Wrong': {'file': 'pages/Templates/Module_Wrong.txt', 'version': '1.0.0'}},
        'packs': {'base': {'version': '1.0.0', 'pages': ['Module:Wrong']}},
    })
    rc, out, err = run_validate(mpath)
    assert rc == 0
    assert 'Module files should use .lua extension' in out
    assert 'Module files should be stored under pages/Modules/' in out


def test_pages_must_be_mapping(run_validate, manifest):
    mpath = manifest({'pages': [], 'packs': {}})
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert "'pages' must be a mapping" in out


def test_packs_must_be_mapping(run_validate, manifest):
    mpath = manifest({'pages': {}, 'packs': []})
    rc, out, err = run_validate(mpath)
    assert rc != 0
    assert "'packs' must be a mapping" in out


# ---- Duplicate key detection ----
def test_duplicate_page_keys_fail_on_load(tmp_path, run_validate):
    manifest_yaml = (
        """
        schema_version: 1.0.0
        pages:
          Template:Dup:
            file: pages/Templates/Dup1.wiki
            version: 1.0.0
          Template:Dup:
            file: pages/Templates/Dup2.wiki
            version: 1.0.0
        packs:
          p:
            version: 1.0.0
            pages: [Template:Dup]
        """
    ).strip() + "\n"
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath, SCHEMA)
    assert rc != 0
    assert 'Failed to read manifest' in out


def test_duplicate_pack_keys_fail_on_load(tmp_path, run_validate):
    manifest_yaml = (
        """
        schema_version: 1.0.0
        pages: {}
        packs:
          dup:
            version: 1.0.0
            pages: []
          dup:
            version: 1.0.0
            pages: []
        """
    ).strip() + "\n"
    mpath = write_tmp(tmp_path, 'manifest.yml', manifest_yaml)
    rc, out, err = run_validate(mpath, SCHEMA)
    assert rc != 0
    assert 'Failed to read manifest' in out
