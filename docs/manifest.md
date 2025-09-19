## Manifest specification

### Root manifest (manifest.yml)

Fields:
- packs: list of pack entries
  - id (string): short identifier
  - path (string): relative path to the pack folder
  - version (string): current version of the pack
  - description (string): short human description

### Pack manifest (packs/<id>/manifest.yml)

Fields:
- name (string): human-friendly name
- id (string): pack identifier (matches root entry id)
- version (string): semantic version
- description (string): human description
- dependencies (list of strings): extension requirements, e.g. SemanticMediaWiki >=6.0
- contents (list of strings): wiki page titles included in the pack

Example:

`yaml
name: Example Pack
id: example
version: 0.1.0
description: Demonstration pack
dependencies:
  - SemanticMediaWiki >=6.0
  - PageForms >=5.6
contents:
  - Template:Example
  - Form:Example
  - Category:Example
`

### Resolution of .wiki files
- Files are stored under packs/<id>/pages/*
- Filenames are Windows-safe and may replace : with _
- The first line of each file is an HTML comment of the intended wiki title, e.g. <!-- Title: Template:Example -->
- Import tooling uses this Title to map the file to the wiki page name
