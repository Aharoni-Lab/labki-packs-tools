from pathlib import Path
from typing import Any


def pdm_build_update_files(context: Any, files: dict[str, Path]) -> None:
    """
    Package schema in distributions
    """
    repo_dir = Path(__file__).parent
    schema_dir = repo_dir / "schema"

    for schema_file in schema_dir.glob("**/*.json"):
        # prefix with src/labki_packs_tools so the schema end up in the package itself
        # rather than the `site-packages` directory
        files["src/labki_packs_tools/" + str(schema_file.relative_to(repo_dir))] = schema_file
