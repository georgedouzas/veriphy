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
| `sage_farkas` | Farkas multipliers (exact rational LP) for linear `=`/`≤`/`<` systems | `linear_combination` + `norm_num` | **working** ✅ |
| `sage_exists` | rational witness for `∃ x₁ … xₙ, P` (equations, linear inequalities, `≠`) | `norm_num` on the witness | **working** ✅ |
| `sage_certify` | a one-off certificate: an agent-written Sage script against the normalized goal | its checker family: `linear_combination` (± `sq_nonneg`, `norm_num`) or `norm_num` on a witness | **working** ✅ |
| `sage_branch` | Lie-group branching rules | character polynomial identity | planned |

`sage_sos [q₁, …, qₖ]` takes candidate squares: Sage finds exact rationals
`c₀, cᵢ ≥ 0` with `p = c₀ + Σ cᵢ qᵢ²` (exact rational LP) — the certificate
format and the check are the same as plain `sage_sos`. Use it when the squares
are known from structure (e.g. field-strength components of a potential) but
the polynomial does not factor.

`sage_farkas` closes `False`, `a ≤ b` or `a < b` from the linear hypotheses in
context (a goal is negated first). It is `linarith` with the certificate
search done by an exact LP in Sage, so it scales to large systems (e.g. gauge
anomaly-cancellation conditions over many representations) where `linarith`
times out; the emitted proof is a single `linear_combination`.

`sage_exists` covers eigen/null-vector witnesses (`A v = λ B v ∧ v ≠ 0`),
feasible points of linear systems, and explicit counterexamples. Kernel-span
certificates ("every solution of these linear equations is a combination of
these vectors") need no new tactic: they are ideal membership of linear forms,
closed by `sage_lincomb`.

`sage_sos` currently certifies polynomials whose odd-multiplicity factors are
constants or single-variable positive-definite quadratics (includes all
perfect-square / even-power cases); wider SOS needs an exact SDP step — a
known, bounded extension, not open-ended scope.

`sage_certify identity|inequality|witness "<script>"` is for certificates no
dedicated tactic finds. The script sees the goal and hypotheses already
normalized (`R`, `x0, x1, …`, `hyps`, `goal`, `binders`) and assigns
`certificate`, for example `{'squares': [(1/2, x0 - x1)]}` for `a * b ≤ (a^2 + b^2)/2`.
The family's checker then verifies it. The emitted proof is the plain checker
proof; the script never reaches committed files.

Design rule: every tactic emits a `Try this:` replacement proof, so **committed
files check with vanilla Lean + mathlib, no Sage installed**. Sage is an
authoring-time tool only; CI never needs it.

All tactics are built from one kit (`Veriphy/Kit/`): problem extraction,
proof reconstruction, checker families, and the replay check. To add one, see
["Adding a certificate"](https://github.com/georgedouzas/veriphy/blob/main/docs/development/index.md#adding-a-certificate).
Contributors run the tests with replay on (`set_option veriphy.checkReplay true`,
already set in `VeriphyTest.lean`). Each emitted replacement is then
re-parsed from its printed text and re-run with Sage disabled:

See [Developing Veriphy](#developing-veriphy) for the commands.

## Layers

```
Veriphy/            Layer 1 — Lean library (lake package): bridge client + certificate tactics
src/veriphy/        Layer 2 — Sage daemon (the `veriphy` Python package): JSON-RPC over stdio, returns certificates
prompts/            Layer 3 — the `prove` playbook (agent-agnostic markdown)
.claude/skills/     Layer 3 — Claude Code adapter for the playbook
```

The dependency arrow points down only: Layer 1 is useful with no AI, Layer 2 with
no Lean. The `prove` skill orchestrates both: the **caller supplies the target**
(a Lean statement, an informal statement, or a backlog item from a repo such as
[Physlib](https://physlib.io)) and receives back a verified proof or a precise
failure report (`blocked-library-gap` / `blocked-missing-building-block` /
`statement-suspect`). What happens with the result is the caller's
responsibility; the tool keeps no state and opens no PRs.

## Setup

Prerequisites: [SageMath](https://doc.sagemath.org/html/en/installation/)
(10.x, with `sage` on `PATH`) and the Lean toolchain manager
[elan](https://leanprover-community.github.io/get_started.html).

1. Install the Sage daemon into SageMath:

   ```sh
   sage -pip install veriphy
   echo '{"id":1,"method":"ping"}' | sage -python -m veriphy.sage_server
   ```

2. Require Veriphy from your Lake project (`lakefile.toml`), pinned to a release tag:

   ```toml
   [[require]]
   name = "veriphy"
   git = "https://github.com/georgedouzas/veriphy"
   rev = "0.4.0"
   ```

   then `lake update && lake exe cache get && lake build`, and `import Veriphy`.

3. Optionally, install the `prove` skill (below).

The tactics start the daemon as `sage -python -m veriphy.sage_server`. Set
`VERIPHY_SAGE_CMD` to the `sage` executable if it is not on `PATH`. Committed
proofs use only the emitted `Try this:` replacements, so building them needs
neither Sage nor the `veriphy` package.

## Developing Veriphy

The repository is generated from
[copier-modern-python](https://github.com/georgedouzas/copier-modern-python);
`copier update` pulls template changes. The Python code follows
`openspec/constitution.md`.

```sh
git clone https://github.com/georgedouzas/veriphy && cd veriphy
lake exe cache get && lake build
sage -pip install -e .   # the tactics now use this checkout's daemon
uv sync                  # development tools
uv run nox -s checks     # ruff, mypy, bandit, docstrings, dependency audit
uv run nox -s tests      # pytest and doctests on SageMath's interpreter
lake build VeriphyTest   # the tactic suite, live Sage, replay on
lake build VeriphyTest.Kit  # the kit alone, no Sage needed
```

To try daemon changes without reinstalling, point `VERIPHY_SAGE_SERVER` at a
script that runs it, such as `src/veriphy/sage_server/__main__.py`.

## Installing the `prove` skill

The agent skill works for any user, via any of three routes. All of them need
the Setup above completed once (the skill checks and will walk you through it
otherwise).

**A. Claude Code plugin (recommended).** The repo is both a Claude Code
plugin and its own single-plugin marketplace
(`.claude-plugin/marketplace.json`), since plugins install from marketplaces.
Register it by its git URL, then install:

```sh
claude plugin marketplace add https://github.com/georgedouzas/veriphy
claude plugin install veriphy@veriphy
```

Use the git URL rather than a local clone: a clone's path also copies its
built `.lake/` (about 8 GB) into the plugin cache. The skill needs only the
Setup above (the daemon in Sage), not a built copy of this repository. From any project:
`/veriphy:prove <statement>` (plugin skills are namespaced by plugin name),
or just ask "prove that …".

**B. Manual copy (Claude Code, no plugin).** Invoked as plain `/prove`
(personal skills are not namespaced; prefer route A for `/veriphy:prove`).
Clone the repo anywhere, run Setup, then:

```sh
git clone <git-url-of-this-repo> ~/veriphy && cd ~/veriphy  # + Setup above
mkdir -p ~/.claude/skills && cp -r skills/prove ~/.claude/skills/
export VERIPHY_HOME=~/veriphy   # put it in your shell profile
```

**C. Any other agent** (Cursor, Copilot, a plain LLM loop). The skill files
are thin adapters; the actual logic is plain markdown at `prompts/prove.md`.
Point your agent at that file, with the Setup above done. Nothing in the
playbook is Claude-specific.

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

Four methods are **advisory**, not certificate-producing, and say so in their
responses (`"advisory": true`): `symbolic_check` decides identities
symbolically (with numeric-sampling fallback and counterexamples) for the
playbook's formalization-time lie detector; `matrix_check` makes the same
decision for matrix-valued identities — Clifford relations, representation
identities, determinant formulas — given named symbolic matrices; `solve`
returns symbolic solution sets as proof-sketch guidance — e.g. the case split
behind a kernel computation; and `run_script` runs a whole derivation session
(loops, random trials, Lean-syntax generation) and returns its structured
`results` dict plus captured stdout, under a timeout. `run_script` executes
arbitrary Sage code with the daemon's own privileges — deliberately so: the
daemon is an untrusted, user-launched oracle, and the trust boundary is the
Lean kernel. Advisory output is never transcribed into a proof; the agent
re-proves in Lean whatever it uses.

## Status

Tactic catalog complete for the classical certificate classes implementable
without an SDP solver (2026-10): five working tactics, all emitting Sage-free
`Try this:` replacements. Tests: `VeriphyTest.lean` (running them requires
Sage; the emitted replacements don't — verified by replay with Sage off PATH).
Remaining catalog entries (`sage_branch`, `sage_eigen`, full SOS) are bounded,
demand-driven additions — build them when a `blocked-missing-building-block` report
asks for them. The pipeline has cleared a real Physlib backlog item end to end
(`isBounded_iff_of_𝓵_zero`). Next: persistent daemon (~2s spawn per call).

## Design

The founding design discussion — why the skeptical architecture, the
certificate-catalog scope boundary, the pure-tool decision — is recorded in
[the user guide](https://github.com/georgedouzas/veriphy/blob/main/docs/overview/user_guide.md).

## Relationship to LeanSage

LeanSage's seven-stage MathAST pipeline is excellent plumbing; where practical,
certificate checkers should be contributed upstream rather than duplicated here.
Veriphy exists for what LeanSage doesn't do: no-`sorry` certification, physics
tactics (SOS, WZ, branching rules), and the `prove` agent skill.
