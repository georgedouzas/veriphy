# Veriphy

An extensible framework for verifying claims, with agents in the loop, in any field that has a checkable notion of
evidence.

A claim can be a theorem, a published regression estimate, or a convention a chapter relies on. Veriphy runs each check
as a deterministic **step** and keeps a **record** of what it checked, with which tools and what came out. It gives the
claim a **level** whose **trust class** says what kind of evidence stands behind it. A kernel-checked proof, a
reproduction of an estimate and a numeric test each get a level, and no report presents one as another. Agents write
the artifacts (a formal statement, a proof, an extraction), and Veriphy checks them.

What a field means by "checked" comes from **packs**. A pack is a directory with a `pack.yaml` that declares its tools,
operations, steps, levels, conventions and workflows, and optionally code and agent playbooks. Adding a field means
writing a pack. Veriphy itself does not change.

## Packs

| Pack | Brings | Levels (trust class) |
|---|---|---|
| `core` | the claim graph: extraction, SHACL validation, reasoning checked by [`oo-horn`](https://github.com/fabio-rovai/open-ontologies), verification appendices | `none` |
| `lean` | Lean 4: `check` a file with its axioms, `level` of every declaration | `lean-proof` (kernel) |
| `math` | SageMath as an untrusted oracle: `veriphy certify` (Sage finds a certificate, the Lean kernel checks it), `meaning` tests of statements, instance tests, translation tables, recipes, and the `prove`, `certify` and `research` skills | `certificate`, `kernel-test` (kernel), `oracle-test` (oracle) |
| `reproduction` | published analyses rerun from their own script and data in a pinned R image, and robustness under declared variations | `reproduced`, `robust` (reproduction) |

A workspace with no `veriphy.yaml` uses `math`, which brings in `lean` and `core`. A workspace that names
`packs: [reproduction]` needs neither Lean nor SageMath.

## How it is built

Veriphy has five layers, each built only on the ones below it, and a pack can add to every layer:

| Layer | Holds | Command |
|---|---|---|
| 0. Primitives | deterministic operations: typed by JSON Schema, pinned, of one trust class, with no records | `veriphy layers primitive` |
| 1. Steps | a primitive with declared inputs, replayed by the digest of their content, and recorded | `veriphy layers step` |
| 2. Claims | the claim graph, each claim's level from the records, effective levels, clashes | `veriphy layers claims` |
| 3. Workflows | step sequences as data, where the records decide the next step | `veriphy layers workflow` |
| 4. Agents | playbooks and skills that follow the workflows | `veriphy layers agents` |

`veriphy config show|check` prints and checks the configuration the packs and `veriphy.yaml` resolve to, and
`veriphy pack list` lists the selected packs. A pack's own programs run as `veriphy pack <pack> <program>`. From Python,
`veriphy.run(step, target, **inputs)` runs the same steps as the shell. In Lean, the `veriphy <verb>` tactic and the
`#veriphy <verb>` command run Lean's operations.

## Two examples

**A theorem** (the `math` pack). Sage finds the certificate, and the kernel checks it:

```lean
import Veriphy

example (a b : ℝ) : 0 ≤ a ^ 2 * b ^ 2 - 2 * a * b + 1 := by
  veriphy certify "return found(nlinarith([sq_nonneg(x0*x1 - 1, problem)]))"
-- Try this: nlinarith [sq_nonneg (a * b - 1)]
```

Lean rejects the block if it uses `sorry` or any axiom beyond the standard three. You commit the Sage-free
replacement, so proofs and CI need only Lean and mathlib. A Sage bug or an agent's mistake can waste time, but it can't
produce a false theorem.

**A published estimate** (the `reproduction` pack). The analysis is rerun in a pinned R image, refused unless the data
is the claim's, and compared with the published value:

```sh
veriphy layers step reproduce analysis.R mtcars.csv <sha256> --claimed -5.344472 --claim mpg-weight
# reproduce: agrees, and the record grants reproduced (reproduction)
veriphy layers step vary analysis.R mtcars.csv <sha256> '["mpg ~ wt + hp", "mpg ~ wt + cyl"]'
# vary: robust, and the record grants robust (reproduction); or fragile, naming the variation
```

Both kinds of claim can sit in the same claim graph. A paper's policy conclusion that rests on a reproduced estimate
and a Lean-proved lemma gets the lower of the two as its effective level, and the report names the claim that caps it.

## Agents and workflows

A workflow is a list of steps, with what each record's status does next:

```yaml
workflows:
  prove-claim:
    - formalize
    - meaning: {counterexample: stop}
    - check: {refused: formalize, attempts: 3}
    - prove
    - check: {refused: prove, attempts: 5}
```

`veriphy layers workflow next prove-claim Claim.lean` reads the target's records and names the next step.
`veriphy layers workflow run …` runs the steps that need no agent until one does. Two agents working from the same
records take the same steps.

The skills follow these workflows:

| Skill | Pack | Input | Output |
|---|---|---|---|
| `prove` | `math` | a Lean or informal statement | a verified proof, or what blocked it |
| `certify` | `math` | one Lean goal | a kernel-checked certificate and a reusable script |
| `research` | `math` | a LaTeX or Markdown draft | a verification appendix covering every claim |
| `reproduce` | `reproduction` | a paper with its script and data | each estimate reproduced, tested for robustness, or refused |

## Install

```sh
pip install veriphy                  # the framework, the core and reproduction packs
pip install 'veriphy[graph]'         # with the claim graph's reasoner and checker
```

The `reproduction` pack needs podman or docker for its pinned image.

The `math` pack needs [SageMath](https://doc.sagemath.org/html/en/installation/) 10 and
[elan](https://leanprover-community.github.io/get_started.html). Install into Sage's Python, and require Veriphy in
your project's `lakefile.toml`:

```sh
sage -pip install 'veriphy[graph]'
```

```toml
[[require]]
name = "veriphy"
git = "https://github.com/georgedouzas/veriphy"
rev = "0.7.0"
```

Then run `lake update && lake exe cache get && lake build`, and add `import Veriphy` to your Lean files. If Sage's
`veriphy` isn't on your `PATH`, run it as `sage -python -m veriphy`.

The skills for Claude Code:

```sh
claude plugin marketplace add https://github.com/georgedouzas/veriphy
claude plugin install veriphy@veriphy
```

Install the plugin from the git URL. A local clone would copy its 8 GB `.lake/` into the plugin cache. Other agents can
follow the playbooks directly: `veriphy layers agents path` prints their directory (`--pack reproduction` for that
pack's playbook).

## Writing a pack

A pack is a directory with a `pack.yaml`. Name it in your `veriphy.yaml` by path, or publish it as a Python package
that declares a `veriphy.packs` entry point. Here is a sketch of a pack that wraps a command-line
tool, pinned by its container image, as a primitive, and declares a step and a level over it:

```yaml
version: 1
name: econ
requires: [core]
levels:
  replicated: {trust: reproduction, above: none, description: the estimate was recomputed from the data}
tools:
  stata:
    contract: files                     # the command writes one JSON result to {out}
    run: [stata-mp, -b, do]
    pin: {image: 'registry.example/stata:18@sha256:…'}
primitives:
  stata.run:
    tool: stata
    trust: reproduction
    command: ['{file:script}', '{file:data}', '{out}']
    input: {type: object, required: [script, data]}
    output: {type: object, required: [status, estimate]}
steps:
  replicate:
    kind: check
    primitive: stata.run
    grants: replicated
    compare: {field: estimate, against: claimed, tolerance: 0.001}
    inputs:
      script: {scope: file, path: true}
      data: {scope: file, path: true}
      claimed: {type: number, record: true}
```

`veriphy config check` refuses a step that would grant a level its primitive's trust class can't grant, and
the step's command and its `--help` are generated from the declaration. See the
[guide](https://georgedouzas.github.io/veriphy/overview/user_guide/#writing-a-pack) for every section.

## More

- [Guide](https://georgedouzas.github.io/veriphy/overview/user_guide/): concepts, configuration, steps, records,
  levels, workflows, the claim graph, and writing a pack
- [Packs](https://georgedouzas.github.io/veriphy/packs/): `math` (certificates, recipes, translations, tests), `lean`
  and `reproduction`
- [Architecture](https://georgedouzas.github.io/veriphy/architecture/): the layers and the design behind them
- [Development](https://georgedouzas.github.io/veriphy/development/): building Veriphy and adding recipes
