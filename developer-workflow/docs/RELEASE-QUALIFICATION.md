# Release Qualification

The build sequence creates a release candidate. It does not qualify or publish
one. Release qualification requires evidence for the exact candidate revision
and stops at `ready_for_human_release_decision`.

## Test before publishing

- Run the package gate from the candidate checkout to test the code, schemas,
  export, and local game fixture. The [local validation guide](LOCAL-VALIDATION-AND-TYPES.md)
  lists the dependencies and commands.
- Install the export on a branch in a separate game repository and open a test
  pull request. GitHub Actions can exercise the pinned CLI, routing, and
  artifact publication before any game deployment. Follow the
  [game quickstart](GAME-DEVELOPER-QUICKSTART.md).
- Keep the framework integration PR and the package release decision separate.
  Merging the source preview into `main` leaves release qualification at
  `hold` until the required evidence exists. Deployment-specific claims
  require evidence from the deployed environment.

## Required release evidence

Use these capabilities for the first external preview candidate:

1. `local-gate`: complete package tests, strict typing, ownership, and mirror
   freshness checks;
2. `hosted-ci`: the same candidate revision passes the repository's hosted
   workflow;
3. `clean-game-canary`: a new game repository installs the export template,
   replaces placeholders, routes representative changes, and preserves hold;
4. `security-review`: an attributable review covers untrusted pull requests,
   permissions, secrets, artifact publication, and script inputs;
5. `placeholder-resolution`: no unresolved `REPLACE-*` value remains in the
   distributable repository template;
6. `package-integrity`: the candidate archive, file inventory, checksums, and
   version metadata match the reviewed revision.

Record each result as `not_requested`, `unavailable`, `failed`, or `produced`.
Evidence from another revision does not satisfy the candidate.

## Evaluation

Copy `release-qualification.template.json`, replace its candidate values, and
attach truthful evidence states. Then run:

```bash
python developer-workflow/scripts/evaluate_release_qualification.py \
  --record release-qualification.json \
  --schema developer-workflow/schemas/release-qualification-v1.schema.json \
  --output evaluated-release-qualification.json
```

The evaluator reports missing capabilities. It cannot record the human release
decision, create a tag, publish an archive, alter repository settings, accept
risk, or claim that an external canary or security review occurred.

## Profile qualification

The game profile is a bundled preview with local routing fixtures. It remains a
preview until a clean external game-repository canary is retained. Mobile,
API/service, AI-agent, and infrastructure profiles remain planned. Do not copy
the game profile, rename it, and present it as a qualified specialized profile.

A profile marked `qualified` must identify an external-repository canary and
evidence reference under `ai-safe2.product-profile.v1`. Repository owners still
adapt paths, roles, trust boundaries, release systems, and rollback behavior.

## Human release decision

`ready_for_human_release_decision` means the required evidence is present for
the candidate revision. The named release owner still decides whether to
publish, defer, or reject the candidate and records the rationale, residual
risk, recovery path, and distribution destination separately.
