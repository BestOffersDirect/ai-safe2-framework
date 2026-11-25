# Local Validation and Type Boundaries

The local gate catches fast, deterministic failures before a push. It does not
replace hosted CI, secret scanning, dependency review, security review, or a
human decision.

## Install the local development tools

```bash
python -m pip install -r developer-workflow/requirements-dev.txt
pre-commit install
```

Run the same gate without pre-commit:

```bash
python developer-workflow/scripts/run_local_gate.py \
  --config developer-workflow/local-gate.json \
  --repository developer-workflow
```

Required checks fail when their command fails or cannot run. Optional checks
may report `unavailable` without passing a required capability.
The pytest check uses the ignored `developer-workflow/.test-temp-local-gate`
directory so it does not depend on a shared operating-system temp directory.

## Current type boundary

Strict mypy checking applies to the Developer Workflow scripts added for
baseline measurement, project discovery, and local-gate execution:

- `scripts/measure_repository_baseline.py`;
- `scripts/discover_project.py`;
- `scripts/run_local_gate.py`.

This boundary does not establish strict typing for the full AI SAFE2 CLI,
Gateway, NEXUS, examples, or third-party adapters. NEXUS retains its own mypy
configuration. Expanding either boundary requires a separate baseline and must
not hide existing errors with broad exclusions.

## Hosted evidence still required

The root repository currently runs tests, Ruff, Gitleaks, and other checks in
GitHub Actions. A local pass shows only that the configured commands returned
success in the developer's environment. The pull-request decision record must
use hosted results tied to the exact revision when policy requires them.

Local output is diagnostic evidence. It is not trusted execution attestation,
review independence, merge approval, release approval, or proof that the
repository is secure.

The repository template installs a smaller default gate that validates the AI
SAFE2 workflow contract. Adopters add their own fast tests, formatting, type,
and project checks to `.ai-safe2/local-gate.json`; the template does not guess
commands or claim coverage it has not observed.
