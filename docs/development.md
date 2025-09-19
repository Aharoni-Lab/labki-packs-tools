## Development

### Create a new pack
1. Create folder: packs/<id>/
2. Add packs/<id>/manifest.yml
3. Add .wiki pages in packs/<id>/pages/
4. Update root manifest.yml
5. Commit with a clear message

### Tips
- Start with a template+form pair
- Define properties used by the template
- Include a category when appropriate

### Testing locally
- Import into a test Labki instance
- Create example pages using the new form
- Verify semantic annotations and queries

### Versioning and releases
- Increment version per semantic versioning
- Document changes in PR descriptions or a CHANGELOG
