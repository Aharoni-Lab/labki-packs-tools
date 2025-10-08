import json
from importlib.metadata import Distribution
from pathlib import Path


def _get_schema_dir() -> Path:
    """
    Get the schema directory

    Gets the top-level repo-level schema if an editable installation from the git repository,
    and otherwise uses the in-package version if installed from a wheel or sdist
    """
    # check if we are in editable mode,
    # which is the only case where we would want to use the top-level schema directory
    # (i.e. we are working on the code and would expect changes to the schema be reflected)
    # See: https://github.com/pypa/setuptools/issues/4186
    direct_url = Distribution.from_name("labki-packs-tools").read_text("direct_url.json")
    is_editable = json.loads(direct_url).get("dir_info", {}).get("editable", False)

    if is_editable:
        return Path(__file__).parents[2] / "schema"
    else:
        return Path(__file__).parent / "schema"


SCHEMA_DIR = _get_schema_dir()
SCHEMA_INDEX = SCHEMA_DIR / "index.json"
