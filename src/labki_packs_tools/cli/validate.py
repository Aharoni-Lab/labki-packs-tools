from pathlib import Path

import click

from labki_packs_tools.validation.repo_validator import validate_repo


@click.command("validate")
@click.argument(
    "manifest",
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--json",
    is_flag=True,
    help="Output results as JSON instead of colored text",
)
def validate(manifest: Path, json: bool) -> None:
    """
    Validate a Labki content repository manifest.

    Validates the manifest against JSON Schema and repository rules.
    Returns non-zero exit code on validation errors (suitable for CI).
    Warnings do not change the exit code.
    """
    rc, results = validate_repo(manifest)
    if json:
        results.print_json()
    else:
        results.print(title="Validation results")
    
    # Exit with the return code from validation
    raise SystemExit(rc)
