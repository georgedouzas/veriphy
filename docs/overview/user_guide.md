# User guide

To install Veriphy, see the [README](../index.md). To add a recipe or a building block, see
[Development](../development/index.md).

## How it works

Lean and a computer algebra system solve complementary problems. Sage computes quickly, but every result has to be
trusted, and wrong branch cuts, dropped solutions and simplifier bugs are real. Lean proves with kernel certainty but
has no comparable symbolic engine. Physics needs both.

Veriphy follows the skeptical approach (Harrison and Théry). Sage finds what is hard to find and easy to check, a short
script turns that into a Lean tactic block, and the kernel accepts it or rejects it. A certificate is worth computing
when finding is much harder than checking and an existing Lean checker accepts it (`ring1`, `linear_combination`,
`nlinarith`, `positivity`, `norm_num`, `decide`). Ideal membership, sums of squares, LP duality and witnesses are the
classic cases.

Sage, the bridge, the translator and the agent are all outside the trusted base:

- `sage_run` rejects `sorry` and any axiom beyond Lean's standard three, and replays the block from its printed text.
- Polynomials cross the bridge as structured term lists rather than strings, so Lean rebuilds terms instead of parsing
  CAS output. A mistranslation fails the tactic. It can't prove the wrong thing.
- Sage is needed only while writing proofs. `sage_run` offers a `Try this:` replacement, you commit that, and your
  proofs and CI need only Lean and mathlib.

Veriphy has no ready-made certificates. Real goals have a long tail, so it ships building blocks: the tactic, a toolkit
and a recipe per technique. Each certificate is written for the goal in hand and saved in your project.

## Skills

`research` calls `prove` for each claim, and `prove` calls `certify` for each computational core. The skills are thin
wrappers around plain markdown (`prompts/prove.md`, `prompts/certify.md`, `prompts/research.md`, `prompts/recipes/`), so
any agent can follow them.

### `prove`: from a statement to a proof

The input is a Lean statement, an informal statement, or a backlog item from a repo you supply, such as a
[Physlib](https://physlib.io) `informal_lemma`. If it refers to another library, the workspace has to require both that
library and Veriphy.

1. **Formalize.** Lean can't check that a formal statement means what the informal one said, so the agent runs two
   checks. It translates the statement back to English and compares. It then tests it with `symbolic_check` or
   `matrix_check`, or at ten or more random values satisfying the hypotheses. A counterexample stops the run.
2. **Compile.** The statement type-checks with `sorry` as the proof.
3. **Prove.** Cheapest route first: `simp`, `norm_num`, `positivity`, `nlinarith`, then premise search, then a
   certificate through `certify`. When the agent doesn't know what the proof even is, it can ask Sage (`solve`,
   `run_script`), but it has to prove in Lean whatever it takes from the answer. Missing lemmas get proved first.
   Missing definitions are flagged to you and never invented.
4. **Verify.** `lake build` from clean, with no `sorry` and no call to Sage in the final proof.

It ends with one of these, and leaves commits and PRs to you:

| Report | Meaning |
|---|---|
| `proved` | a verified Lean proof, naming the recipes and scripts used |
| `tested` | no certificate is feasible, and `sage_test` checked the claim at instances. The report gives the level and the counts |
| `statement-suspect` | the numeric test contradicted the claim, and the report gives the counterexample |
| `blocked-library-gap` | the statement needs theory that doesn't exist yet, named in the report |
| `blocked-missing-building-block` | the toolkit lacks a Sage computation or a Lean emitter, named in the report |

### `certify`: one goal, one certificate

It inspects the goal, reuses a saved script if one fits, and otherwise adapts a recipe. It then iterates on Lean's
errors until the block is accepted. Working scripts stay in `.veriphy/certificates/`, where any goal of the same shape
can reuse them. See [Building proofs with `sage_run`](#building-proofs-with-sage_run).

### `research`: a paper or chapter as a whole

`research` checks a draft and doesn't write your prose. A typical use is to run it on each chapter as it stabilizes, and
again after each substantial edit.

1. **Extract.** The agent writes claims, conventions, concepts and dependencies to
   `.veriphy/graph/sources/<source>.agent.ttl`. It never writes to a `.human.ttl` file. Confirming an assertion is your
   act.
2. **Validate.** `validate` checks the file against the SHACL shapes. A clean report means the file is complete, not
   that it is right.
3. **Triage.** Each claim with a computable form is tested numerically under the conventions it assumes. A
   counterexample makes it `suspect`, and a convention clash is a common cause. The rest go to `recipe`, `test`
   (`sage_test`) or `formalize` (needs definitions or theory you don't have yet).
4. **Prove.** In dependency order, each claim goes through `prove` with its graph slice as context, and is linked to its
   Lean claim with `formalizedBy`.
5. **Export.** `#veriphy_graph <prefix>` writes the levels and dependencies Lean knows.
6. **Reason.** `reason` derives the consequences and `oo-horn` checks the run. `excludes`, `clashes`, `levels` and
   `appendix` then build the report.
7. **Report.** You get the appendix and, for each claim, its group and effective level, along with every clash, suspect
   and capped claim. A claim isn't called proved below `lean-proof`, and an unchecked run isn't called checked.

The appendix goes in the paper with `--format latex`. Your reader sees the level of each claim, what caps it, the
checker's verdict and the command that rechecks the run. Before changing a convention midway, run `impact` and `plan
--against HEAD` to see what the change reaches.


## Your project

Veriphy keeps its files under `.veriphy/` at the Lean workspace root. Commit it with your proofs.

| Directory | Holds |
|---|---|
| `.veriphy/certificates/` | certificate scripts |
| `.veriphy/translations/` | your translation and rewrite entries |
| `.veriphy/lean/` | Lean files copied from Veriphy, such as recipe assets |
| `.veriphy/coverage/` | coverage reports |
| `.veriphy/tests/` | records written by `sage_test` |
| `.veriphy/graph/` | the research claim graph: `sources/`, `lean/` and `runs/` |

Projects from Veriphy 0.1.0 keep scripts in a top-level `certificates/`. They still work, and the catalog prints the
command that moves them.

Some recipes need Lean assets. Copy them from `assets/VeriphyAssets/` in the Veriphy repository to
`.veriphy/lean/VeriphyAssets/`, and declare the library once in `lakefile.toml`:

```toml
[[lean_lib]]
name = "VeriphyAssets"
srcDir = ".veriphy/lean"
```

| Asset | States | Recipe |
|---|---|---|
| `CoordinateGeometry.lean` | Christoffel symbols, curvature, Killing vectors and forms in a chart | `coordinate_geometry` |
| `FusionData.lean` | multiplicity-free fusion data, pentagon and hexagon equations, gauge transformations | `fusion_category` |

Environment variables:

| Variable | Effect |
|---|---|
| `VERIPHY_SAGE_CMD` | the `sage` executable, if it isn't on `PATH` |
| `VERIPHY_SAGE_TIMEOUT` | seconds allowed per Sage request (default 150) |
| `VERIPHY_HOME` | your Veriphy clone, when the skills are copied by hand |
| `VERIPHY_GRAPH_SETUP` | `off` stops the graph fetching or building anything |
| `VERIPHY_OO_HORN` | use this `oo-horn` binary |

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

The steps are the ones `certify` follows:

1. **Inspect.** `sage_run "print(goal_kind, goal); print(hyps); print(atoms); proof = 'sorry'"` fails on purpose, and
   the error shows the problem.
2. **Reuse.** `sage -python -m veriphy.certificates list` shows your saved scripts, and `show <name>` prints one. A
   saved script runs unchanged on any goal of the same shape.
3. **Adapt.** Otherwise copy a template from `prompts/recipes/templates/` to `.veriphy/certificates/` and edit the lines
   marked `EDIT`.
4. **Iterate.** A failure shows the script's output, the Lean text and Lean's error together.
5. **Commit** the emitted replacement, and keep the script.

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
| commutators of explicit or differential operators; gamma-matrix identities | `operator_identity` |
| Christoffel symbols, Killing vectors, exact forms, contractions in coordinates | `coordinate_geometry` |
| hypergeometric sums (binomials, factorials): WZ pairs, Gosper | `wz_certificate` |
| closed forms of linear recurrences | `recurrence` |
| rational bounds on `exp`, `log`, `sin`, `cos`, `π` at explicit points | `certified_bound` |
| a real root or eigenvalue in an explicit interval | `root_isolation` |
| `∫ x in a..b, f x = v` with an elementary antiderivative | `definite_integral` |
| `LinearIndependent K v`, its negation, spans equal to spans or kernels | `independence` |
| `Matrix.rank A = r` and its bounds, for an explicit matrix | `matrix_rank` |
| `Module.finrank K V = n` for spans, intersections, kernels, product spaces | `dimension` |
| `¬ ∃ f : V →ₗ[K] W, …`: a map that is not linear or bilinear | `nonlinearity` |
| the signature of an explicit symmetric matrix (`Veriphy.Linear.HasSignature`) | `signature` |
| no certificate is feasible: test the claim at instances (`sage_test`) | `test_fallback` |
| fusion or braided fusion data (pentagons, hexagons, gauges), naturality of an intertwiner | `fusion_category` |
| graded brackets, super-Jacobi (`sl(m\|n)`, `osp`, `D(2,1;α)`, `G(3)`, `F(4)`) | `lie_superalgebra` |
| (Physlib) an explicit matrix `∈ lorentzAlgebra` | `physlib/lorentz_algebra` |
| (Physlib) a commutator of ladder operators, positions and momenta | `physlib/ladder_operators` |

While formalizing, you can also ask Sage for guidance with `symbolic_check`, `matrix_check`, `solve` and `run_script`.
Their output is never copied into a proof.

## Extending the translation

Veriphy translates Lean terms to Sage through tables in three namespaces, resolved in order:

1. `mathlib`, the core: field arithmetic, elementary and inverse trigonometric functions, `rpow`, `logb`, sums and
   products, integer functions, derivatives, matrices and polynomials;
2. library packs shipped with Veriphy, such as `physlib`, active only when the library is imported;
3. your project's entries in `.veriphy/translations/*.json`.

A later namespace never overrides an earlier one. `#veriphy_tables` prints the namespaces in force, `#veriphy_translate
t` shows how a term translates, and `sage -python -m veriphy.translations list` lists your project's entries (`--all`
adds the core and the packs).

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

A function entry names the Lean constant, the Sage function, the number of explicit arguments, the argument and result
types, its domain conditions (`ne`, `nonneg` or `pos` on argument `#i`, or `le` between two sides) and an example term.
A rewrite entry names a lemma, the functions it applies to, its direction, its side conditions (with `#i` for the
argument a Sage `pattern` binds to `wi`) and an example signature such as `(x : ℝ) (hx : x ≠ 0) : Real.Gamma (x + 1) = x
* Real.Gamma x`. Check every entry with:

```lean
#veriphy_check_translations
```

It translates each function's example, renders it back, proves the two equal, and closes each rewrite's example with its
lemma, reporting each entry as passed or failed.

### Types, casts and integer functions

Sage computes over one symbolic ring, and Lean doesn't. The translation records each subterm's Lean type, so a script's
result renders back at the right type: `symbolic(e, problem, lean_type='ℕ')` writes casts where the goal has them,
`typed(e, 'ℕ')` marks a natural-number subterm, and natural subtraction and division keep Lean's meaning: `a - b` is
plain subtraction when a hypothesis gives `b ≤ a` and `max(a - b, 0)` otherwise, and `/` and `%` need a positive
divisor. `Nat.factorial`, `Nat.choose`, `Nat.gcd`, `Int.floor`, `Int.ceil`, `max` and `min` translate to Sage's
`factorial`, `binomial`, `gcd`, `floor`, `ceil`, `max_symbolic` and `min_symbolic`.

`#veriphy_coverage` measures which statements of a corpus translate without opaque atoms, and ranks the heads that
don't. Use it to decide which entries to add.

## Unknown functions and differential equations

A local function `x : ℝ → ℝ` (or of a type that views as `ℝ`, `ℂ` or `ℚ`, such as Physlib's `Time`) translates to a Sage
symbolic function `F_x`, and `deriv x t`, `deriv (deriv x) t` and a pack's derivative notations (`∂ₜ x t`) to its
derivatives. A script sees:

- `problem.functions`, the unknown functions;
- `problem.definitions`, hypotheses `hx : x = fun s => …` that define one explicitly;
- `problem.exists_function`, a goal `∃ x, (∀ t, ODE) ∧ x t₀ = y₀ ∧ …`, split into its conjuncts.

The `ode_solution` recipe proves that an explicit function solves the equation, by differentiation rather than by
trusting Sage. `desolve` proposes the solution. The proof states each derivative of it as a fact, proved by mathlib's
derivative lemmas, rewrites the equation with them and closes it by `ring` or `field_simp`:

```lean
example (ω x₀ v₀ : ℝ) (hω : ω ≠ 0) :
    ∃ x : ℝ → ℝ, (∀ t, deriv (deriv x) t + ω ^ 2 * x t = 0) ∧ x 0 = x₀ ∧ deriv x 0 = v₀ := by
  sage_run file "ode_solution.sage"
```

A wrong solution fails with the equation Lean could not close, such as `Real.exp (t * 3) * 9 = Real.exp (t * 3) * 6`.

## Large checks: `VeriphyCheck`

Entrywise proofs stop scaling at a few dozen entries. `VeriphyCheck` has checkers that run in the kernel by `decide
+kernel`, each with a soundness theorem that gives the mathlib statement:

| Checker | Proves |
|---|---|
| `mul_eq_of_check`, `ofLists_mul` | `A * B = C` for explicit matrices (32×32 integer products in about 5 s) |
| `bracket_eq_of_check`, `commute_of_check` | `⁅A, B⁆ = C`, `A * B = B * A` |
| `trace_eq_of_check`, `eq_of_check` | `trace A = c`, `A = B` |
| `jacobi_of_check`, `bracket_self_of_check` | the Jacobi identity and antisymmetry of a structure-constant table |
| `prime_of_pratt` | `Nat.Prime p`, from a Pratt certificate |

The toolkit picks entrywise proofs for small goals and checkers for large ones. `VeriphyCheck` imports only mathlib. If
your project can't depend on Veriphy, as with a mathlib or Physlib contribution, copy in the bundle that `python3
scripts/bundle_check.py` writes.

## When no certificate exists: `sage_test` and verification levels

Some claims have no certificate, such as a statement about every matrix or in every dimension. Their proofs are mathlib
proofs, and Veriphy tests them instead:

```lean
theorem traceDouble (n : ℕ) (A : Matrix (Fin n) (Fin n) ℚ) : Matrix.trace (A + A) = 2 * Matrix.trace A := by
  rw [Matrix.trace_add]; ring

sage_test traceDouble file "trace_double_test.sage"
```

The script picks values for every binder. The kernel checks each instance by computation, or Sage evaluates it exactly
(or by intervals) when Lean can't state it. Instances come from the claim's statement, never its proof. A run needs
three accepted instances, one of them an edge case. It writes `.veriphy/tests/<claim>.json`, which `sage -python -m
veriphy.certificates tests` lists and `tests --rerun <claim>` reruns.

Every claim has one of five levels, highest first:

| Level | What was checked | Builds without Sage |
|---|---|---|
| `certificate` | a recipe built the proof, which the kernel checked | yes |
| `lean-proof` | a complete Lean proof that no recipe built, on the standard axioms alone | yes |
| `kernel-test` | the kernel checked the claim at instances, each by computation | yes |
| `oracle-test` | Sage evaluated the claim at some instances, exactly or by intervals of at least 53 bits | the record is kept |
| `none` | no checked proof and no test: a stated proposition, or a proof that uses `sorry` or another axiom | |

`#veriphy_levels MyProject` lists the level of every theorem under a prefix. A test is never reported as a proof.

## The research claim graph

Veriphy's tactics check one claim at a time. The graph checks how the claims of a paper or research program fit
together: which conventions each one assumes, which claims it rests on, and how verified it is once its weakest
dependency counts.

The reasoner is untrusted. `oo-horn`, a verified Lean checker from [Open
Ontologies](https://github.com/fabio-rovai/open-ontologies) that shares no code with Veriphy, accepts or refuses every
run, and Veriphy reports a graph conclusion only with the verdict the checker printed. The `research` skill drives the
commands below, and you can run any of them yourself.

### Setup

```bash
sage -pip install 'veriphy[graph]'
```

The first command that needs them sets up the reasoner and `oo-horn` from the pinned Open Ontologies release, says what
it fetches or builds, and caches it in `~/.cache/veriphy/open-ontologies/v2.1.0`:

- the release is cloned with `git`, and refused unless its commit is the pinned one
- the reasoner is imported from the release's source, so nothing is installed into Python at run time
- on Linux x86_64 `oo-horn` is the release's prebuilt binary, kept only if its SHA-256 matches both the pinned hash and
  the hash the release lists, and only if it runs
- elsewhere `oo-horn` is built once with the release's Lean toolchain through `elan`, which takes minutes

`sage -python -m veriphy.graph checker build` does the same ahead of time. `VERIPHY_GRAPH_SETUP=off` forbids automatic
setup, for offline machines and CI. Without a checker, every result is labelled `unchecked`, with the command that sets
it up.


### Sources

Each source has one Turtle file per provenance in `.veriphy/graph/sources/`: `chapter9.agent.ttl` for what an agent
extracted, and `chapter9.human.ttl` for what a person wrote or confirmed.

```turtle
@prefix vp: <urn:veriphy:vocabulary#> .
@prefix : <urn:veriphy:source:chapter9#> .

:half a vp:Convention ; vp:conventionFor "killing-normalization" ;
    vp:statement "Tr(T^a T^b) = 1/2 δ^ab" ; vp:realizedBy <urn:veriphy:lean:KK.killingHalf> .
:lemma-5.2 a vp:Claim ; vp:statedIn :chapter9 ; vp:statement "The Killing form is -3/2 δ." ;
    vp:assumes :half ; vp:formalizedBy <urn:veriphy:lean:KK.killing_form_value> .
:thm-9.1 a vp:Claim ; vp:statedIn :chapter9 ; vp:statement "The vacuum is stable." ;
    vp:uses :lemma-5.2, <urn:veriphy:source:arXiv:0808.3236#thm-2> .
```

A claim from another paper is a node of that paper's source, named by its arXiv identifier or DOI. `owl:sameAs` says two
sources mean the same concept.

```bash
sage -python -m veriphy.graph vocabulary                            # print the vocabulary
sage -python -m veriphy.graph validate                              # check the files and shapes
sage -python -m veriphy.graph confirm chapter9 lemma-5.2 assumes half   # move one triple to the human file
```

`validate`'s SHACL report is a measurement, not a checked conclusion.

### The Lean export

`#veriphy_graph KK` writes every theorem and definition under `KK` to `.veriphy/graph/lean/KK.nt`, with their levels,
statements and dependencies. These come from the Lean environment, not from extraction. Use `formalizedBy` to link a
prose claim to its Lean claim, and `realizedBy` to link a convention to the Lean definition behind it.

### Reasoning and verdicts

`sage -python -m veriphy.graph reason` derives the consequences and writes a certificate under
`.veriphy/graph/runs/<digest>/`: the asserted triples, the rules, one derivation line per conclusion, and a digest.
Veriphy states the meaning of its vocabulary as OWL axioms that the checker's built-in rules evaluate. So every run uses
the built-in rule table unchanged, and an accepted run earns `entailed` through the theorem
`OOCert.entails_of_builtin_horn`: every conclusion holds in every model of the asserted triples.

| Status | Meaning |
|---|---|
| `entailed` | the checker accepted the run, and the verdict is its own word |
| `rejected` | the checker refused a derivation line, and names it |
| `unchecked` | no checker was found or it didn't finish, and no conclusion is reported as checked |
| `incomplete` | the run stopped before its fixpoint |

`sage -python -m veriphy.graph recheck .veriphy/graph/runs/<digest>` checks a stored run again without the reasoner, and
says whether the current graph still asserts the same triples. The commands exit with status 3 when the checker didn't
accept the run.


### Levels

A claim's own level comes from the export or from the Lean claim that formalizes it, and is `none` otherwise. Its
effective level is the lowest level among everything it uses, directly or not. `sage -python -m veriphy.graph levels
--source chapter9` prints:

```
| claim | own | effective | capped by | Lean |
|---|---|---|---|---|
| lemma-5.2 | certificate | certificate |  | KK.killing_form_value |
| lemma-8.4 | oracle-test | oracle-test |  | KK.curvature_pos |
| thm-9.1 | certificate | oracle-test | lemma-8.4 | KK.vacuum |
```

### Convention impact and plans

`sage -python -m veriphy.graph impact chapter9 half` lists every claim that assumes the convention `half`, directly or
through its dependencies, with the chain that reaches it and its Lean name. Before changing a convention, edit the
source file and compare against the last commit:

```bash
sage -python -m veriphy.graph plan --against HEAD
```

The plan reasons over both graphs, has both runs checked, and lists the assertions you changed and the consequences
added and removed: `assumes` triples, level caps and clashes. Editing only a statement's text gives one changed
assertion and no changed consequence.

### Clashes

Conventions of the same aspect exclude each other. `sage -python -m veriphy.graph excludes` proposes the `excludes`
triples, and `--confirm` writes them as human assertions. `sage -python -m veriphy.graph clashes` then reports every
claim or concept with two checked `assumes` conclusions whose conventions exclude each other, including assumptions
inherited across papers.

### Slices

`sage -python -m veriphy.graph slice chapter9 thm-9.1` prints what an agent needs to formalize `thm-9.1`: its statement,
the statements and levels of the claims it uses, and each convention it assumes with the Lean definition behind it.
Veriphy reasons over the slice alone, has that run checked, and offers the slice only if it keeps every consequence
about the claim.

### The verification appendix

`sage -python -m veriphy.graph appendix chapter9 --format latex` writes `.veriphy/graph/appendix/chapter9.tex`: a row
per claim with its own and effective levels, what caps it, its Lean name and its clashes, and a paragraph with the run,
the verdict, the provenance of the assertions and the command that rechecks it. An unchecked run says so in the
paragraph and the table header. `--format markdown` writes the same as Markdown.


### Limits

- The graph doesn't check that a prose claim and its Lean statement say the same thing. `formalizedBy` is an assertion,
  and reports count where each assertion came from.
- A checked conclusion is only as good as the asserted triples. A bad extraction gives a faithfully wrong conclusion.
- No clash found is the reasoner's result, not a checked conclusion. A Horn certificate proves what was derived, not
  what wasn't.
