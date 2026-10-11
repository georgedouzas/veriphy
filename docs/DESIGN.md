# Veriphy: design rationale

Distilled from the founding discussion (2026-10-07/08). Records what was
decided and *why*, so future changes argue against the original reasoning
rather than rediscovering it.

## 1. The problem

Lean 4 and a CAS (SageMath) solve complementary problems: a CAS *computes*
answers fast but every result is trusted (wrong branch cuts, dropped
solutions, simplifier bugs are real failure modes); Lean *proves* statements
with kernel certainty but has nothing like a CAS's symbolic engine. Physics
needs both: heavy computation and, for long error-prone derivations,
certainty.

## 2. Core decision: the skeptical architecture

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

## 3. Relationship to LeanSage

[LeanSage](https://github.com/oOo0oOo/LeanSage) (discovered mid-design) solved
the Lean↔Sage *communication* problem (a seven-stage MathAST pipeline) but its
flagship `by sage` mode closes goals with `sorry` — the trusting oracle,
unusable for mathlib/Physlib contributions. Veriphy deliberately occupies the
complement: certification and the agent skill. Where practical, certificate
checkers should be contributed upstream rather than duplicated.

## 4. Scope boundary: the certificate catalog

A `sage_*` tactic exists only where three things coincide: (1) finding ≫
checking, (2) a known certificate format, (3) an existing Lean checker
(`ring1`, `positivity`, `norm_num`, `linear_combination`, `decide`). That
triple intersection is the classical, essentially closed catalog
(Gröbner/ideal membership, factorization, SOS, WZ pairs, primality
certificates, eigen witnesses, LP duality) — eight to ten entries, ever.

Implemented (2026-10): `sage_factor`, `sage_sos` (factorization + completed
squares, plus caller-supplied candidate squares `sage_sos [q₁, …]`; full SOS
needs an exact SDP step), `sage_lincomb` (local polyrith via `ideal.lift`;
also kernel-span certificates), `sage_witness`, `sage_sum` (Sage discovers the
closed form; the proof is kernel-only induction — Sage-free by construction),
`sage_farkas` (LP duality: exact rational Farkas multipliers checked by
`linear_combination`), `sage_exists` (rational witnesses checked by
`norm_num`; this subsumes the planned `sage_eigen`).

The last three were added on demand from a physics formalization (Forgács–Manton
reduction over super coset spaces): the gauge-anomaly no-go systems exceeded
`linarith`, the potentials were sums of squares of field strengths that do not
factor, and mass spectra need eigenvector witnesses.

Remaining entries (`sage_branch` for Lie branching rules, full SOS) are built
**only when a `blocked-missing-tactic` report demands them**.
If this repo is still growing tactics without such demand, something went
wrong.

Since 2026-10 the catalog grows by **checker families**, not bespoke tactics.
Every tactic was the same six stages, and only the Sage solve step (plus the
choice of checker) differed. The shared stages now live in a kit (`Veriphy/Kit/`),
and a fixed set of families covers the checkers: `identity` (`ring1`,
`linear_combination`), `inequality` (`linear_combination` with `sq_nonneg`
terms, or a `norm_num` refutation), `witness` (`norm_num`), `sum` (induction)
and `cases` (`decide`). The agent can also write a one-off certificate itself:
`sage_certify <family> "<sage script>"` runs a script against the normalized
problem and checks its `certificate` with the family's checker, so a
certificate that fits a family needs no new tactic. `blocked-missing-tactic`
now means *no family can check it*. A new family is the unit of growth.

### Adding a certificate

| stage | what | where |
|---|---|---|
| 1. parse | goal + context → `Problem` (shared atom table, `=`/`≤`/`<`/`≠`, `∃` binders, conjuncts; inaccessible hypotheses skipped) | `withProblem` (`Kit/Problem.lean`) |
| 2. request | typed daemon call, refused during replay | `Kit.run (Bridge.…)` / `Bridge.call` (`Kit/Replay.lean`, `Bridge.lean`) |
| 3. solve | the certificate search, the only new code | `@method("name", vars=Vars, poly=Poly, …)` in `sage_bridge/server.py`, plus `exact_lp` |
| 4. rebuild | rationals, polynomials, weighted hypothesis sums, witnesses, step blocks, all unhygienic | `Kit/Build.lean` |
| 5. check | pick a family | `Checker.*` (`Kit/Family.lean`) |
| 6. emit | run exactly what is printed, replay it if `veriphy.checkReplay`, emit one `Try this:` | `closeAndEmit` |

A complete tactic (`∃ x, p x = 0` by a rational root):

```lean
elab ref:"my_root" : tactic => do
  -- stages 1–4: extract, call Sage, rebuild — inside the problem's context
  let root ← withProblem { tac := "my_root", allowExists := true } fun p => do
    let .exists_ _ #[c] := p.goal | throwError "my_root: expected `∃ x, p x = q x`"
    let some r := (← Kit.run "roots" (Bridge.roots c.poly "x0")).head?
      | throwError "my_root: no rational root"
    return r
  -- stages 5–6: the witness family builds the proof; closeAndEmit runs it, replays it, emits it
  closeAndEmit ref (← Checker.witness [root] 1)
```

Tests run with `set_option veriphy.checkReplay true`: every emitted replacement is
pretty-printed, re-parsed and re-run on the original goal with the bridge
disabled. That catches hygienic names (`h✝`), printer round-trip failures and
hidden Sage calls. Daemon methods are tested with `sage -python -m unittest
sage_bridge/test_server.py`, and the kit itself (Sage-free) with
`lake build VeriphyTest.Kit`.

## 5. Product decision: a pure tool

Veriphy is a tool, not a campaign:

- **The caller supplies the target** (a formal Lean statement, an informal
  statement, or a backlog item in a repo the caller provides — e.g. a
  [Physlib](https://physlib.io) `informal_lemma`). No target library is
  cloned, wired, or assumed by the repo.
- **The caller owns the outcome.** The `prove` skill ends at a report —
  `proved` / `blocked-library-gap` / `blocked-missing-tactic` /
  `statement-suspect` — and never opens PRs, keeps ledgers, or commits beyond
  what was asked. (An earlier design embedded a Physlib stub ledger and PR
  step; both were removed for this reason.)
- Workspaces wiring Veriphy to a target library (a lakefile requiring both)
  are created on demand and are disposable.

## 6. The AI's role

The agent (any agent — the skill logic is plain markdown in
`prompts/prove.md`) proposes formalizations and proofs; Lean checks them. Two
lie detectors guard the one step the kernel cannot check — that the *formal
statement means what the informal one said*: round-trip informalization, and
numeric evaluation of the statement in Sage at random parameter values before
any proof attempt. Definitions are never invented by the agent; they are
flagged to the caller.

## 7. Validation

The pipeline ran end to end once during design (2026-10-08): Physlib's
informal lemma `isBounded_iff_of_𝓵_zero` (Higgs potential bounded iff
`μ2 ≤ 0` when `𝓵 = 0`) was formalized, numerically validated, proved
(~15 lines, one compile-fix round), and kernel-checked. Notably it needed *no*
Sage tactic — evidence that easy backlog items clear with plain mathlib
automation, and the `sage_*` tactics earn their keep on the computational
residue.

## 8. Known future work

- Persistent daemon (each tactic call currently pays ~2 s of Sage startup).
- `sage_sos` beyond completed squares and hinted squares (exact rational SDP).
- Candidate upstreaming of checkers to LeanSage.
