# Grounding system validation

## Contract and execution checkpoint

Objective: establish the Portfolio-only skill, project rules, and checks that
guide physical/scene-coherence review at planning and pre-handoff, preserving
navigation exactly. Validate against known failures and approved designs and
state judgment limits. **No website design or behavior changes.**

Worktree: `/home/dlybeck/Projects/Portfolio-worktrees/portfolio-dev`.
Branch: `dev`; starting HEAD `6e691aa6b76ddc3bed0730a2b85646dad84ec8f1`.
This is an existing dirty worktree; prior runtime/theme changes are not part
of this goal. Allowed: local docs, repo-local skill, tests, validation/capture
tools, isolated fixtures, and evidence. No main/push/deploy, global skills,
David Skills changes, theme repair, or recurring AI automation.

Starting website-content SHA-256:
`10572fb2cf5af4eb0a00f4d86f7ad628335315f9648d804195f231e4cce886aa`.
Generated from the sorted per-file SHA-256 output for Git tracked/untracked,
nonignored paths in `apis core static templates main.py Dockerfile
cloudbuild.yaml requirements.txt`. Recheck this exact scope at completion.

Evidence needed: discoverable project-local instructions; unambiguous authority
and navigation boundary; plan and rendered workflow trials on counterexamples
and accepted cases; failing-fixture checks; fail-closed/stale-receipt tests;
actual visual inspection; unchanged website hash; concise limitations.

Current checkpoint: instructions, skill, runner and capture tool implemented;
plan and rendered trials reviewed; 23 isolated checks and skill validation pass.
Website-content hash matches the starting baseline exactly; HEAD remains the
starting commit on dev. The final current-source mechanical run passed and its
receipt was verified on the owner's explicit results-check request. System
setup and validation are complete; theme repairs remain outside this goal.

The review system itself must be assessed against this contract before
completion; file existence and successful skill syntax validation are not
sufficient. Validation commands and results will be recorded below.

## Discovery and mechanical counterexamples

- Native Codex `skills/list` with this worktree as `cwd` and `forceReload:true`
  found `portfolio-grounding`, `scope:repo`, `enabled:true`, no loading errors.
  This was metadata discovery only, not an AI task or global installation.
- System Python ran skill-creator's `quick_validate.py`: **Skill is valid!**
  The app's phase-1 venv lacks PyYAML, so validation used existing system Python
  instead of adding a production dependency.
- `pytest tests/test_grounding_system.py tests/test_grounding_known_failures.py`:
  **23 passed**. The first run went red on accepting wrong-command and
  missing-JUnit receipts; the verifier was corrected and the full group rerun.
  Other cases exercise stale source/rules, added/deleted assets, modified or
  missing logs, incomplete runs, skipped/empty tests, timeouts and failure.
  Final audit added the standalone Original guard to source freshness and a
  regression case: changing the guard invalidates a previous receipt too.
- Isolated copies of actual approved assets pass the material guards; injected
  oval globes, unclipped globe markings, missing ring halves and leaf-top
  ripples fail those same guards. No installed SVG was modified.

## Plan workflow trial

Inputs: `tests/fixtures/grounding/review-cases.md`. The main agent read the
installed local skill and current project rules, then applied them to these
requests without executing their suggested changes. This is a transparent
author-run exercise, **not a blind independent-model evaluation or a measured
future-model success rate**.

| Case | Scoped verdict | Reason / next action |
| --- | --- | --- |
| P1 unchanged sleeve writing | revise | Stationary printed matter changes before occlusion. A clean endpoint is insufficient. Propose a physically visible transition/persistent print; no website repair in this system goal. |
| P2 frog-controlled traversal | revise | Changes the layout, input target and neighbor availability. Preserve navigation even if the metaphor is otherwise plausible. |
| P3 existing planet Grow | ready for implementation, not final handoff | Retains approved chart annotation and scene. Timing changes still require actual motion/neighbor/reduced-motion proof. Do not ban annotation or inclined rings to enforce literalism. |
| P4 renamed weather notebook | revise | Renaming does not change the scene or reverse the owner's rejection. Need a visibly coherent alternative, not another caption. |
| P5 fog prototype | ready for bounded exploration only | Navigation preserved; concept remains unproven. Inspect readability, content reveal/close and phone neighborhood before accepting; no mandatory notebook or premature ban on fog. |
| P6 rebranded dotted connector | revise | Visual evidence is unchanged. Connector appearance participates in grounding even though navigation itself is exempt from redesign. |
| P7 audit-only candidate | revise finding; report only | Metaphor needs work, but audit authority does not permit implementing a fix. Record evidence/uncertainty and request authority. |
| P8 green tests without viewing | unverified | No visual/mid-motion evidence. Mechanical success cannot become a completion or aesthetic-approval claim. |

These exercises establish that the workflow distinguishes plan readiness from
rendered readiness and allows creative experiments without requiring the owner
to invent the solution. They do not prove that every future judgment is correct.

## Rendered workflow trial

Actual screenshots were opened and inspected, not merely generated. Evidence:
`tests/results/grounding/captures-002/`, eight contact sheets covering Canonical,
Planets, Clouds and Postcards at 390x844 and 1440x900. Each covers Home, long
ScribbleScan copy, Programs and Tennis documents, and sampled Hobbies entry / Home
return. The manifest records 96 frames, actual motion sampling elapsed times,
and no page errors. Static captures use reduced motion; motion frames use the
normal setting. This is a scoped workflow trial, not approval of every theme,
route, browser, animation frame or phone. Contact sheets assess composition;
they do not establish pixel-level text readability at their reduced display size.

`portfolio-dev-theme-preview.service` reports this worktree as WorkingDirectory,
running its app on port 51354. The capture requests used that local origin and
verified each requested theme activated. The website-content hash is unchanged
from the starting baseline. Review-system files changed after capture; no
website files did. Do not treat a capture's local fingerprint alone as remote
deployment proof.

| Case | Observed evidence and scoped verdict |
| --- | --- |
| Canonical | **ready within comparison scope**: chalk connections belong on the chalkboard, separate paper covers the smaller note, and opened content retains taped, ruled backing with white inner pages. No reason to reinterpret or redesign the approved original. |
| Planets | **ready within comparison scope**: round bodies, inclined rings with occlusion, and the approved chart/observation-screen vocabulary remain distinct from physically rewriting printed paper. Do not fail an approved annotated chart for not being a literal view into space. |
| Postcards | **ready for the reviewed physical-continuity case**: the envelope title persists while a separate card clears its opening and moves in front, then returns. Airmail-edged opened content belongs to the correspondence vocabulary. Connectors remain visible drawn arrows against the backing, not an invisible exception; their broader aesthetic acceptance was not newly decided here. |
| Clouds | **revise**: the sky itself remains the owner's liked environment, but dashed connections still have no visibly established relationship to it. The opened book visibly remains labeled Sky Observations, the rejected carrier; changing its caption would not fix that relationship. These findings survive green mechanical checks. No repair is authorized in this goal. |

All four retain the same visible neighborhood pattern in the sampled settled
states. The navigation tests supply separate behavioral evidence; screenshots
alone cannot establish routing, keyboard semantics, or interruption handling.
Clouds/Lily connector treatment remains future design work, not a system-setup
blocker and not a reason to change the navigation graph.

The first capture attempt failed while building its contact sheet because the
gallery viewport was passed to the wrong Playwright method. It remained an
incomplete run in `captures-001`; the corrected capture tool produced the fresh
`captures-002` evidence above. No failed output was overwritten or presented as
successful evidence.

## Limits and delivery boundary

- Project instructions require review; this is not an unstoppable runtime hook
  or an autonomous aesthetic judge. Codex can still make reasoning mistakes.
- Deterministic guards reject specific measurable failures and stale/incomplete
  evidence. They do not certify that a scene feels convincing or override owner
  rejection. New failure classes may need new checks and visual cases.
- The exercises were author-run, not independent reviewers or a multi-model
  benchmark. Their purpose is to expose ambiguity and replay known mistakes,
  not claim a measured future compliance rate.
- Review evidence lives in ignored `tests/results/grounding/` directories;
  reproducible commands and findings live here. Do not assume local captures
  travel with a future commit. Preserve needed evidence before cleanup.
- The skill is discoverable in the `portfolio-dev` linked worktree. Nothing was
  installed globally or in David Skills, and the primary checkout, main and
  deployment were not changed. No website design or behavior was changed.

## Final-run checkpoint

The initial broad run `system-001` passed 64 fit/material tests, 23 selected
navigation/motion tests, 81 pack tests, and Original fidelity. Its terminal
status correctly became **stale** because review-system inputs changed during
execution. This is useful freshness evidence, not the final completion proof.
A subsequent run also overlapped the final checker-fingerprint correction;
do not use it for completion.

Final run: `tests/results/grounding/system-003/receipt.json`, launched after
load-bearing source changes were finished. Its OS process records the terminal
status in `/tmp/grounding-system-checks-003.exit` and output in
`/tmp/grounding-system-checks-003.log`. A single bounded completion check found
the process still running; no recurring AI polling is authorized.

On the owner's explicit results-check request, the verifier confirmed:
**Mechanical evidence is current; visual review is still required.** The run
finished at `2026-09-06T19:18:12.141757+00:00` with status
`mechanical_checks_passed`: 64 fit/material, 23 navigation/motion and 81 pack
tests passed, with zero failures, errors or skips; Original fidelity passed.
All required command logs and JUnit artifacts match their recorded hashes.
Current source fingerprint:
`93596f0c63792feb7431cfa44f30d725ba7e6ce80cf8b09e27754af6bac7f046`.

The exact website-content hash was checked again and matches the starting
baseline above. `git diff --check` passed. The separate plan and rendered
reviews above satisfy the system-validation requirement; the mechanical
receipt deliberately does not turn those judgments into theme approval.

Completion audit: repo-scoped discovery and skill validity proven; planning
and pre-handoff instructions present; navigation/Original boundary explicit;
known failures and approved cases exercised; mechanical evidence current;
actual desktop/phone visual review recorded; judgment limits documented;
website unchanged. No required system-setup work remains. Findings about the
Cloudscape book and unexplained connectors are retained for a separately
authorized design task. Nothing was committed, pushed or deployed by this goal.

This report is excluded from the source fingerprint so recording results does
not invalidate the evidence it describes.
