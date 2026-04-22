# Changelog

## Unreleased

### Added
- `--hymnal-dir`, if specified, will populate an array of musical scores in `HYMN_SHEETS` which correspond by index to `HYMNS`. Each score is also an array since a score may contain multiple sheets. Each sheet is encoded as a base64 uri of a rasterized image of the source.
- Schedule column headers that build arrays are matched by prefix, so you can add a note about the conventional purpose of data at this index. 
	e.g. `Hymn 1 - Call to Worship`.

### Changed
- Scripture references are modeled as an array, like hymns.
- Schedules index arrays from one, handlebars from zero. The assumption is non-programmers might be editing the schedule and zero is better in programming contexts.
- If a particular array entry is missing from the schedule, a null value will be written to the array to preserve index pairing for subsequent indices.

### Deprecated
 
### Removed

### Fixed
- Single chapter book references (e.g. `Jude 1-3`) are correctly parsed

### Security

## 2.0.0 - 2025-09-14

Initial public release
