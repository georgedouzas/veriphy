# Proposal

## Why

Veriphy's certificates cover only a small slice of real goals:
- seven bespoke tactics, each tied to one certificate shape;
- `sage_certify`, which accepts only three fixed certificate schemas.

Anything outside those shapes ends as `blocked-missing-tactic`. Examples are case splits, products of hypotheses, multi-step derivations, rational witnesses with non-trivial side conditions, and matrix identities. Adding tactics one by one cannot keep up.

What generalizes is the division of labour. Sage finds whatever is expensive to find (coefficients, products, substitutions, case splits, witnesses, intermediate forms). Lean's existing automation (`linear_combination`, `nlinarith`, `positivity`, `field_simp`, `ring`, `norm_num`, `decide`) checks it. So the agent needs composable building blocks that let a Sage script assemble a Lean proof on the fly, plus a fast loop to iterate on it.

## What Changes

- **`sage_run "<script>"`, a general tactic.** The agent's Sage script runs against the extracted problem and returns a Lean tactic block.
  - Lean runs exactly that block, then checks the resulting proof term for `sorry` and non-standard axioms.
  - When replay is on, the block is replayed with Sage disabled.
  - On success it is emitted as the single `Sage-free replacement:`.
  - Sage stays untrusted: whatever text the script returns, only the kernel decides.
- **A Python toolkit for scripts (`veriphy.toolkit`, a new subpackage).** It is pre-bound in every script.
  - **Lean emitters:** turn Sage objects and proof steps into well-formed, unhygienic Lean text over the goal's atoms. They cover rationals, polynomials, references to named hypotheses, `linear_combination` sums, `sq_nonneg` terms, `nlinarith`/`positivity`/`field_simp` hint lists, `calc` chains whose steps close by `ring`/`field_simp`/`norm_num`, `rw [show a = b by …]` steps, `by_cases`/`rcases` splits, witness tuples with side-goal tactics, and step sequences.
  - **Search primitives:** exact LP, Gröbner `lift`, factorization, real-root isolation with rational separating points, a product search that picks `nlinarith` hint products, SOS with exact rationalization (hinted squares, or a numeric SDP rounded and verified exactly), substitutions and normal forms, matrix decompositions checked by multiplication, and enumeration of sign and case splits.
- **Hint-oriented proofs.** The toolkit treats Lean automation plus Sage-found hints as a first-class proof shape. This is often far cheaper than a full certificate.
- **Derivation chains.** Sage proposes intermediate expressions, and each `calc` step is checked independently, so a failure points at the step that broke.
- **Presets.** The seven existing tactics (`sage_factor`, `sage_sos`, `sage_lincomb`, `sage_witness`, `sage_sum`, `sage_farkas`, `sage_exists`) keep their syntax, but are reimplemented as preset scripts on the toolkit. The scripts ship with the package, so the agent can read and adapt them. `sage_certify` is reimplemented the same way, as presets for its three families.
- **A persistent daemon session.** One daemon process per Lean process replaces the spawn per request. It is restarted on failure and stays disabled during replay. This removes about 2 s of start-up per call.
- **Feedback for iteration.** When `sage_run` fails, the error contains:
  - the script's own output;
  - the Lean text it produced;
  - Lean's elaboration error, located in that text.

  The agent fixes the script without guessing.
- **Agent workflow.** `prompts/prove.md` is rewritten around the loop: inspect the goal and problem, script with the toolkit, emit Lean, iterate on the combined feedback, then commit the replacement. The presets are positioned as shortcuts. `blocked-missing-tactic` becomes `blocked-missing-building-block`: a Sage capability or emitter the toolkit lacks.
- **BREAKING (report vocabulary only):** the `blocked-missing-tactic` report category is renamed. Tactic syntax is unchanged.

## Capabilities

### New Capabilities
- `certificates/script-tactic`: `sage_run`, from the script's inputs and Lean output to the axiom guard, emission, replay and combined feedback.
- `certificates/lean-emitters`: the toolkit's Lean text builders, with well-formedness and hygiene guarantees.
- `certificates/search-primitives`: the toolkit's exact search functions and their result contracts.
- `certificates/daemon-session`: the persistent daemon's lifecycle, recovery and isolation.

### Modified Capabilities
- `certificates/checker-families`: "Existing tactics preserve their interface". The replacements of the seven tactics may now come from preset scripts through the script-tactic pipeline, not only from a Lean-side checker family.
- `certificates/agent-certify`: "Agent workflow documents the route". The workflow now leads with building proofs through `sage_run` and the toolkit, and the report category is renamed.

## Impact

- **Lean:**
  - new `Veriphy/Tactic/SageRun.lean`;
  - `Veriphy/Kit/Family.lean` gains the axiom guard in `closeAndEmit`;
  - `Veriphy/Bridge.lean` gets a session (persistent process) in place of spawn-per-request;
  - `Veriphy/Kit/Problem.lean` serializes richer goal context (pretty-printed hypotheses and goal);
  - the seven tactic files and `SageCertify.lean` shrink to preset calls.
- **Python:**
  - a new `src/veriphy/toolkit/` subpackage (emitters, search), public, with doctests;
  - a new `src/veriphy/presets/` subpackage holding the preset scripts;
  - the oracle gains a `run` method that executes a script with the toolkit bound and returns Lean text;
  - the daemon serves many requests per process (already line-oriented).
- **Tests:** `VeriphyTest.lean` keeps every existing example and adds `sage_run` examples, including hint, calc, case-split, matrix and witness cases, and the guard rejecting `sorry` and `native_decide`. pytest covers each emitter and primitive.
- **Docs:** `prompts/prove.md`, `skills/prove/SKILL.md`, `docs/overview/user_guide.md`, `docs/development/index.md` and README.
- **Dependency:** builds on `package-and-distribute` (the `veriphy` package layout, the constitution, nox, CI), which must be merged first.
