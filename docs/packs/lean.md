# The `lean` pack

The `lean` pack checks Lean 4 files and reads the levels Lean's proof terms carry. It needs
[elan](https://leanprover-community.github.io/get_started.html) and a Lake workspace that requires Veriphy, and no
SageMath.

| Step | Kind | Does |
|---|---|---|
| `check <file>` | check | Lean checks the file, and the record gives each declaration's axioms |
| `level <module> [--prefix P]` | derived | the level `#veriphy level` gives each declaration under the prefixes |

`lean-proof` (a complete proof on the standard axioms alone) is the level Lean reads from a proof term, through
`level` and `#veriphy export`.

```sh
veriphy layers step check Claim.lean
veriphy layers step level MyProject.Basic --json
```

Each step runs Lean once, as `lake env lean` in the workspace, and keeps no process: the record names the
workspace's toolchain.

`check`'s digest scope is `lean-imports`: the file, the workspace files it imports, the toolchain and the manifest. An
edit to a file the claim doesn't import replays the record, and a toolchain bump runs it again. `level` digests the
whole workspace (`lean-workspace`).

## In Lean

`import Veriphy` gives one tactic, `veriphy <verb>`, and one command, `#veriphy <verb>`, so no name clashes with
mathlib. `#veriphy help` lists the verbs. The ones that need no Sage:

| Command | Does |
|---|---|
| `#veriphy level P …` | the level of each theorem under the prefixes |
| `#veriphy export P … ["file.nt"]` | the formalized claims under the prefixes, with levels, statements and dependencies, for the [claim graph](../overview/user_guide.md#the-claim-graph) |
| `#veriphy translate t`, `#veriphy translations`, `#veriphy coverage [p, …]` | the `math` pack's translation to Sage, inspected without Sage |

`#veriphy export KK` writes every theorem and definition under `KK` to `.veriphy/graph/lean/KK.nt`. These come from the
Lean environment, not from extraction. In a source file, `formalizedBy` links a prose claim to its Lean claim, and
`realizedBy` links a convention to the Lean definition behind it.
