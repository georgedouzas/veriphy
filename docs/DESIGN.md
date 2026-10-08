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
squares; full SOS needs an exact SDP step), `sage_lincomb` (local polyrith via
`ideal.lift`), `sage_witness`, `sage_sum` (Sage discovers the closed form;
the proof is kernel-only induction — Sage-free by construction).

Remaining entries (`sage_branch` for Lie branching rules, `sage_eigen`, full
SOS) are built **only when a `blocked-missing-tactic` report demands them**.
If this repo is still growing tactics without such demand, something went
wrong.

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
- `sage_sos` beyond completed squares (exact rational SDP).
- Candidate upstreaming of checkers to LeanSage.
