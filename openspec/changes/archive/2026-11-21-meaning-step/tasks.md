# Tasks

## 1. Evaluation

- [x] 1.1 Add the daemon method `meaning`: seeded values from `default_cases`, rejection by the hypotheses, exact then interval evaluation (D1, D2, D3). Verify with pytest on serialized problems: the two scenario claims, a narrow hypothesis that gives `undecided`, and the same seed giving the same values.
- [x] 1.2 Try `symbolic_check` first for equations (D4). Verify with pytest: the trigonometric identity agrees symbolically, and an identity it cannot decide falls back to sampling.

## 2. Command and step

- [x] 2.1 Add `#veriphy_meaning` in Lean, reusing `sage_test`'s binder opening. Verify with Lean tests in `VeriphyTest/SageRun.lean` for the scenarios, run in the integration job.
- [x] 2.2 Add the `meaning` step with `--informal`, `--seed` and `--values` (D5). Verify with pytest: the record has kind `evidence` and no level, and replay returns it.

## 3. Playbooks and integration

- [x] 3.1 Rewrite `prove.md` step 1 and `research/triage.md` to run the step and cite its record. Verify with the recipe and research document tests, extended to check that both playbooks name the step.
- [x] 3.2 Run the gate and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
