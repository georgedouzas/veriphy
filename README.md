# Veriphy

Veriphy checks the claims in your work, keeps a record of every check, and tells you how far each claim is verified.

A claim can be a theorem, an estimate from a regression, a number in a table, or a quotation. Veriphy checks it with
the right tool: Lean for a proof, the authors' own script for an analysis, a short function for a statistic. It records
what was checked and what came out, and gives the claim a level such as `lean-proof`, `reproduced` or `none`. Every
level says what kind of evidence stands behind it, so a reproduced estimate never reads as a proof.

Agents can do the writing: a formal statement, a proof, the list of claims in a paper. Veriphy checks what they write.
Lean refuses a wrong proof, and sampling a statement catches one that doesn't say what was meant.

## An example

A study reports that each extra year of education raises social trust by 0.127 points. With its script and data:

```console
$ veriphy layers step reproduce analysis.py survey.csv --claimed 0.127 --claim trust-education
reproduce analysis.py: agrees
  found 0.1265132608543874, the claim says 0.127 (tolerance 0.0005)
  level: reproduced (reproduction)
  record: .veriphy/runs/reproduce/39da61d5….json
```

Run it again and nothing reruns: the inputs haven't changed, so Veriphy returns the record it has. Change the data or
the script, and the step runs again.

## Packs

Each field Veriphy checks comes as a pack: a directory whose `pack.yaml` declares the field's tools, steps, levels,
conventions and workflows, with its agents' playbooks beside it. Two ship with Veriphy:

| Pack | Checks | Needs |
|---|---|---|
| `math` | mathematics in Lean: proofs, with SageMath to find them, and statements, by sampling them | Lean, SageMath |
| `social-science` | a study: its analysis rerun from its own Python script and data, its robustness, its constructs against a thesaurus | Python |

Every workspace also has the claim graph, which is part of Veriphy rather than a pack. It records what each claim
rests on and which conventions it assumes, finds the weakest link, and reports clashes. Its reasoning is checked by
[`oo-horn`](https://github.com/fabio-rovai/open-ontologies).

A workspace chooses its packs in `veriphy.yaml`; without one, it uses `math`:

```yaml
version: 1
packs: [social-science]
```

A field Veriphy doesn't cover yet needs a pack, often a few dozen lines of YAML and a short function. The
[guide to packs](https://georgedouzas.github.io/veriphy/packs/) walks through two complete examples, for economics and
for history.

## Install

```sh
pip install veriphy
```

For the `math` pack, install into SageMath's Python instead (`sage -pip install veriphy`), and require Veriphy's Lean
library in your Lean project's `lakefile.toml`:

```toml
[[require]]
name = "veriphy"
git = "https://github.com/georgedouzas/veriphy"
rev = "0.7.0"
subDir = "src/veriphy/packs/math/lean"
```

In Claude Code, the skills `/veriphy:prove`, `/veriphy:research` and `/veriphy:reproduce` run the same commands for you:

```sh
claude plugin marketplace add https://github.com/georgedouzas/veriphy
claude plugin install veriphy@veriphy
```

## Learn more

- [Getting started](https://georgedouzas.github.io/veriphy/overview/getting_started/): a first session with each pack
- [Guide](https://georgedouzas.github.io/veriphy/overview/user_guide/): records, levels, workflows and the claim graph
- [Packs](https://georgedouzas.github.io/veriphy/packs/): choosing, combining and writing packs
- [Reference](https://georgedouzas.github.io/veriphy/overview/reference/): every command and every `pack.yaml` field
