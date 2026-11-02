# Veriphy

Agent skills and a Lean 4 toolkit for machine-verified math and physics, from a single theorem to a whole paper.

Veriphy treats SageMath and the agent as untrusted. Sage finds what is expensive to find (coefficients, sums of squares,
witnesses, closed forms), a script turns that into a Lean tactic block, and the kernel accepts it or rejects it. A Sage
bug or an agent's hallucination can waste time, but it can't produce a false theorem. Committed proofs are plain Lean
and build with mathlib alone, so CI never needs Sage.

For a paper, single proofs aren't enough. You also need to know which conventions each claim assumes and how far a weak
lemma undermines what rests on it. Veriphy records this in a claim graph. An untrusted reasoner derives the
consequences, and `oo-horn`, an independent Lean checker from
[Open Ontologies](https://github.com/fabio-rovai/open-ontologies), accepts or refuses every run.

## Workflows

Veriphy has three skills. `research` calls `prove`, and `prove` calls `certify`.

| Skill | Input | Output |
|---|---|---|
| `prove` | a Lean statement, an informal statement, or a backlog item from a repo you supply | a verified proof, or a report of what blocked it |
| `certify` | one Lean goal | a kernel-checked certificate and a reusable script |
| `research` | a LaTeX or Markdown draft, chapter or paper | a verification appendix covering every claim |

### Proving a theorem

```text
/veriphy:prove the partition function Z(β) = 2cosh(βh) satisfies ∂²(log Z)/∂β² = h²/cosh²(βh)
```

1. **Formalize.** The agent states the claim in Lean, following the conventions of the target file. Lean can't check
   that the formal statement means what you said, so two checks come first: the agent translates the statement back to
   English and compares, then tests it with `symbolic_check` or at random values in Sage.
2. **Prove.** It tries the cheap routes first: `simp`, `nlinarith` and friends, then premise search. For a computational
   core it calls `certify`, which reuses a saved script from `.veriphy/certificates/` or adapts one of the recipes.
3. **Verify.** `lake build` from clean, no `sorry`, and only the Sage-free replacements committed.
4. **Report.** `proved`, `tested` (no certificate is feasible, so `sage_test` checked instances),
   `statement-suspect` (with the counterexample), `blocked-library-gap` or `blocked-missing-building-block`.

It never opens PRs. What to do with the result is your decision.

### Writing a paper

`research` doesn't write your prose. It checks a draft, and you run it repeatedly as the draft grows:

```text
/veriphy:research chapter9.tex
```

1. **Extract.** The agent records claims, conventions and dependencies in `.veriphy/graph/sources/chapter9.agent.ttl`.
   You confirm what you agree with, which moves it to your own `.human.ttl` file.
2. **Triage.** Each claim gets tested numerically under the conventions it assumes, then goes into one of four groups:
   `suspect` (a counterexample turned up), `recipe`, `test` or `formalize`.
3. **Prove.** In dependency order, each claim goes through `prove` or `sage_test`, with a graph slice as context: its
   statement, the claims it uses and the Lean definitions behind its conventions.
4. **Reason.** `#veriphy_graph` exports levels and dependencies from Lean, the reasoner derives the consequences, and
   `oo-horn` checks the run. An accepted run has the verdict `entailed`.
5. **Report.** The appendix gives each claim's own and effective level and names what caps it, along with convention
   clashes, including those inherited from cited papers. Fix the draft, run again, and include the appendix in the paper
   (`--format latex`).

A theorem proved with a recipe but resting on a Sage-tested lemma has the effective level `oracle-test`, and the report
names that lemma. Before changing a convention midway, `impact` lists every claim it reaches and `plan --against HEAD`
shows what your edit would change.

The graph doesn't check that a prose claim and its Lean statement say the same thing. That link is an assertion, and
reports count who made it.

### Building one certificate

When you are already in a Lean proof and one computational goal is in the way, `/veriphy:certify` builds the proof for
that goal. It is also the route for `sage_run` by hand, described in the
[user guide](https://georgedouzas.github.io/veriphy/overview/user_guide/#building-proofs-with-sage_run).

## What's included

| Piece | What it does |
|---|---|
| `sage_run` | runs a proof script against the goal, checks the emitted block, and emits a Sage-free replacement |
| Toolkit (`veriphy.toolkit`) | binds the goal as a `problem`, emits Lean (`linear_combination`, `nlinarith`, `calc`, witnesses, refutations and more), and has exact solvers (rational LP, SOS from an SDP) |
| Recipes (`prompts/recipes/`) | one per technique: when to use it, a tested template, a worked example and its failure modes |
| Translation tables | map Lean terms to Sage, for mathlib, library packs such as `physlib`, and your project's own entries, each checked by `#veriphy_check_translations` |
| `VeriphyCheck` | mathlib-only kernel checkers (`decide +kernel`) with soundness theorems, for matrix products, structure constants and primality too large for entrywise proofs |
| `sage_test` and levels | test claims with no feasible certificate at instances. `#veriphy_levels` reports `certificate`, `lean-proof`, `kernel-test`, `oracle-test` or `none` |
| Claim graph (`veriphy.graph`) | effective levels, convention impact, clashes across papers, context slices and appendices, with each conclusion checked by `oo-horn` |
| Coverage | `#veriphy_coverage` measures which statements of a corpus translate without opaque atoms |

## Install

You need [SageMath](https://doc.sagemath.org/html/en/installation/) 10 with `sage` on `PATH`, and
[elan](https://leanprover-community.github.io/get_started.html).

Install the skills and the Sage side:

```sh
claude plugin marketplace add https://github.com/georgedouzas/veriphy
claude plugin install veriphy@veriphy
sage -pip install veriphy            # or 'veriphy[graph]' for the research skill
```

Then require Veriphy in your project's `lakefile.toml`:

```toml
[[require]]
name = "veriphy"
git = "https://github.com/georgedouzas/veriphy"
rev = "0.6.0"
```

Run `lake update && lake exe cache get && lake build`, and add `import Veriphy` to your Lean files.

The graph extra is the only install step for `research`. Its first run fetches the reasoner and the `oo-horn` checker
from a pinned Open Ontologies release and verifies them against a pinned commit and hash. On Linux x86_64 `oo-horn` is a
prebuilt binary. Elsewhere it is built once with `elan`, which takes a few minutes.

Install the plugin from the git URL. A local clone would copy its 8 GB `.lake/` into the plugin cache.

**Other agents.** The skills are plain markdown. Point your agent at
[`prompts/prove.md`](https://github.com/georgedouzas/veriphy/blob/main/prompts/prove.md),
[`certify.md`](https://github.com/georgedouzas/veriphy/blob/main/prompts/certify.md) or
[`research.md`](https://github.com/georgedouzas/veriphy/blob/main/prompts/research.md).

**Claude Code without the plugin:**

```sh
git clone https://github.com/georgedouzas/veriphy ~/veriphy
mkdir -p ~/.claude/skills
cp -r ~/veriphy/skills/prove ~/veriphy/skills/certify ~/veriphy/skills/research ~/.claude/skills/
export VERIPHY_HOME=~/veriphy   # in your shell profile
```

## What a proof looks like

The skills work through one tactic, which you can also use by hand:

```lean
import Veriphy

example (a b : ℝ) : 0 ≤ a ^ 2 * b ^ 2 - 2 * a * b + 1 := by
  sage_run "proof = nlinarith([sq_nonneg(x0*x1 - 1, problem)])"
```

The script sees the goal as `problem` and builds a Lean tactic block. Lean runs the block, and rejects it if it uses
`sorry` or any axiom beyond the standard three. Then Lean offers a replacement to commit, with no Sage in it:

```text
Try this: nlinarith [sq_nonneg (a * b - 1)]
```

## More

- [User guide](https://georgedouzas.github.io/veriphy/overview/user_guide/): the skills, `sage_run` by hand, recipes,
  verification levels and the research claim graph
- [Components](https://georgedouzas.github.io/veriphy/overview/components/): what the toolkit covers, family by family
- [Development](https://georgedouzas.github.io/veriphy/development/): building Veriphy and adding recipes
