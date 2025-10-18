import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from labki_packs_tools.manifest import Manifest
from labki_packs_tools.types import UTCDateTime

MW_XML_NS = {"export": "http://www.mediawiki.org/xml/export-0.11/"}
"""
Namespace prefixes for mediawiki exports

See: https://docs.python.org/3/library/xml.etree.elementtree.html#parsing-xml-with-namespaces
"""


class ExportPage(BaseModel):
    name: str
    last_updated: UTCDateTime
    content: str

    @classmethod
    def from_xml(cls, tree: ET.Element) -> "ExportPage":
        """
        Parse the content and timestamp from the latest revision of a mediawiki page export

        Args:
            tree (ET.ElementTree): A `page` element from a mediawiki export
        """
        name = tree.find("export:title", MW_XML_NS).text

        # find latest revision
        # revisions are usually exported in chronological order, ascending, but sort to be sure
        revisions = tree.findall("export:revision", MW_XML_NS)
        revisions = sorted(revisions, key=_revision_timestamp)
        latest = revisions[-1]

        last_updated = _revision_timestamp(latest)
        content = latest.find("export:text", MW_XML_NS).text
        return cls(name=name, last_updated=last_updated, content=content)

    @property
    def safe_name(self) -> str:
        """name that is safe to use as a filename"""
        return re.sub(r"[^a-z0-9]", "_", self.name.lower()) + ".wiki"

    def write(self, path: Path) -> None:
        path.parent.mkdir(exist_ok=True, parents=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.content)


def parse_export(path: Path) -> list[ExportPage]:
    """
    Parse a mediawiki export, returning the latest revision of each page.
    """
    tree = ET.parse(path)
    pages = tree.getroot().findall("export:page", MW_XML_NS)
    return [ExportPage.from_xml(page) for page in pages]


def update_manifest(manifest_path: Path, export_path: Path) -> list[ExportPage]:
    """
    Update a manifest from a mediawiki export,
    writing new or updated files,
    and writing an updated copy of the manifest.

    Returns:
        The list of pages that were updated during the update operation
    """
    manifest_path = Path(manifest_path)
    export_path = Path(export_path)
    repo_dir = manifest_path.parent
    manifest = Manifest.from_yaml(manifest_path)
    updated = manifest.update_from_export(export_path, repo_dir)
    if not updated:
        return []
    manifest.last_updated = datetime.now(UTC)
    manifest.to_yaml(manifest_path)
    return updated


def _revision_timestamp(revision: ET.Element) -> UTCDateTime:
    return datetime.fromisoformat(revision.find("./export:timestamp", MW_XML_NS).text)
