# Proposal

## Why

Every `sage_*` tactic runs the same six stages: parse the goal and hypotheses, call the daemon, solve in Sage, rebuild Lean syntax, check with a mathlib checker, and emit a Sage-free `Try this:`. Only the solve step and the choice of checker differ between tactics. The other stages were copied for each new tactic, and the same bugs came back with the copies:

- `sage_farkas` re-implemented `sage_lincomb`'s hypothesis collection, and `sage_exists` re-implemented `sage_witness`'s witness reconstruction.
- Hygienic names (`hfk✝`, `not_le✝`) leaked into printed proofs that then failed to re-parse.
- An LP with no constraints crashed PPL.
- `peelExists` had to be restructured into CPS form.

`sage_lincomb` still differs from `sage_farkas` on inaccessible hypotheses, which shows the copies have already drifted.

There is a second cost. Each new certificate shape needs a new tactic, so the agent stops with `blocked-missing-tactic` even when a mathlib checker could verify the certificate and Sage could find it in a few lines of `run_script`. If we expose the components themselves (normalized problems, builders and checker families), the agent can assemble a one-off certificate at proof time. The kernel still checks every proof.

## What Changes

- **Lean problem extraction** (new `Veriphy/Kit/`): one shared atom table plus extractors that turn the goal and local context into a normalized `Problem`. A problem holds typed constraints (`=`, `≤`, `<`, `≠`, with `≥`/`>` flipped), source hypothesis names, peeled `∃` binders and split conjunctions. Inaccessible hypotheses are skipped consistently.
- **Lean proof reconstruction**: builders for rationals, polynomials (moved from `Translate.lean`), weighted sums of hypotheses, witness tuples and tactic step sequences. Every identifier they emit is unhygienic and user-nameable, so printed proofs re-parse.
- **Checker families**: a small fixed set of proof shapes, each of which runs its check and emits the `Try this:` replacement:
  - `identity`: `ring1` or `linear_combination`.
  - `inequality`: `linear_combination` with nonnegative weights and `sq_nonneg` terms (positivity side conditions), with a refutation variant that uses `norm_num`.
  - `witness`: an anonymous constructor plus `norm_num`.
  - `sum`: induction plus `ring1`.
  - `cases`: `decide`.
- **Typed bridge calls**: a single `Bridge.call` with a JSON decoder replaces the hand-written request and parse code in each `Bridge.*` function.
- **Python method framework** (`sage_bridge/`): an `@method` decorator handles parameter parsing (ring construction and identifier validation), exact-rational and term-list output encoding, and uniform error messages. Shared solver helpers include an exact rational LP that guards against empty problems and returns `None` when the LP is infeasible.
- **Replay harness**: a `veriphy.checkReplay` option. When it is on, every emitted replacement is pretty-printed, re-parsed from text, and re-elaborated against the original goal with the daemon disabled. A mismatch is a tactic error. The test suite turns the option on.
- **Agent route, `sage_certify`**: a new generic tactic, `sage_certify <family> "<sage script>"`. It extracts the problem, binds it into a `run_script`-style Sage session, and reads back a `certificate` value in the family's schema. It then builds and checks the proof with that family's checker. The `Try this:` it emits is the plain checker proof; the script never reaches committed proofs.
- **Refactor**: all seven existing tactics (`sage_factor`, `sage_sos`, `sage_lincomb`, `sage_witness`, `sage_sum`, `sage_farkas`, `sage_exists`) are rebuilt on the components. Their syntax is unchanged. The surface form of their printed replacements may change, but each replacement must pass the replay check.
- **Docs**: `prompts/prove.md` adds a step for `sage_certify` before the agent reports `blocked-missing-tactic`. `docs/DESIGN.md` §4 records that the catalog now grows by checker families and agent certificates rather than by bespoke tactics. A short "adding a certificate" guide is added.

No **BREAKING** changes to tactic syntax. `Veriphy.Translate`'s builders move into the kit and are re-exported, so existing imports keep compiling.

## Capabilities

### New Capabilities
- `certificates/problem-extraction`: normalizes a Lean goal and its context into a constraint problem with a shared atom table and Sage encoding.
- `certificates/proof-reconstruction`: builds re-parseable Lean syntax (rationals, polynomials, weighted hypothesis sums, witnesses, step sequences) from certificate data.
- `certificates/checker-families`: the fixed set of kernel-checked proof shapes and the uniform way a tactic closes a goal and emits its Sage-free replacement.
- `certificates/oracle-methods`: the daemon's method contract (registration, parameter parsing, exact output encoding, error reporting) and shared exact solvers.
- `certificates/replay-check`: verifies that every emitted replacement re-parses and closes the original goal without Sage.
- `certificates/agent-certify`: the generic `sage_certify` tactic, which checks agent-written Sage certificate scripts with a chosen checker family.

### Modified Capabilities
<!-- none: openspec/specs/ is empty -->

## Impact

- **Lean**:
  - New modules under `Veriphy/Kit/`.
  - `Veriphy/Translate.lean` is slimmed down and re-exports the builders.
  - `Veriphy/Bridge.lean` gains a typed call helper and a `certify` method.
  - All seven `Veriphy/Tactic/*.lean` files are rewritten, plus a new `Veriphy/Tactic/SageCertify.lean`.
  - `Veriphy.lean` gets new imports.
- **Python**:
  - `sage_bridge/server.py` is restructured around the decorator, with a new `certify` method.
  - A new `sage_bridge/test_server.py`, run with `sage -python -m unittest`.
- **Tests**: `VeriphyTest.lean` turns on `veriphy.checkReplay` and adds regressions for hygiene, inaccessible hypotheses, empty LPs and `sage_certify`.
- **Docs**: `prompts/prove.md`, `docs/DESIGN.md`, `README.md` and `skills/prove/SKILL.md` (if it duplicates the tactic list).
- **Trust base**: unchanged. Sage, the scripts, the kit and the builders stay untrusted; only mathlib checkers close goals.
