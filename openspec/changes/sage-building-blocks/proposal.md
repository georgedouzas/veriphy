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
  - **Solvers:** only what is general and hard to get right per proof: an exact rational LP, and exact SOS from a numeric SDP (rounded, projected and verified exactly). Technique-specific search (Farkas rows, ideal lifts, product search, witnesses, root isolation, closed sums) is ordinary Sage code in the recipes' templates.
- **Hint-oriented proofs.** The toolkit treats Lean automation plus Sage-found hints as a first-class proof shape. This is often far cheaper than a full certificate.
- **Derivation chains.** Sage proposes intermediate expressions, and each `calc` step is checked independently, so a failure points at the step that broke.
- **No ready-made certificates.** The seven certificate tactics (`sage_factor`, `sage_sos`, `sage_lincomb`, `sage_witness`, `sage_sum`, `sage_farkas`, `sage_exists`) and `sage_certify` are removed, together with their daemon methods and the Lean-side reconstruction they needed. Every certificate is created per goal, by an agent or a human. Committed proofs are unaffected, because they contain only emitted replacements.
- **Procedures, templates and skills.** The value moves into how to build certificates:
  - one agent-agnostic recipe per technique, each with a decision rule, a fill-in `sage_run` template and its failure modes: ideal membership, Farkas, SOS, factorization, witnesses, hint search, `calc` derivations, case splits, matrix identities, sums by induction;
  - a `certify` skill for the build loop;
  - a recipe index in the `prove` playbook.
- **Certificate scripts in the caller's project.** Scripts are `.sage` files in the project's `certificates/` directory, run with `sage_run file "…"`. Each carries a header (name, technique, goal shape, description), and `sage -python -m veriphy.certificates list` makes them discoverable to any agent. The playbook has the agent reuse before writing and save after success. A shared certificate repository is future work in a separate repo.
- **Effectiveness gate.**
  - Every problem the removed tactics solved becomes a benchmark solved with `sage_run` following its recipe.
  - A fresh agent with only the skills must solve the whole benchmark from bare statements, with iterations and time recorded.
  - The change does not ship with any regression.
- **A persistent daemon session.** One daemon process per Lean process replaces the spawn per request. It is restarted on failure and stays disabled during replay. This removes about 2 s of start-up per call.
- **Feedback for iteration.** When `sage_run` fails, the error contains:
  - the script's own output;
  - the Lean text it produced;
  - Lean's elaboration error, located in that text.

  The agent fixes the script without guessing.
- **Agent workflow.** `prompts/prove.md` is rewritten around the loop: inspect the goal and problem, script with the toolkit, emit Lean, iterate on the combined feedback, then commit the replacement. `blocked-missing-tactic` becomes `blocked-missing-building-block`: a Sage capability or emitter the toolkit lacks.
- **BREAKING:** the certificate tactics, `sage_certify`, and the daemon methods `factor`, `sos`, `roots`, `lincomb`, `farkas`, `exists`, `sum` and `certify` are removed. The `blocked-missing-tactic` report category is renamed.

## Capabilities

### New Capabilities
- `certificates/script-tactic`: `sage_run`, from the script's inputs and Lean output to the axiom guard, emission, replay and combined feedback.
- `certificates/lean-emitters`: the toolkit's Lean text builders, with well-formedness and hygiene guarantees.
- `certificates/search-primitives`: the toolkit's exact search functions and their result contracts.
- `certificates/daemon-session`: the persistent daemon's lifecycle, recovery and isolation.

- `certificates/project-scripts`: certificate scripts stored in the caller's project, their header format, the catalog, and running them from a file.
- `certificates/procedures`: recipes, templates and skills for building certificates, and the benchmark showing they are at least as effective as the removed tactics.

### Modified Capabilities
- `certificates/checker-families`: the fixed Lean-side families and "Existing tactics preserve their interface" are removed (the tactics go).
- `certificates/agent-certify`: `sage_certify` is removed, and the workflow requirement now leads with creating certificates through `sage_run` and the procedures.
- `certificates/proof-reconstruction`: removed; Lean-side reconstruction is replaced by the Python emitters.
- `certificates/oracle-methods`: the `certify` method and the certificate-search methods are removed (their algorithms live on as toolkit primitives).
- `certificates/replay-check`: the hygiene regressions are expressed as `sage_run` examples.

## Impact

- **Lean:**
  - new `Veriphy/Tactic/SageRun.lean`;
  - `Veriphy/Kit/Family.lean` gains the axiom guard in `closeAndEmit`;
  - `Veriphy/Bridge.lean` gets a session (persistent process) in place of spawn-per-request;
  - `Veriphy/Kit/Problem.lean` serializes richer goal context (pretty-printed hypotheses and goal);
  - the seven tactic files, `SageCertify.lean` and most of `Kit/Build.lean` and the `Kit/Family.lean` checkers are deleted.
- **Python:**
  - a new `src/veriphy/toolkit/` subpackage (emitters, search), public, with doctests;
  - the oracle gains a `run` method that executes a script with the toolkit bound and returns Lean text;
  - the daemon serves many requests per process (already line-oriented).
- **Tests:** every existing example in `VeriphyTest.lean` is ported to `sage_run` following its recipe (the benchmark), and new `sage_run` examples are added for hint, calc, case-split and matrix proofs and for the guard rejecting `sorry` and `native_decide`. pytest covers each emitter and primitive. An agent benchmark run is recorded under `docs/development/`.
- **Docs and skills:** new `prompts/recipes/*.md` and `skills/certify/SKILL.md`; `prompts/prove.md`, `skills/prove/SKILL.md`, `docs/overview/user_guide.md`, `docs/development/index.md` and README are updated.
- **Dependency:** builds on `package-and-distribute` (the `veriphy` package layout, the constitution, nox, CI), which must be merged first.
