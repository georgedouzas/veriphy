# Veriphy

**Certified computer algebra for Lean 4, with agent skills that turn a physics or math statement into a
machine-verified proof.**

Veriphy connects SageMath and Lean 4 using the *skeptical* architecture: Sage is an untrusted oracle. Sage finds
what is expensive to find, such as coefficients, squares, multipliers, witnesses, closed forms and intermediate
expressions. A Lean tactic block built from that data is checked by the kernel, or rejected. Sage can be wrong, buggy
or malicious and your proofs stay valid. No `sorry`, ever.

Veriphy ships **building blocks, procedures and skills, not ready-made certificates**. Each certificate is created
for the goal at hand, by an agent or by you, from a short Sage script. The script's output is checked by Lean, and
the emitted proof is plain Lean that builds without Sage.

## How it looks

```lean
import Veriphy

example (a b : ℝ) : 0 ≤ a ^ 2 * b ^ 2 - 2 * a * b + 1 := by
  sage_run "proof = nlinarith([sq_nonneg(x0*x1 - 1, problem)])"
```

Lean extracts the goal and hypotheses into a `problem`, here with `x0 = a` and `x1 = b`. The script uses Sage and
Veriphy's toolkit to build a Lean tactic block, and assigns it to `proof`. Lean runs the block and checks it. It also
rejects `sorry`, rejects any axiom beyond the standard three, and replays the printed text. Then Lean offers the
**Sage-free replacement** to commit:

```text
Try this: nlinarith [sq_nonneg (a * b - 1)]
```

Scripts usually live in your project's `.veriphy/certificates/` directory and run with
`sage_run file "<name>.sage"`.

## What Veriphy provides

| Piece | What it is |
|---|---|
| `sage_run` | The tactic: runs a proof script against the goal, checks the emitted block, emits the replacement |
| Toolkit (`veriphy.toolkit`) | Problem binding, Lean emitters (`linear_combination`, `sq_nonneg`, `nlinarith`, `calc`, case splits, witnesses, refutations, …), and exact solvers (rational LP, SOS from an SDP) |
| Recipes (`prompts/recipes/`) | One per technique, each with when to use it, a tested template, a worked example and failure modes. Covers ideal membership, Farkas refutation, SOS, factorization rewrite, witnesses, hint search, calc derivations, case splits, matrix identities, sums by induction, rational inequalities, transcendental rewrites, derivatives and ODE solutions |
| Translation tables | Lean terms to Sage in three namespaces: the `mathlib` core, library packs (`physlib`) active when the library is imported, and the project's own entries in `.veriphy/translations/`, each checked by `#veriphy_check_translations` |
| `VeriphyCheck` | Mathlib-only kernel checkers (`decide +kernel`) with soundness theorems, for matrix products, brackets, traces, structure constants and primality certificates too large for entrywise proofs |
| Coverage | `#veriphy_coverage` measures which statements of a corpus translate without opaque atoms, and ranks the heads that do not |
| Skills | `prove` (statement to verified proof, end to end) and `certify` (build one certificate with `sage_run`) |
| Catalog | `sage -python -m veriphy.certificates list` lists a project's saved scripts, so they get reused |
| Advisory oracle | `symbolic_check`, `matrix_check`, `solve`, `run_script`: Sage as guidance while formalizing, never transcribed into proofs |

Committed proofs contain only the emitted replacements, so **they build with Lean and mathlib alone, with no Sage
installed**. CI never needs Sage.

## Setup

Prerequisites: [SageMath](https://doc.sagemath.org/html/en/installation/) (10.x, with `sage` on `PATH`) and the Lean
toolchain manager [elan](https://leanprover-community.github.io/get_started.html).

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
   rev = "0.1.0"
   ```

   Then run `lake update && lake exe cache get && lake build`, and add `import Veriphy`.

3. Install the skills (below), if you work with an agent.

The tactic starts one daemon per Lean process, as `sage -python -m veriphy.sage_server`. Set `VERIPHY_SAGE_CMD` to the
`sage` executable if it is not on `PATH`. Set `VERIPHY_SAGE_TIMEOUT` (seconds, default 150) to bound each request.

## Usage

**Build a certificate:**

1. Inspect what the script will see:

   ```lean
   sage_run "print(goal_kind, goal); print(hyps); print(atoms); proof = 'sorry'"
   ```

   It fails on purpose, and the error shows the problem.
2. Pick a recipe from the index in [`prompts/prove.md`](https://github.com/georgedouzas/veriphy/blob/main/prompts/prove.md) (step 3c).
3. Copy the recipe's template from [`prompts/recipes/templates/`](https://github.com/georgedouzas/veriphy/blob/main/prompts/recipes/templates) into your project's
   `.veriphy/certificates/`, and adapt the lines marked `EDIT`.
4. Run it with `sage_run file "<name>.sage"`, and iterate on the feedback. A failure shows the script's
   output, the Lean text it built, and Lean's error.
5. Replace the `sage_run` call with the emitted `Try this:` block, and keep the script for reuse.

**Reuse:** `sage -python -m veriphy.certificates list` prints your project's scripts (name, technique, goal shape,
description), and `… show <name>` prints one. A saved script reads the bound `problem`, so it runs unchanged on any
goal of the same shape.

The full procedure is in [`prompts/certify.md`](https://github.com/georgedouzas/veriphy/blob/main/prompts/certify.md).

## Skills

- **`prove`**: turns a formal Lean statement, an informal statement, or a backlog item from a repo you supply into a
  verified proof. It formalizes with lie detection (round-trip and numeric checks), builds certificates with `certify`
  when needed, verifies, and reports `proved`, `blocked-library-gap`, `blocked-missing-building-block` or
  `statement-suspect`. You own the outcome: it opens no PRs and keeps no state.
- **`certify`**: builds one certificate for one goal with `sage_run`. It reuses the project's saved scripts, follows
  the recipes otherwise, and saves what works in `.veriphy/certificates/`.

The skill logic is plain, agent-agnostic markdown (`prompts/prove.md`, `prompts/certify.md`, `prompts/recipes/`).
The `skills/` files are thin Claude Code adapters.

**Claude Code plugin (recommended).** The repo is its own single-plugin marketplace:

```sh
claude plugin marketplace add https://github.com/georgedouzas/veriphy
claude plugin install veriphy@veriphy
```

Then use `/veriphy:prove <statement>` and `/veriphy:certify` from any project, or just ask "prove that …". Use the git
URL rather than a local clone, because a clone's path also copies its built `.lake/` (about 8 GB) into the plugin
cache.

**Manual copy (Claude Code, no plugin):**

```sh
git clone https://github.com/georgedouzas/veriphy ~/veriphy
mkdir -p ~/.claude/skills && cp -r ~/veriphy/skills/prove ~/veriphy/skills/certify ~/.claude/skills/
export VERIPHY_HOME=~/veriphy   # in your shell profile
```

**Any other agent** (Cursor, Copilot, a plain LLM loop): point it at `prompts/prove.md`. Nothing in the playbooks is
Claude-specific. Inside this repository, the project-scoped copies in `.claude/skills/` load automatically.

## Developing Veriphy

The repository is generated from [copier-modern-python](https://github.com/georgedouzas/copier-modern-python), and
`copier update` pulls template changes. The Python code follows `openspec/constitution.md`.

```sh
git clone https://github.com/georgedouzas/veriphy && cd veriphy
lake exe cache get && lake build
sage -pip install -e .           # the tactic now uses this checkout's daemon
uv sync                          # development tools
uv run nox -s checks             # ruff, mypy, bandit, docstrings, dependency audit
uv run nox -s tests              # pytest and doctests on SageMath's interpreter
lake build VeriphyTest           # Lean suite: kit (no Sage), sage_run examples, the benchmark
lake build VeriphyTest.Kit       # the kit alone, no Sage needed
```

`VeriphyTest/Benchmark.lean` holds every problem the former certificate tactics solved, each now solved by a recipe
template through `sage_run`, with replay on. See [the developer guide](https://github.com/georgedouzas/veriphy/blob/main/docs/development/index.md) for how the pieces
fit and how to add a recipe or a toolkit building block.

## Layers

```text
Veriphy/            Lean library: sage_run, problem extraction, closeAndEmit (checks, replay), the daemon bridge
src/veriphy/        The `veriphy` Python package: the Sage daemon, the toolkit, the certificate catalog
VeriphyCheck/       Mathlib-only kernel checkers with soundness theorems, bundled by scripts/bundle_check.py
coverage/           Lake project measuring translation coverage on Physlib and mathlib corpora
prompts/            Playbooks (prove, certify) and recipes with templates — agent-agnostic markdown
skills/             Claude Code adapters for the playbooks
```

## Protocol

The daemon reads one JSON request per line on stdin and writes one response per line on stdout. Every response
carries the package version. The methods are:

- `ping`;
- `run`, which runs a proof script against a serialized problem and returns its Lean text and output;
- four **advisory** methods, `symbolic_check`, `matrix_check`, `solve` and `run_script`.

Advisory output is guidance for formalization and is never transcribed into a proof. Scripts run with the daemon's
own privileges. This is deliberate: the daemon is a user-launched, untrusted oracle, and the trust boundary is the
Lean kernel.

## Status

The general route (`sage_run`, the toolkit, recipes and skills) solves every problem the former bespoke tactics
solved: 32 benchmark problems, including gauge-anomaly Farkas systems, sums of squares of field strengths and
eigenvector witnesses. The pipeline has cleared a real Physlib backlog item end to end (`isBounded_iff_of_𝓵_zero`).

## Relationship to LeanSage

[LeanSage](https://github.com/oOo0oOo/LeanSage) solved the Lean↔Sage *communication* problem with a broad
translation pipeline (MathAST), but its flagship `by sage` mode closes goals with `sorry` (a trusted oracle). Veriphy
does what LeanSage does not: kernel-checked certification and the agent loop.

Veriphy's symbolic translation follows LeanSage's coverage tables (MIT License, credited in
`Veriphy/Kit/Symbolic.lean`). Scripts see each hypothesis and the goal both as polynomials over atoms and as Sage
symbolic expressions: rational functions, `sqrt`/`exp`/`log`/trigonometric functions, `abs`, `pi`, `I`, range sums,
matrix literals, determinants and polynomial evaluation. The domain conditions those expressions need come with the
hypotheses that discharge them. One deliberate difference is that `abs` is the absolute value of its own type
(LeanSage maps it to `Int.natAbs`).

The design rationale is in [the user guide](https://github.com/georgedouzas/veriphy/blob/main/docs/overview/user_guide.md).
