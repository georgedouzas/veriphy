# Benchmark

The effectiveness gate for the move from ready-made certificate tactics to building blocks (the
`sage-building-blocks` change), run on 2026-10-12.

## Mechanical half

`VeriphyTest/Benchmark.lean` holds all 32 problems the removed tactics (`sage_factor`, `sage_sos`, `sage_lincomb`,
`sage_witness`, `sage_sum`, `sage_farkas`, `sage_exists`, `sage_certify`) solved. Each one is closed by running a recipe
template with `sage_run`, with replay on. **32/32 pass.**

## Agent half

The setup:

- **Agents:** four fresh agents, each given 8 of the 32 statements with the proofs blanked.
- **Allowed reading:** only `prompts/certify.md`, step 3 of `prompts/prove.md`, and the recipes. The test files, the
  OpenSpec artifacts and the git history were off limits.
- **Project:** a scratch Lake project that requires Veriphy, with a shared `certificates/` directory, so the agents
  could reuse each other's scripts.

**32/32 solved.** The committed proofs build with Sage removed from `PATH`.

| Agent | Solved | Iterations | Reused a saved script | Wall time |
|---|---|---|---|---|
| 1 | 8/8 | 9 | 4 | about 72 s |
| 2 | 8/8 | 10 | 4 | about 83 s |
| 3 | 8/8 | 11 | 8 | about 44 s |
| 4 | 8/8 | 9 | 8 | about 40 s |
| **All** | **32/32** | **39** | **24** | |

The project ended with 7 saved scripts covering all 32 problems. 26 problems closed on the first run of their script.
The extra iterations came from three causes:

- one hinted sum of squares, where the SDP route reported boundary rounding and the recipe's failure mode led to
  `HINTS`;
- one implication goal, `P → Q`, which needed `intro` before the script could see the relation;
- scripts that one agent saw in the catalog but another agent deleted or renamed concurrently.

## Friction found, and what changed

| Friction | Change |
|---|---|
| The Farkas negation emitted unused `simp` lemmas, which caused lint warnings | `negate_goal` emits `push Not at h` |
| The catalog showed header names, not the path `sage_run file` needs | `list` prints the path first |
| It was unclear whether the replacement's parentheses and `[apply]` marker belong in the proof | `certify.md` says to keep the parentheses and drop the marker |
| Implication goals arrive as `other` | `certify.md` says to `intro` and split before `sage_run` |
| Goal-specific scripts, such as hard-coded `HINTS`, looked general | `certify.md` says to name them specifically and keep `name` equal to the file name |
| Agents deleted or renamed each other's scripts | `certify.md` says never to delete or rename another's script |
| `factor_rewrite` leaves a goal open, but its output did not say so | its header and recipe now say a closing tactic must follow |
