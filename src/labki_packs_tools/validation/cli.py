from __future__ import annotations

import argparse
import sys
from pathlib import Path

from labki_packs_tools.validation.repo_validator import validate_repo
from labki_packs_tools.validation.result_formatter import print_results, print_results_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a Labki content repository")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_validate = sub.add_parser("validate", help="Validate a manifest")
    p_validate.add_argument("manifest", type=Path, help="Path to manifest.yml")
    p_validate.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of colored text",
    )

    args = parser.parse_args()

    if args.cmd == "validate":
        rc, results = validate_repo(args.manifest)

        if args.json:
            print_results_json(results)
        else:
            print_results(results, title="Validation results")

        sys.exit(rc)


if __name__ == "__main__":
    main()
