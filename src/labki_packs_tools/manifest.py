"""
Pydantic models for manipulating the manifest within the package.

At the moment, the manually-created json schema is the
source of truth for the manifest, and this is just for programmatic use.
These models are thus *not* strictly validating,
e.g. the fields don't have the correct regex patterns
to avoid defining them twice in a conflicting way.

see the `validation` subpackage.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Union

import yaml
from pydantic import BaseModel, Field

from labki_packs_tools.types import UTCDateTime

if TYPE_CHECKING:
    from labki_packs_tools.ingest import ExportPage


class ManifestPage(BaseModel):
    file: str
    last_updated: UTCDateTime
    description: str | None = None


class ManifestPack(BaseModel):
    description: str | None = None
    version: str
    pages: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class Manifest(BaseModel):
    schema_version: str = "1.0.0"
    name: str
    last_updated: UTCDateTime | None = None
    pages: dict[str, ManifestPage] = Field(default_factory=dict)
    packs: dict[str, ManifestPack] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path | str) -> "Manifest":
        path = Path(path)
        with open(path) as f:
            data = yaml.safe_load(f)
        return Manifest(**data)

    def to_yaml(self, path: Path | str) -> None:
        dumped = self.model_dump(exclude_unset=True)
        with open(path, "w") as f:
            yaml.safe_dump(dumped, f)

    def update_from_export(
        self, export_path: Path | str, repo_dir: Path | str
    ) -> list["ExportPage"]:
        """
        Update a manifest from a mediawiki export .xml file

        Args:
            export_path (Path | str): Path to the export .xml file
            repo_dir (Path | str): Root directory that contains `manifest.yml` and `pages`

        Returns:
            A list of `ExportPage` objects for which the entry in the manifest was updated
        """
        from labki_packs_tools.ingest import parse_export

        export_path = Path(export_path)
        repo_dir = Path(repo_dir)
        repo_dir.mkdir(exist_ok=True, parents=True)

        pages = parse_export(export_path)
        updated = []
        for page in pages:
            p = self._update_page(page, repo_dir)
            if p is not None:
                updated.append(p)
        return updated

    def _update_page(self, page: "ExportPage", repo_dir: Path | str) -> Union["ExportPage", None]:
        """
        Update a single page from an exported .xml file page,
        writing the file if it doesn't exist or has been updated
        since the last recorded update time
        """
        repo_dir = Path(repo_dir)
        if page.name not in self.pages:
            page_path = repo_dir / "pages" / page.safe_name
            page.write(page_path)
            self.pages[page.name] = ManifestPage(
                file=str(page_path.relative_to(repo_dir)),
                last_updated=page.last_updated,
            )
            return page
        elif page.last_updated > self.pages[page.name].last_updated:
            page_path = repo_dir / self.pages[page.name].file
            page.write(page_path)
            self.pages[page.name].last_updated = page.last_updated
            return page
        else:
            # no update performed
            return None
