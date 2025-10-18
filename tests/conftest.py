from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import pytest
from _pytest.python import Function

from tests.utils import make_manifest, make_page_file

# ────────────────────────────────────────────────────────────────
# CLI options
# ────────────────────────────────────────────────────────────────


def pytest_addoption(parser: argparse.ArgumentParser) -> None:
    parser.addoption(
        "--with-packaging",
        action="store_true",
        default=False,
        help="Run tests marked with `@pytest.mark.packaging`, which are excluded by default.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[Function]) -> None:
    if not config.getoption("--with-packaging"):
        skip_packaging = pytest.mark.skip(reason="use --with-packaging to run packaging tests")
        for item in items:
            if item.get_closest_marker("packaging"):
                item.add_marker(skip_packaging)


# ────────────────────────────────────────────────────────────────
# Paths
# ────────────────────────────────────────────────────────────────


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def fixtures_repo(repo_root: Path) -> Path:
    return repo_root / "tests" / "fixtures" / "basic_repo"


@pytest.fixture
def test_data(repo_root: Path) -> Path:
    return repo_root / "tests" / "data"


@pytest.fixture
def mediawiki_data(test_data: Path) -> Path:
    return test_data / "mediawiki"


@pytest.fixture
def export_data(mediawiki_data: Path) -> Path:
    return mediawiki_data / "export"


# ────────────────────────────────────────────────────────────────
# Fixtures built from shared utilities
# ────────────────────────────────────────────────────────────────


@pytest.fixture
def base_manifest(tmp_path: Path) -> Callable[[dict | None], Path]:
    """Create a valid minimal manifest for mutation and return its path."""
    return lambda overrides=None: make_manifest(tmp_path, overrides)


@pytest.fixture
def tmp_page(tmp_path: Path) -> Callable[..., dict]:
    """Create a valid dummy page and return its manifest entry."""
    return lambda **kwargs: make_page_file(tmp_path, **kwargs)
