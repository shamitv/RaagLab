# Phase 05 provider-readiness evidence (local checks)

Date: 2026-09-14. Branch: `phase-5-provider-readiness`, based on
`da3474277f7b1bbed89a8a208db6f192f76a55b4` (`origin/main`). This is partial
verification for the working-tree implementation, not a Phase 05 completion
report.

## Capability and contract changes

The API now exposes a typed supported/unsupported/unknown capability matrix for
the mock and pinned YuE2 adapter. New version provenance records the matrix;
historical provenance without it remains readable. The composer follows the
active provider's lyrics modes, language list, and operations; prevents generation
from unsupported saved choices; disables unsupported duration control; and shows
provider identity, readiness, capability evidence, and warnings. The YuE2 model
capability audit and measured application boundary are recorded in
[`docs/model-integration.md`](../../../../model-integration.md).

## Checks run in this checkout

| Check | Result |
| --- | --- |
| `.venv/bin/python -m pytest tests/unit -q` | 148 passed; one optional NumPy-dependent test skipped because NumPy is not installed in this local environment |
| `npm test` in `apps/web` | 3 passed |
| `npm run build` in `apps/web` | TypeScript check and Vite production build passed |
| `API_BASE_URL=http://127.0.0.1:4173 npm run test:browser -- browser/capabilities.spec.ts --project=desktop` | 1 passed against Vite; the test intercepted health, settings, and capabilities responses to verify provider-driven UI behavior |
| API capability route contract tests in `tests/unit/test_capabilities.py` | Passed as part of the Python unit suite; response schema and old-provenance compatibility covered |
| API OpenAPI export and `npm run types:api` | Passed; generated types require the capability matrix on current capability responses and make it optional on historical version provenance |

The browser check above is a frontend regression with API responses intercepted;
it is not counted as an API-served browser acceptance run.

## Remaining integrated checks

The local environment has no Docker or Compose executable. This run therefore did
not repeat real-service provider routing/lifecycle tests, inspect resolved Compose
profiles and queue bindings, run the API-served browser regression, or run
`scripts/smoke.sh mock`. The prior [D03 integration evidence](../../../../deployment/evidence/2026-09-14-d03-review-corrections/README.md)
records those real-worker startup/routing/no-fallback checks and a mock regression
run against the Phase 04 baseline; Phase 05 still needs its fresh combined run on
a Docker runner. No capability claim above treats that earlier run as evidence of
musical behavior.
