# Veriphy

**Certified computer algebra for Lean 4, with an agent skill that turns a physics
or math statement into a machine-verified proof.**

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
prompts/            Layer 3 — the `prove` playbook (agent-agnostic markdown)
.claude/skills/     Layer 3 — Claude Code adapter for the playbook
```

The dependency arrow points down only: Layer 1 is useful with no AI, Layer 2 with
no Lean. The `prove` skill orchestrates both: the **caller supplies the target**
(a Lean statement, an informal statement, or a backlog item from a repo such as
[Physlib](https://physlib.io)) and receives back a verified proof or a precise
failure report (`blocked-library-gap` / `blocked-missing-tactic` /
`statement-suspect`). What happens with the result is the caller's
responsibility; the tool keeps no state and opens no PRs.

## Setup

Prerequisites: [SageMath](https://doc.sagemath.org/html/en/installation/)
(tested with 10.9; `sage` must be on `PATH`) and the Lean toolchain manager
[elan](https://leanprover-community.github.io/get_started.html).

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

## Installing the `prove` skill

The agent skill works for any user, via any of three routes. All of them need
the Setup above completed once (the skill checks and will walk you through it
otherwise).

**A. Claude Code plugin (recommended).** The repo is a Claude Code plugin;
installing it clones the repo and registers the skill globally:

```
/plugin install <git-url-of-this-repo>
```

Then run Setup inside the installed plugin directory (the plugin root is the
repo). From any project: `/prove <statement>`, or just ask "prove that …".

**B. Manual copy (Claude Code, no plugin).** Clone the repo anywhere, run
Setup, then:

```sh
git clone <git-url-of-this-repo> ~/veriphy && cd ~/veriphy  # + Setup above
mkdir -p ~/.claude/skills && cp -r skills/prove ~/.claude/skills/
export VERIPHY_HOME=~/veriphy   # put it in your shell profile
```

**C. Any other agent** (Cursor, Copilot, a plain LLM loop). The skill files
are thin adapters; the actual logic is plain markdown at `prompts/prove.md`.
Point your agent at that file, tell it where the repo is, and set
`VERIPHY_SAGE_SERVER=<repo>/sage_bridge/server.py` for builds outside the
repo. Nothing in the playbook is Claude-specific.

Working *inside* this repo needs no installation: the project-scoped copy in
`.claude/skills/` loads automatically.

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
demand-driven additions — build them when a `blocked-missing-tactic` report
asks for them. The pipeline has cleared a real Physlib backlog item end to end
(`isBounded_iff_of_𝓵_zero`). Next: persistent daemon (~2s spawn per call).

## Relationship to LeanSage

LeanSage's seven-stage MathAST pipeline is excellent plumbing; where practical,
certificate checkers should be contributed upstream rather than duplicated here.
Veriphy exists for what LeanSage doesn't do: no-`sorry` certification, physics
tactics (SOS, WZ, branching rules), and the `prove` agent skill.
