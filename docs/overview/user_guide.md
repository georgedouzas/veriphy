# User guide

How Veriphy works and why it is built this way. The design was distilled from
the founding discussion (2026-10-07/08), and it records what was decided and
*why*, so future changes argue against the original reasoning rather than
rediscovering it. To add a recipe or a toolkit building block, see
[Development](../development/index.md).

## The problem

Lean 4 and a CAS (SageMath) solve complementary problems: a CAS *computes*
answers fast but every result is trusted (wrong branch cuts, dropped
solutions, simplifier bugs are real failure modes); Lean *proves* statements
with kernel certainty but has nothing like a CAS's symbolic engine. Physics
needs both: heavy computation and, for long error-prone derivations,
certainty.

## Core decision: the skeptical architecture

Sage is an **untrusted oracle**. Every Sage result must return a
**certificate** that Lean reconstructs into a kernel-checked proof, or the
tactic fails. This is the classical "skeptic's approach" (Harrison/Théry);
mathlib's `polyrith` already applies it to one problem class, with Sage
specifically, via a remote server.

Consequences:

- Sage, the bridge, the translator, and any AI in the loop are all outside the
  trusted base. A bug or hallucination can waste time, never produce a false
  theorem.
- **Sage is authoring-time only.** Every tactic emits a `Try this:`
  replacement; committed proofs check with vanilla Lean + mathlib, no Sage
  installed. CI never needs the daemon. (Verified by replaying emitted proofs
  with Sage off `PATH`.)
- Polynomials cross the bridge as **structured term lists** (coefficient +
  exponent vector), not syntax strings — the Lean side reconstructs terms
  instead of parsing CAS output, eliminating most translation brittleness. A
  mistranslation fails a tactic; it cannot prove the wrong thing.

## Relationship to LeanSage

[LeanSage](https://github.com/oOo0oOo/LeanSage) (discovered mid-design) solved
the Lean↔Sage *communication* problem (a seven-stage MathAST pipeline) but its
flagship `by sage` mode closes goals with `sorry` — the trusting oracle,
unusable for mathlib/Physlib contributions. Veriphy deliberately occupies the
complement: certification and the agent skill. Where practical, certificate
checkers should be contributed upstream rather than duplicated.

Veriphy's symbolic translation (`Veriphy/Kit/Symbolic.lean`) ports LeanSage's
coverage tables, with credit (MIT License): rational functions, `sqrt`, `exp`,
`log`, trigonometric functions, `abs`, `pi`, `I`, range sums, matrix literals,
`det`, `trace` and polynomial evaluation reach scripts as Sage symbolic
expressions, together with the domain conditions they need (nonzero
denominators, nonnegative `sqrt` arguments, positive `log` arguments). The
toolkit renders Sage results back to Lean through an explicit function table,
and anything outside it is rejected with an error naming it.

## Scope boundary: building blocks, not certificates

A certificate is worth computing in Sage where three things coincide: (1) finding is much harder than checking,
(2) there is a certificate format, and (3) an existing Lean checker accepts it (`ring1`, `linear_combination`,
`nlinarith`, `positivity`, `norm_num`, `decide`). The classical examples are ideal membership, factorization, sums of
squares, LP duality and witnesses.

Veriphy first shipped one tactic per certificate (`sage_factor`, `sage_sos`, `sage_lincomb`, `sage_farkas`, …).
That covered only the cases someone had already solved, and every new shape needed a Lean metaprogram, a daemon
method and a release. Because real goals have a long tail, Veriphy now ships the **building blocks** instead and
leaves each **certificate** to whoever needs it:

- **`sage_run`** runs a Sage script against the goal and checks the Lean block it returns. Only the kernel decides.
  The block must not use `sorry` or non-standard axioms, and it is replayed from its printed text.
- **The toolkit** binds the goal as a `problem`, provides emitters that write well-formed Lean (sums of weighted
  hypotheses, `sq_nonneg` terms, `nlinarith` hints, `calc` chains, case splits, witnesses, refutations) and adds two
  exact solvers that are hard to get right per proof: a rational LP, and SOS from a numeric SDP rounded and verified
  exactly.
- **Recipes** carry the knowledge the old tactics hard-coded. Each technique has its decision rule, a tested
  template, a worked example and its failure modes.
- **Skills** (`prove`, `certify`) run the loop: inspect, reuse a saved script, or adapt a recipe, then run, iterate
  and save.

Scripts belong to the project being proved, under its `.veriphy/` directory, and the catalog makes them reusable.
Every problem the old tactics solved is in the benchmark (`VeriphyTest/Benchmark.lean`), solved by the recipes.
`blocked-missing-building-block` now means the toolkit cannot express a proof: a missing Sage primitive or Lean
emitter, named in the report.

## Project layout

Everything Veriphy creates or reads in your project lives under `.veriphy/` at the Lean workspace root (the directory
with the root lakefile):

| Directory | Holds |
|---|---|
| `.veriphy/certificates/` | certificate scripts, run with `sage_run file "<name>.sage"` |
| `.veriphy/translations/` | your project's translation and rewrite entries |
| `.veriphy/lean/` | Lean files copied from Veriphy, such as recipe assets |
| `.veriphy/coverage/` | coverage reports |

Commit `.veriphy/` with your proofs. The proofs themselves stay in your own Lean files. Lean files copied into
`.veriphy/lean/` build through a library you declare once in `lakefile.toml`:

```toml
[[lean_lib]]
name = "VeriphyAssets"
srcDir = ".veriphy/lean"
```

Projects created with Veriphy 0.1.0 keep scripts in a top-level `certificates/`. The catalog still lists them, warns,
and prints the command that moves them: `mkdir -p .veriphy && git mv certificates .veriphy/certificates`.

## Extending the translation

Veriphy translates Lean terms to Sage through tables in three namespaces, resolved in order:

1. `mathlib`, the core: field arithmetic, elementary and inverse trigonometric functions, `rpow`, `logb`, sums and
   products, integer functions, derivatives, matrices and polynomials;
2. library packs shipped with Veriphy, such as `physlib`, active only when the library is imported;
3. your project's entries in `.veriphy/translations/*.json`.

A later namespace never overrides an earlier one. `#veriphy_tables` prints the namespaces in force,
`#veriphy_translate t` shows how a term translates, and `sage -python -m veriphy.translations list` lists your
project's entries (`--all` adds the core and the packs).

When a function stays an atom, add an entry. For `Real.arcosh`, which Sage calls `arccosh` and which needs `1 ≤ x`:

```json
{
  "functions": [
    {"lean": "Real.arcosh", "sage": "arccosh", "arity": 1, "types": ["ℝ"], "result": "ℝ",
     "conditions": [{"kind": "le", "lhs": "1", "rhs": "#0"}],
     "example": "Real.arcosh x"}
  ]
}
```

A function entry names the Lean constant, the Sage function, the number of explicit arguments, the argument and
result types, its domain conditions (`ne`, `nonneg` or `pos` on argument `#i`, or `le` between two sides) and an
example term. A rewrite entry names a lemma, the functions it applies to, its direction, its side conditions (with
`#i` for the argument a Sage `pattern` binds to `wi`) and an example signature such as
`(x : ℝ) (hx : x ≠ 0) : Real.Gamma (x + 1) = x * Real.Gamma x`. Check every entry with:

```lean
#veriphy_check_translations
```

It translates each function's example, renders it back, proves the two equal, and closes each rewrite's example
with its lemma, reporting each entry as passed or failed.

### Types, casts and integer functions

Sage computes over one symbolic ring; Lean does not. The translation records each subterm's Lean type, so a script's
result renders back at the right type: `symbolic(e, problem, lean_type='ℕ')` writes casts where the goal has them,
`typed(e, 'ℕ')` marks a natural-number subterm, and natural subtraction and division keep Lean's meaning: `a - b` is
plain subtraction when a hypothesis gives `b ≤ a` and `max(a - b, 0)` otherwise, and `/` and `%` need a positive
divisor. `Nat.factorial`, `Nat.choose`, `Nat.gcd`, `Int.floor`, `Int.ceil`, `max` and `min` translate to Sage's
`factorial`, `binomial`, `gcd`, `floor`, `ceil`, `max_symbolic` and `min_symbolic`.

## Unknown functions and differential equations

A local function `x : ℝ → ℝ` (or of a type that views as `ℝ`, `ℂ` or `ℚ`, such as Physlib's `Time`) translates to a
Sage symbolic function `F_x`, and `deriv x t`, `deriv (deriv x) t` and a pack's derivative notations (`∂ₜ x t`) to
its derivatives. A script sees:

- `problem.functions`, the unknown functions;
- `problem.definitions`, hypotheses `hx : x = fun s => …` that define one explicitly;
- `problem.exists_function`, a goal `∃ x, (∀ t, ODE) ∧ x t₀ = y₀ ∧ …`, split into its conjuncts.

The `ode_solution` recipe proves that an explicit function solves the equation, by differentiation rather than by
trusting Sage. `desolve` proposes the solution; the proof states each derivative of it as a fact, proved by
mathlib's derivative lemmas, rewrites the equation with them and closes it by `ring` or `field_simp`:

```lean
example (ω x₀ v₀ : ℝ) (hω : ω ≠ 0) :
    ∃ x : ℝ → ℝ, (∀ t, deriv (deriv x) t + ω ^ 2 * x t = 0) ∧ x 0 = x₀ ∧ deriv x 0 = v₀ := by
  sage_run file "ode_solution.sage"
```

A wrong solution fails with the equation Lean could not close, such as `Real.exp (t * 3) * 9 = Real.exp (t * 3) * 6`.

## Large checks: `VeriphyCheck`

Entrywise proofs (`ext i j; fin_cases …; simp`) stop scaling at a few dozen entries. `VeriphyCheck` is a small
library of checkers that run in the kernel by `decide +kernel` (never `native_decide`), each with a soundness
theorem that turns a `true` result into the mathlib statement:

| Checker | Proves |
|---|---|
| `mul_eq_of_check`, `ofLists_mul` | `A * B = C` for explicit matrices (32×32 integer products in about 5 s) |
| `bracket_eq_of_check`, `commute_of_check` | `⁅A, B⁆ = C`, `A * B = B * A` |
| `trace_eq_of_check`, `eq_of_check` | `trace A = c`, `A = B` |
| `jacobi_of_check`, `bracket_self_of_check` | the Jacobi identity and antisymmetry of a structure-constant table |
| `prime_of_pratt` | `Nat.Prime p`, from a Pratt certificate |

The toolkit emits these proofs (`matrix_goal_proof`, `packed_product_certificate`, `prime_certificate`,
`structure_constants_term`), choosing entrywise proofs for small goals and checkers for large ones. `VeriphyCheck`
imports only mathlib. A project that must not depend on Veriphy, such as a mathlib or Physlib contribution, copies
the bundle `python3 scripts/bundle_check.py` writes into `.veriphy/lean/`. Polynomial identities stay with mathlib's
`ring` and `linear_combination`, which are faster than a kernel normalizer.

## Building proofs with `sage_run`

```lean
-- the script sees the goal as `problem` (x0 = a, x1 = b) and returns a Lean tactic block
example (a b : ℝ) : 0 ≤ a ^ 2 * b ^ 2 - 2 * a * b + 1 := by
  sage_run "proof = nlinarith([sq_nonneg(x0*x1 - 1, problem)])"
-- Try this: nlinarith [sq_nonneg (a * b - 1)]

-- a saved script from the project, here a Farkas refutation found by an exact LP
example (x y : ℚ) (h1 : x + y ≤ 1) (h2 : x - y = 3) (h3 : 0 ≤ y) : False := by
  sage_run file "farkas.sage"
```

The steps are:

1. **Inspect.** `sage_run "print(goal_kind, goal); print(hyps); print(atoms); proof = 'sorry'"` fails on purpose,
   and its error shows the problem.
2. **Reuse.** `sage -python -m veriphy.certificates list` shows the project's saved scripts.
3. **Adapt.** Otherwise copy a recipe template from `prompts/recipes/templates/` to `.veriphy/certificates/` and
   adapt the lines marked `EDIT`.
4. **Iterate.** A failure shows the script's output, the Lean text and Lean's error together.
5. **Commit** the emitted replacement, which builds without Sage, and keep the script.

| Goal shape | Recipe |
|---|---|
| `a = b` from equality hypotheses | `ideal_membership` |
| `False`, `a ≤ b`, `a < b` linear in the hypotheses | `farkas` |
| `0 ≤ p`, `p` polynomial | `sos` |
| polynomial inequality needing products or squares | `hint_search` |
| `lhs = rhs` where the factored `lhs` helps | `factor_rewrite` |
| `∃ x₁ … xₙ, …` with rational values | `witness` |
| `∑ k ∈ Finset.range n, f k = F n` | `sum_induction` |
| long manipulation through intermediate forms | `calc_derivation` |
| easy on each side of a condition | `case_split` |
| identity between explicit matrices | `matrix_identity` |
| `lhs ≤ rhs` with divisions (rational functions) | `rational_inequality` |
| identity of `exp`, `log`, `sqrt`, `sin`, `cos`, `cosh`, … by named lemmas | `transcendental_rewrite` |
| `!![…]` identity, `det` or `trace` written in the goal | `matrix_from_goal` |
| `deriv (fun x => f x) a = v` with an explicit `f` | `derivative` |
| ODE in `deriv x`, `x` given by `hx : x = fun s => …` or asked for by `∃ x` | `ode_solution` |
| bracket relations, Casimirs, Cartan-matrix facts of explicit matrices | `lie_structure` |
| representations, decompositions, branching, Clebsch-Gordan | `representation` |
| `False` from nonlinear polynomial hypotheses; `p = 0` from `pᵏ` in the ideal | `infeasibility` |
| `Nat.Prime p` for a large explicit `p` | `primality` |
| Smith or Jordan form, diagonalization of an explicit matrix | `matrix_normal_form` |
| `NormedSpace.exp` of an explicit matrix (nilpotent, diagonalizable) | `matrix_exponential` |
| graded brackets, super-Jacobi (`sl(m\|n)`, `osp`, `D(2,1;α)`, `G(3)`, `F(4)`) | `lie_superalgebra` |
| (Physlib) an explicit matrix `∈ lorentzAlgebra` | `physlib/lorentz_algebra` |

## Product decision: a pure tool

Veriphy is a tool, not a campaign:

- **The caller supplies the target** (a formal Lean statement, an informal
  statement, or a backlog item in a repo the caller provides — e.g. a
  [Physlib](https://physlib.io) `informal_lemma`). No target library is
  cloned, wired, or assumed by the repo.
- **The caller owns the outcome.** The `prove` skill ends at a report —
  `proved` / `blocked-library-gap` / `blocked-missing-building-block` /
  `statement-suspect` — and never opens PRs, keeps ledgers, or commits beyond
  what was asked. (An earlier design embedded a Physlib stub ledger and PR
  step; both were removed for this reason.)
- Workspaces wiring Veriphy to a target library (a lakefile requiring both)
  are created on demand and are disposable.

## The AI's role

The agent (any agent — the skill logic is plain markdown in
`prompts/prove.md`) proposes formalizations and proofs; Lean checks them. Two
lie detectors guard the one step the kernel cannot check — that the *formal
statement means what the informal one said*: round-trip informalization, and
numeric evaluation of the statement in Sage at random parameter values before
any proof attempt. Definitions are never invented by the agent; they are
flagged to the caller.

## Validation

The pipeline ran end to end once during design (2026-10-08): Physlib's
informal lemma `isBounded_iff_of_𝓵_zero` (Higgs potential bounded iff
`μ2 ≤ 0` when `𝓵 = 0`) was formalized, numerically validated, proved
(~15 lines, one compile-fix round), and kernel-checked. Notably it needed *no*
Sage tactic — evidence that easy backlog items clear with plain mathlib
automation, and the `sage_*` tactics earn their keep on the computational
residue.

## Distribution

Veriphy ships through three channels, all cut from one git tag `X.Y.Z`:

| Channel | Artifact | How a user gets it |
|---|---|---|
| Lake | the Lean library at the repository root | `[[require]] … rev = "X.Y.Z"` |
| PyPI | the `veriphy` package, the Sage daemon | `sage -pip install veriphy` |
| Claude plugin | the `prove` skill and playbook | `claude plugin install veriphy@veriphy` |

Versioning is left to hatch-vcs: the tag is the only place a version is
written, and nothing compares the Lean and Python versions at run time. The
daemon runs inside an existing SageMath (Sage is never a declared dependency),
and the tactics start it as `sage -python -m veriphy.sage_server`. Releases are
gated by CI: a Lean job without Sage, the Python checks, and an integration job
in a SageMath container that installs the built wheel and runs the full tactic
suite with replay on.
