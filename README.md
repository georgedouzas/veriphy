# Veriphy

**Certified computer algebra for Lean 4, and an agent loop for clearing PhysLean's formalization backlog.**

Veriphy connects SageMath and Lean 4 using the *skeptical* architecture: Sage is an
untrusted oracle. Every Sage result must come with a **certificate** that Lean
reconstructs into a kernel-checked proof — or the tactic fails. Sage can be wrong,
buggy, or malicious and your proofs stay valid. No `sorry`, ever.

This is the complement to [LeanSage](https://github.com/oOo0oOo/LeanSage), which
solved the Lean↔Sage *communication* problem but whose flagship `by sage` mode
closes goals with `sorry` (trusted oracle). Veriphy targets the two layers LeanSage
doesn't: **certification** and the **agent loop**.

## The idea in one line

For many problem classes, *finding* the answer is hard but *checking* it is easy.
Sage finds; Lean checks; only the check is trusted.

| Tactic | Sage finds | Lean checks via | Status |
|---|---|---|---|
| `sage_factor` | polynomial factorization | multiply back: `ring1` | **working** ✅ |
| `sage_sos` | sum-of-squares decomposition | `positivity` + `ring1` | **working** ✅ |
| `sage_lincomb` | Gröbner cofactors (local polyrith) | `linear_combination` | **working** ✅ |
| `sage_witness` | rational roots for `∃ x, p x = 0` | `norm_num` on the witness | **working** ✅ |
| `sage_sum` | closed form of `∑ k ∈ range n` (`#sage_sum`) | induction + `ring1`, kernel-only | **working** ✅ |
| `sage_branch` | Lie-group branching rules | character polynomial identity | planned |
| `sage_eigen` | eigenpairs | `Av = λv` by `norm_num` | planned |

`sage_sos` currently certifies polynomials whose odd-multiplicity factors are
constants or single-variable positive-definite quadratics (includes all
perfect-square / even-power cases); wider SOS needs an exact SDP step — a
known, bounded extension, not open-ended scope.

Design rule: every tactic emits a `Try this:` replacement proof, so **committed
files check with vanilla Lean + mathlib, no Sage installed**. Sage is an
authoring-time tool only; CI never needs it.

## Layers

```
Veriphy/            Layer 1 — Lean library (lake package): bridge client + certificate tactics
sage_bridge/        Layer 2 — Sage daemon: JSON-RPC over stdio, returns structured ASTs + certificates
prompts/            Layer 3 — agent playbook (agent-agnostic markdown)
.claude/skills/     Layer 3 — Claude Code adapter for the playbook
bench/              Layer 3 — PhysLean stub ledger: cleared / blocked / cost per stub
```

The dependency arrow points down only: Layer 1 is useful with no AI, Layer 2 with
no Lean. The agent layer orchestrates both against PhysLean's `informal_lemma`
backlog and logs every outcome — including failures, which map the mathlib gaps
that block physics formalization.

## Setup

```sh
# 1. Lean toolchain (pinned in lean-toolchain)
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh
cd veriphy && lake exe cache get && lake build

# 2. Sage daemon (requires a local SageMath; tested with 10.9)
echo '{"id":1,"method":"ping"}' | sage -python sage_bridge/server.py

# 3. Smoke test the bridge end to end
echo '{"id":2,"method":"factor","params":{"poly":"x^4 - 1","vars":["x"]}}' \
  | sage -python sage_bridge/server.py
```

## Protocol

One JSON object per line on stdin, one response per line on stdout.
Polynomials cross the boundary as **structured term lists**, not strings
(`[{"coeff":"-1","exps":[0]},{"coeff":"1","exps":[4]}]` for `x⁴ − 1`), so the
Lean side reconstructs terms directly instead of parsing CAS syntax — this kills
most of the classic translation brittleness.

A `factor` response is a certificate: `unit` and `factors` (each a term list with
multiplicity). The Lean tactic rebuilds the product and closes `lhs = product`
with `ring`. The daemon's output is never trusted.

## Status

Tactic catalog complete for the classical certificate classes implementable
without an SDP solver (2026-10): five working tactics, all emitting Sage-free
`Try this:` replacements. Tests: `VeriphyTest.lean` (running them requires
Sage; the emitted replacements don't — verified by replay with Sage off PATH).
Remaining catalog entries (`sage_branch`, `sage_eigen`, full SOS) are bounded,
demand-driven additions — build them when a ledger row asks for them.
Next: persistent daemon (currently ~2s spawn per call), PhysLean stub run.

## Relationship to LeanSage

LeanSage's seven-stage MathAST pipeline is excellent plumbing; where practical,
certificate checkers should be contributed upstream rather than duplicated here.
Veriphy exists for what LeanSage doesn't do: no-`sorry` certification, physics
tactics (SOS, WZ, branching rules), and the PhysLean agent loop.
