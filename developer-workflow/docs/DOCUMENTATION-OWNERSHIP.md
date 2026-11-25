# Documentation Ownership and Freshness

`documentation-ownership.json` tells maintainers and tools which files are
canonical, hand-authored, generated, historical, or vendored. It names the
owner, source inputs, freshness method, current status, and required notice for
content that should not be edited or interpreted as a current source.

## Why the map exists

The same fact can appear in a README, guide, template, schema, release note,
and generated report. Updating one copy without knowing which source owns the
fact creates drift. Deleting apparent duplication can also remove navigation,
historical evidence, or a machine-readable contract that serves a different
reader.

The ownership map makes those differences explicit:

| Classification | Meaning | Update rule |
| --- | --- | --- |
| `canonical` | Owns the named policy, architecture, or contract explanation | Review every dependent surface after a material change |
| `hand_authored` | Maintained prose derived from named sources | Update deliberately; do not overwrite from a generator |
| `generated` | Rebuilt from named sources | Edit the source and regenerate |
| `historical_snapshot` | Evidence for its recorded subject and time | Preserve provenance; regenerate a new snapshot instead of relabeling the old one |
| `vendored` | Imported and pinned content | Update through an isolated reviewed change |

## Freshness check

Run:

```bash
python developer-workflow/scripts/validate_documentation_ownership.py \
  --root developer-workflow \
  --manifest developer-workflow/documentation-ownership.json \
  --schema developer-workflow/schemas/documentation-ownership-v1.schema.json
```

The validator checks that:

- every declared document exists;
- every Markdown file under the configured coverage roots has an owner;
- generated, historical, and vendored entries include an interpretation or
  editing notice;
- exported script mirrors match normalized source text;
- exported JSON schemas match their source objects;
- duplicate entries and unsafe relative paths fail.

The validator does not decide whether manually maintained prose is correct. A
fresh mirror can repeat a bad source. A listed canonical source can still be
wrong. Review the final diff, links, rendered layout, accessibility, version
claims, and navigation before release.

## Adding or moving documentation

1. Choose the classification and owner before adding the file.
2. Name the actual source paths or external source identity.
3. Add a notice when the file is generated, historical, or vendored.
4. Update return navigation and page maps where readers need them.
5. Run the ownership check and relevant link or render checks.
6. Preserve historical records unless the change explicitly supersedes them.

Adopting repositories should copy the schema and validator, then create their
own ownership map. The Developer Workflow package map is an example, not an
ownership decision for another repository.
