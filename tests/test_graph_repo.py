import subprocess
import sys
from pathlib import Path

from tools.utils import load_yaml
from tools.graph_repo import emit_dot


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / 'tests' / 'fixtures' / 'basic_repo'


def test_emit_dot_contains_expected_nodes_and_edges():
    manifest_path = FIXTURES / 'manifest.yml'
    manifest = load_yaml(manifest_path)
    dot = emit_dot(manifest)

    # Packs cluster nodes
    assert 'pack_publication' in dot
    assert 'pack_meeting_notes' in dot
    assert 'pack_onboarding' in dot

    # Pages cluster nodes (a subset)
    assert 'page_Template_Publication' in dot
    assert 'page_Form_Publication' in dot
    assert 'page_Onboarding' in dot

    # Includes edges: page -> pack
    assert 'page_Template_Publication -> pack_publication' in dot
    assert 'page_Form_MeetingNotes -> pack_meeting_notes' in dot

    # Depends_on edge: dependency -> dependent pack (publication -> onboarding)
    assert 'pack_publication -> pack_onboarding' in dot


def test_graph_cli_writes_dot_to_file(tmp_path: Path):
    out = tmp_path / 'graph.dot'
    manifest_path = FIXTURES / 'manifest.yml'
    rc = subprocess.run(
        [sys.executable, '-m', 'tools.graph_repo', str(manifest_path), '--format', 'dot', '--output', str(out)],
        capture_output=True,
        text=True,
    )
    assert rc.returncode == 0, f"stderr={rc.stderr}"
    content = out.read_text(encoding='utf-8')
    assert content.startswith('digraph Manifest {')
    assert 'subgraph cluster_packs' in content
    assert 'subgraph cluster_pages' in content


