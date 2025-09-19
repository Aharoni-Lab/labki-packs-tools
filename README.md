# Labki Packs

Reusable content packs for Labki-based wikis. This repository provides modular, versioned pages (templates, forms, properties, and categories) that can be imported via the LabkiPackManager extension.

Note about filenames: Windows does not allow : in filenames. We save pages using underscores (e.g., Template_Publication.wiki) and place the intended wiki page title in the first line as an HTML comment, e.g.:

`wiki
<!-- Title: Template:Publication -->
`

## Manifests

- Root manifest.yml indexes all packs
- Each pack has its own manifest.yml describing its contents and dependencies

Example (root):

`yaml
packs:
  - id: publication
    path: packs/publication
    version: 1.0.0
    description: Templates and forms for managing publications
  - id: onboarding
    path: packs/onboarding
    version: 1.1.0
    description: Standardized onboarding checklists
  - id: meeting_notes
    path: packs/meeting_notes
    version: 1.0.0
    description: Templates and forms for meeting notes
`

Example (pack):

`yaml
name: Publication Pack
id: publication
version: 1.0.0
description: Standard template and form for adding publications
dependencies:
  - SemanticMediaWiki >=6.0
  - PageForms >=5.6
contents:
  - Template:Publication
  - Form:Publication
  - Category:Publication
  - Property:Has author
`

## Using with LabkiPackManager

1. Ensure your Labki wiki has the LabkiPackManager extension installed and enabled.
2. Make this repository accessible to the wiki host (clone or reference a remote).
3. In LabkiPackManager, add this repo as a content source and import desired packs (publication, onboarding, meeting_notes).
4. After import, new page templates/forms will be available for use.

See docs/usage.md for details.

## Creating a new pack

- Create packs/<pack_id>/manifest.yml
- Add .wiki files under packs/<pack_id>/pages/
- Use Windows-safe filenames and include the intended page Title: comment
- Update root manifest.yml

See docs/development.md for a step-by-step guide.

## Contributing

- Open a PR with a clear summary and pack-level manifest updates
- Keep changes modular by pack
- Follow naming and semantic conventions in docs/conventions.md

## License

TBD
