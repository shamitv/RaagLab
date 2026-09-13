# Phase 00: Discovery and contracts

## Objective

Turn the portable application prompt, product specification and visual references into an actionable, internally consistent implementation plan. Resolve routine architecture/data/UI decisions early and make every requirement, dependency, acceptance check and real-model deferral explicit before application code is written.

## Dependencies and entry criteria

Access to the repository and Part 1 prompt. Read applicable instructions and inspect current state before writing. Read `design.md`, inspect both actual mockup images, and read the Part 2 boundary so portable work is not confused with machine deployment. The user requested the plan on `planning-docs`; this run is planning only and does not continue into Phase 01 application implementation.

## Scope

Repository/reference audit, architecture decision, selected dependency/image baseline and compatibility checks, schema/API/provider/queue/storage/UI contracts, seven phase plans with status/to-do tracking, requirement mapping, verification strategy and documentation integrity evidence. No application source, migrations, Compose runtime, real provider, model weights or deployment state is created in this phase.

## Work breakdown

1. **00-01** Inspect repository, current branch/base commit and applicable instructions; record actual files/environment limitations and preserve reference hashes.
2. **00-02** Read Part 1/design and Part 2 scope; inspect desktop/mobile images and document responsive/capability/scope tradeoffs, including the 1440 px width conflict.
3. **00-03** Record ADR 0001 and concrete HTTP/schema/provider/artifact/queue contracts, immutable version/selection rules, idempotency, outbox/lease/cancellation/recovery strategy and local security boundary.
4. **00-04** Select compatible supported runtime/direct package/image pins using primary metadata/docs; run isolated dependency resolution checks and record their limits without claiming runtime integration.
5. **00-05** Write master/overall tracking and all seven phases' concrete plans/status/to-do lists with stable identifiers, entry dependencies, deliverables, acceptance criteria and planned verification commands.
6. **00-06** Map every Part 1/design section and all twelve numbered acceptance checks to owner phases/evidence, retaining explicit Part 2 D00–D05 handoff and unselected-model scope.
7. **00-07** Audit required files/headings, relative links, phase/task/acceptance consistency, preserved source hashes, whitespace and documentation-only change scope; fix any gaps and record evidence.
8. **00-08** Synchronize phase/overall tracking and create the Phase 00 implementation-status.md for completed documentation work only; leave future-phase implementation tasks/reports open/absent and provide the plan links to the user.

## Contracts and data changes

Documented decisions only: [contracts](../../contracts.md), [job reliability](../../job-reliability.md), [UI behavior](../../ui-behavior.md), [ADR](../../decisions/0001-application-architecture.md), and [dependency baseline](../../dependency-baseline.md). No database schema is applied. Future endpoint/schema/module names are implementation obligations, not claims of existing behavior. Real model selection/adapter remains Part 2 D03.

## Acceptance criteria

- **00-AC1:** Baseline repository/instructions and all three product references are inspected; both prompt files and images remain unchanged and model/host assumptions are explicit.
- **00-AC2:** Architecture, selected versions and API/data/provider/queue/storage/selection/recovery contracts contain concrete decisions sufficient to start foundation work.
- **00-AC3:** Master plan plus all seven plan/status/to-do sets exist with dependency-ordered work, stable IDs, deliverables, acceptance checks and verification instructions; Phase 02 remains the early integrated checkpoint.
- **00-AC4:** The requirement matrix covers Part 1/design sections and all A01–A12 checks with owners/evidence; Part 2 and unavailable product scope remain explicit.
- **00-AC5:** Documentation integrity and original-file preservation checks pass; dependency checks are recorded accurately and no application build/runtime/browser test is falsely reported.
- **00-AC6:** Overall/phase status is synchronized, Phase 00 closure describes documentation only, future-phase tasks remain unchecked and future completion reports are absent.

## Verification

Run the reproducible documentation audit recorded in [planning verification](../../evidence/planning-verification.md). Inspect file presence/headings, link targets, task IDs and matching plan/to-do text, nonempty acceptance/verification sections, phase states/report presence, full prompt/design/A01–A12 ownership and preserved reference SHA-256 values. Run `git diff --check` and audit whitespace in new untracked Markdown as well. Review the documented commands and contracts manually for missing gates/inconsistent scope. Dependency resolution was performed in an isolated temporary workspace; it is not a source implementation or runtime acceptance check.

## Risks, assumptions, and deferred work

No Docker executable was discoverable in this authoring shell; Phase 01 must identify an appropriate existing Linux-engine execution environment before container verification. Real hardware/model capabilities are unknown and intentionally deferred. Selected versions can change before implementation; Phase 01/06 must record necessary pin/lock updates and retest affected gates. Completing Phase 00 proves the plan and decisions, not the application, machine deployment or real inference.

See [master plan](../../master-plan.md), [status](status.md) and [to-do list](todo.md).
