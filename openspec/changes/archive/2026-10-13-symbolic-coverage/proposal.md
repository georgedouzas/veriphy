# Proposal

## Why

Veriphy 0.1.0 handles goals whose hard part is polynomial or elementary algebra: field arithmetic, the elementary `Real`/`Complex` functions, range sums, small matrices. Research mathematics and physics need far more. Representation theory, Lie superalgebras, differential equations, operator algebras, curvature, summation identities, certified numerics and fusion categories all have the same shape: a computation that is expensive to find and cheap to check. That shape is what Veriphy's architecture is built for.

Three things stand in the way:
- the translation sees too little of these goals;
- there is no certificate format or checker for these computations;
- Lean cannot check certificates of research size by rewriting.

This change provides the components for all three. It also keeps translation coverage measured on real corpora, so new entries follow data rather than guesses.

## What Changes

### Foundations

- **One root for Veriphy artifacts:** everything Veriphy creates or reads in a downstream project lives under `.veriphy/` at the workspace root:
  - `certificates/`: scripts;
  - `translations/`: project entries;
  - `lean/`: copied Lean assets, built through a declared `lean_lib`;
  - `coverage/`: reports.

  `sage_run file "name.sage"` resolves bare names in `.veriphy/certificates/`. Projects using the 0.1.0 `certificates/` layout get a warning and the `git mv` command that moves them. **BREAKING** for playbooks and docs, which now name `.veriphy/` paths.
- **Core translation coverage.** Each new construct comes with its domain conditions, and with explicit handling where Lean and Sage disagree on meaning:
  - **Functions:** `rpow` with real exponents, `cosh`, `sinh`, `tanh`, `arctan`, `arcsin`, `arccos` and `Real.logb`. A shared rewrite table holds `exp_log`, `log_exp`, `log_mul`, `log_div`, `log_rpow`, `sqrt_mul_self`, `cosh_sq` and similar entries, with their side conditions.
  - **Sums and products** over `Finset.Icc`, `Finset.Ico` and `Finset.range` with symbolic bounds, nested.
  - **Integer functions:** `Nat.factorial`, `Nat.choose`, `Nat.gcd`/`Int.gcd`, `Int.floor`, `Int.ceil`, and integer division and remainder.
  - **Calculus:** `deriv` and partial derivatives in coordinates, with a `HasDerivAt` proof emitter.
  - **Typed rendering:** casts and ascriptions are restored, so `n % 7` on ℕ never elaborates as a real remainder.
  - **Semantic gaps:** a domain condition bridges each gap, or the term stays opaque. Examples are ℕ subtraction, integer division, `arcsin` clamping, `rpow` of negative bases, and `deriv` at non-differentiable points. Conditions gain the two-term kind `a ≤ b`.
- **Table namespaces and extensions.** Translation and rewrite entries live in three namespaces:
  - `mathlib`: the core, always active;
  - library packs such as `physlib`: data shipped with Veriphy, active only when that library is in the environment, never imported by Veriphy;
  - `project`: JSON files in the project's `.veriphy/translations/`.

  A later namespace never overrides an earlier one. Entries drive both translation directions, are checked by a round-trip command, are listed by `sage -python -m veriphy.translations list`, and are added by agents through the `certify` playbook with no Veriphy release. Library-specific recipes live under `prompts/recipes/<library>/`.
- **Scalable checking.** `VeriphyCheck` is a mathlib-only Lean library of reflective checkers, each with a soundness theorem, evaluated by `decide` or `rfl` in the kernel, never by `native_decide`. It covers:
  - sparse rational matrices;
  - sparse polynomials;
  - structure-constant tables;
  - Pratt primality certificates.

  The emitters switch to it above a size threshold. It is also offered as a copyable file, so proofs contributed to mathlib or Physlib carry no Veriphy dependency.
- **Coverage measurement.** A Sage-free Lean command reports, for chosen modules, the share of statements translated with no opaque atom, the share left with uninterpreted local functions only, and the most frequent opaque heads. A runner measures Physlib, mathlib's `Archive`, and mathlib's ODE, Lie and manifold directories. The baseline and the post-change results are recorded.

### Mathematics and physics components

Each component has three parts: a concrete representation both sides can express, its translation, and a proof shape Lean checks. Each comes with a recipe.

- **ODEs:** Sage solves the equation, and Lean checks the solution and its initial conditions by substitution and differentiation (`ode_solution`).
- **Lie algebras:** for explicit matrix Lie algebras, including sum-indexed ones such as `Fin 1 ⊕ Fin 3`: brackets, structure constants, Killing forms, Casimirs, and Cartan-matrix facts against mathlib's `CartanMatrix` (`lie_structure`).
- **Representations and Lie superalgebras:**
  - explicit representations, from Cartan types or matrix algebras;
  - decompositions and branching rules (including GUT branchings), certified by intertwiners and projectors, never by dimension counts;
  - Clebsch–Gordan coefficients;
  - graded matrix Lie superalgebras (`sl(m|n)`, `osp`, `D(2,1;α)`, `G(3)`, `F(4)`) with super-Jacobi, supertrace and Casimir (`representation`, `lie_superalgebra`).
- **Operators:** commutators and normal ordering of matrix operators, differential-operator identities checked on an arbitrary test function, gamma-matrix traces and contractions, and Fierz identities (`operator_identity`).
- **Coordinate geometry:** mathlib-only reference definitions, shipped as a recipe asset, of Christoffel symbols, the Riemann and Ricci tensors, the Killing equation, differential forms (exterior derivative, wedge, Hodge star) and tensor contraction. Components are computed by SageManifolds and proved one by one (`coordinate_geometry`).
- **Algebraic certificates:**
  - Nullstellensatz, radical membership and Positivstellensatz certificates;
  - Smith and Jordan normal forms;
  - matrix exponentials against mathlib's `exp`, for example Lorentz boosts;
  - Pratt primality (`infeasibility`, `matrix_normal_form`, `matrix_exponential`, `primality`).
- **Summation certificates:** Wilf–Zeilberger pairs, Zeilberger telescopers, Gosper antidifferences and holonomic recurrences, proved by telescoping and induction (`wz_certificate`, `recurrence`).
- **Certified numerics:** bounds on transcendental values by series with rational remainder bounds, and isolation of real roots and eigenvalues by sign certificates (`certified_bound`, `root_isolation`).
- **Fusion categories:**
  - fusion rules, F- and R-symbols from Sage, with associativity, pentagon and hexagon equations proved over cyclotomic fields, against a mathlib-only fusion-data asset;
  - naturality of explicit linear natural transformations (`fusion_category`).

  Abstract category theory stays with mathlib's automation (`aesop_cat`, `simp`, coherence), which Veriphy does not duplicate.

## Capabilities

### New Capabilities
- `certificates/project-layout`: the `.veriphy/` directory as the single root of Veriphy artifacts in a downstream project, its resolution, copied Lean sources, and migration from 0.1.0.
- `certificates/translation-extensions`: translation and rewrite entries in namespaces (mathlib core, library packs, project), their format, discovery, round-trip checking, conflict rules and agent workflow.
- `certificates/translation-coverage`: measuring translation coverage on corpora, and reporting the opaque heads that matter most.
- `certificates/scalable-checking`: mathlib-only reflective checkers with soundness theorems, and the switch to them above a size threshold.
- `certificates/ode-bridge`: ODE goals, solutions found in Sage and proved by substitution.
- `certificates/lie-bridge`: matrix Lie algebras, structure constants, Killing forms, Casimirs and root data.
- `certificates/representation-bridge`: explicit representations, decompositions certified by intertwiners, Clebsch–Gordan coefficients and Lie superalgebras.
- `certificates/operator-bridge`: partial derivatives, and matrix-operator, differential-operator, Clifford and Fierz identities.
- `certificates/coordinate-geometry-bridge`: coordinate definitions of curvature, forms and contraction, with components checked against SageManifolds.
- `certificates/algebraic-certificates`: Nullstellensatz and Positivstellensatz certificates, matrix normal forms, matrix exponentials and primality.
- `certificates/summation-certificates`: WZ, telescoping and holonomic certificates for sums and recurrences.
- `certificates/certified-numerics`: rational certificates for bounds, roots and eigenvalues.
- `certificates/fusion-category-bridge`: fusion data with pentagon and hexagon equations, and naturality of explicit transformations.

### Modified Capabilities
- `certificates/project-scripts`: scripts move to `.veriphy/certificates/`, bare names resolve there, and the catalog finds the workspace root from subdirectories.
- `certificates/symbolic-translation`: the coverage list grows, domain conditions gain the two-term kind, semantic gaps must be bridged or left opaque, and type changes are marked.
- `certificates/symbolic-emitters`: the function table grows, rendering becomes type-aware, rewrites come from one shared table, and derivative proofs get an emitter.
- `certificates/procedures`: the recipe set gains `derivative`, `sum_induction` covers `Icc`/`Ico`, and `transcendental_rewrite` reads the shared table. Each bridge spec adds its own recipes.

## Impact

- **Lean:**
  - `Veriphy/Kit/Symbolic.lean` gains the tables as data, namespaces, the extension loader, the new conditions and typed sub-expressions;
  - new `Veriphy/Kit/Coverage.lean` and the round-trip command;
  - a new mathlib-only library `VeriphyCheck/` (checkers and soundness theorems);
  - new recipe assets: `CoordinateGeometry.lean` and `FusionData.lean`, mathlib-only.
- **Python:** `veriphy.toolkit` gains type-aware rendering, the rewrite table, the derivative emitter, and one module per component:
  - Lie and representations;
  - operators and Clifford;
  - geometry, through SageManifolds;
  - algebraic certificates;
  - summation;
  - numerics;
  - fusion;
  - reflection emitters.

  New `veriphy.translations` catalog. New library packs under `src/veriphy/packs/` (`physlib` first).
- **Optional Sage packages:** `ore_algebra` for holonomic recurrences. Each template that needs it names the install command.
- **Recipes:** about 18 new recipes, plus library-specific ones under `prompts/recipes/physlib/`, all in the recipe index.
- **Corpus runner:** `coverage/`, a separate Lake project requiring Veriphy by path and Physlib at a pinned commit (`ee0bfb40` or later with a matching mathlib). It is outside the library build and CI.
- **Docs:** a user-guide chapter per component family, the developer guide (adding entries, packs and checkers), and `docs/development/coverage.md`.
- **Compatibility:** additive, except the project layout. Scripts move from `certificates/` to `.veriphy/certificates/`, with a warning and a migration command for 0.1.0 projects. Existing scripts keep working. `symbolic` output may gain casts. Proofs that use a reflective checker depend on `VeriphyCheck`, a mathlib-only library, or on its copied file.
- **Release:** everything ships together as 0.2.0.
