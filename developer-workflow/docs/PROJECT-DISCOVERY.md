# Project Discovery

Project discovery records repository facts before planning begins. It does not
change the target repository, install tools, select a risk tier, or authorize
work.

## Generate a project map

```bash
python developer-workflow/scripts/discover_project.py \
  --repository . \
  --output .ai-safe2/project-map.json
```

Validate the output against
`developer-workflow/schemas/project-map-v1.schema.json`.

The map records:

- observed languages and file counts;
- package and build ecosystems with source paths;
- GitHub workflow files;
- repository instruction and security files;
- nearby README entry points;
- directories whose names suggest that a human should inspect them for trust,
  data, payment, policy, release, secret, or agent-tool boundaries.

Path-name matches are review candidates. They do not prove that a directory is
sensitive or that an unlisted directory is safe.

The subject records the base revision and whether uncommitted changes were
present. A dirty project map describes the working tree and must not be cited as
evidence for the base commit alone.

## Use the CLI-owned planning contracts

The Developer Workflow does not define a second execution-plan or task-receipt
format. AI SAFE2 CLI owns these contracts:

- `safe2/data/development-plan-v1.schema.json`;
- `safe2/data/development-receipt-v1.schema.json`;
- `safe2/data/task-receipt-v1.schema.json`.

After a human reviews the project map, use `safe2 dev plan` to record the
outcome, scope, exclusions, acceptance conditions, delivery shape, risk tier,
trust boundaries, assumptions, unknowns, evidence requirements, and isolation
strategy. Use `safe2 dev receipt` at the final revision.

The project map supplies observations. The CLI policy may raise risk and add
evidence requirements. Neither the map nor the plan can approve a merge,
release, deployment, exception, policy change, or risk acceptance.

## Review before planning

Confirm or correct:

1. the repository and revision;
2. detected ecosystems and automation;
3. the instructions that apply to the work;
4. actual trust and data boundaries;
5. external services and deployed environments;
6. owners for security, release, policy, and residual risk decisions;
7. sensitive paths missed by path-name discovery.

Store the reviewed project map with the planning evidence or regenerate it
when the revision or repository structure materially changes.
