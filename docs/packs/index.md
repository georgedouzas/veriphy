# Packs

A pack holds the checks of one field. Statistics has a pack that reruns analyses and recomputes p-values. Physics has
one that checks the units of formulas. Mathematics has one that checks proofs in Lean. You choose the packs a project
uses in its `veriphy.yaml`, and their steps become commands.

This page lists the packs that ship with Veriphy, then explains how to choose, combine and write packs. Each pack
has its own page with examples.

Some things don't belong to any field, so every workspace has them, whatever its packs: records, the claim graph,
workflows, and the steps `record-statement`, `record-claims`, `validate`, `reason`, `appendix` and `check-concepts`.

## The shipped packs

Every shipped pack checks claims with the standard library of its field, so a check means what the field already
takes it to mean: SciPy recomputes a p-value, Biopython reads a FASTA file, RDKit reads a molecule.

| Pack | Field | Steps | Levels | Install |
|---|---|---|---|---|
| [`math`](math.md) | mathematics, and mathematical physics, in Lean | `check`, `levels`, `sample`, `record-proof` | `oracle-test` < `kernel-test` < `lean-proof` < `certificate` | Lean, SageMath |
| [`statistics`](statistics.md) | analyses of data, and the statistics papers report | `reproduce`, `robustness`, `check-p-value`, `check-mean` | `recomputed` < `reproduced` < `robust` | `veriphy[statistics]`: pandas, SciPy, statsmodels |
| [`social-science`](social_science.md) | surveys and studies: their scales and constructs | `check-reliability`, and the `statistics` steps | those of `statistics` | `veriphy[social-science]`: pingouin |
| [`economics`](economics.md) | the tables of economic papers | `recompute`, and the `statistics` steps | those of `statistics` | `veriphy[economics]` |
| [`physics`](physics.md) | formulas and physical constants | `check-units`, `check-constant` | `dimensionally-consistent` | `veriphy[physics]`: pint, SciPy |
| [`life-sciences`](life_sciences.md) | sequences, and ontology terms | `check-sequence` | `sequence-checked` | `veriphy[life-sciences]`: Biopython, pronto |
| [`chemistry`](chemistry.md) | molecules and reactions | `check-molecule`, `check-reaction` | `structure-checked` | `veriphy[chemistry]`: RDKit |

### Subfield packs

A subfield pack is nested in its field's pack, and builds on it with the codes its subfield trusts: its package sits
in the field's (`veriphy/packs/physics/particle_physics/`), and selecting it brings the field, so
`packs: [econometrics]` also gives the `economics` and `statistics` steps.

```text
math/          number-theory  group-theory  graph-theory
statistics/    epidemiology
economics/     econometrics
physics/       particle-physics  general-relativity
life-sciences/ genomics
social-science/  chemistry/
```

| Pack | Builds on | Checks | Steps | Level | Install |
|---|---|---|---|---|---|
| [`number-theory`](number_theory.md) | `math` | factorizations, class numbers | `check-factorization`, `check-class-number` | `oracle-test` | PARI, in Sage |
| [`group-theory`](group_theory.md) | `math` | finite groups: order, structure, properties | `check-group` | `oracle-test` | GAP, in Sage |
| [`graph-theory`](graph_theory.md) | `math` | graph invariants | `check-graph` | `oracle-test` | Sage |
| [`particle-physics`](particle_physics.md) | `physics` | flavour predictions, running coefficients, PDG values | `check-prediction`, `run-coefficients`, `check-pdg` | `prediction-recomputed` | flavio, wilson, particle |
| [`general-relativity`](general_relativity.md) | `physics` | the curvature claimed of a metric | `check-metric` | `curvature-checked` | EinsteinPy, SymPy |
| [`genomics`](genomics.md) | `life-sciences` | variant calls, genotypes, read depth | `check-variant`, `check-coverage` | `genomic-data-checked` | pysam |
| [`econometrics`](econometrics.md) | `economics` | regressions: OLS, IV, panel | `check-regression` | `recomputed` | linearmodels |
| [`epidemiology`](epidemiology.md) | `statistics` | hazard ratios, median survival | `check-hazard-ratio`, `check-median-survival` | `recomputed` | lifelines |

Each installs with its extra, `pip install 'veriphy[genomics]'`, which brings its field pack's libraries too. The
subfields of mathematics need only SageMath, which ships PARI and GAP: they run their code under Sage, through the
math pack's `sage` tool, with `run <module:function>`.

`social-science` and `economics` build on `statistics`, so selecting either brings its steps too. Every workspace also
has `check-concepts`, which checks a source's concepts against a thesaurus or an ontology, in SKOS, OWL or OBO.

`pip install 'veriphy[all]'` installs every pack's libraries. A pack whose libraries are missing still loads, and
`veriphy layers primitive list` names what can't run.

## Choosing packs

A workspace names its packs in `veriphy.yaml`, at its root:

```yaml
version: 1
packs: [social-science]
```

Without a `veriphy.yaml`, a workspace uses `math`. That is the default for a Lean project.

A pack is named in one of three ways:

- the name of a shipped pack: `math`, `statistics`, `life-sciences`;
- the name a Python package registers under the `veriphy.packs` entry point, for a pack published on PyPI;
- the path of a directory holding a `pack.yaml`: `./packs/epidemiology`, for a pack of your own.

`veriphy pack list` shows the packs a workspace uses, and `veriphy config show` shows everything they declare, with
the pack each entry comes from. `veriphy config check` checks that it all fits together.

## Combining packs

A workspace can use several packs. A paper on a drug's binding that quotes a physical constant might use:

```yaml
version: 1
packs: [physics, chemistry]
```

Packs are applied in order, each after the packs it `requires`. When two packs that don't require each other declare
the same entry, `veriphy config check` names both, and the workspace decides by declaring that entry itself.

The levels of a workspace form one order, from `none` up, so that a claim's effective level, the lowest among
everything it rests on, is well defined. Each pack places its levels with `above`. Two packs that each put a level
directly above `none` leave the order open:

```console
$ veriphy config check
config: levels dimensionally-consistent and structure-checked are both directly above 'none': set one's `above`
config: levels.dimensionally-consistent is not on the chain from none
config: levels.structure-checked is not on the chain from none
```

The workspace settles it:

```yaml
version: 1
packs: [physics, chemistry]
levels:
  structure-checked: {above: dimensionally-consistent}
```

## Changing a pack's entries

`veriphy.yaml` can change any entry a pack declares, as a JSON Merge Patch (RFC 7396). A mapping merges key by key, a
later value replaces an earlier one, and `null` removes an entry:

```yaml
version: 1
packs: [math]
tools:
  sage: {timeout: 1200}          # give Sage more time
steps:
  sample: {help: sample the statement before proving it}
```

The configuration's digest enters every record, so a change that alters what a step does reruns it, while a change
to a comment doesn't.

## Writing a pack

Writing a pack starts with three questions about the field:

- **What is checked?** A statistic recomputed from data, a sequence read from a file, a proof accepted by Lean.
- **What does a successful check establish?** That becomes a level, with a trust class saying what kind of evidence it
  is. A level must be one the check can establish: a recomputation can't grant a proof.
- **What do claims assume?** Choices that exclude each other, such as two genome assemblies or two measures of one
  construct, become conventions.

The answers become a `pack.yaml`. The shipped `economics` pack is a short, complete one: it recomputes a statistic of
a published table with pandas and compares it with the claim.

### A check in Python

The check is a Python function. It receives the step's inputs and returns a status with what it found. This is the
`economics` pack's, in full:

```python
--8<-- "src/veriphy/packs/economics/primitives/_tables.py"
```

The `pack.yaml` declares the function as a primitive, a step over it, the field's conventions and a workflow:

```yaml
--8<-- "src/veriphy/packs/economics/pack.yaml"
```

The step grants `recomputed`, a level the `statistics` pack declares. A pack that needs a level of its own declares it
with its trust class and the level directly below it. These are the `statistics` pack's:

```yaml
levels:
  recomputed: {trust: reproduction, above: none, description: 'A statistic recomputed from the published data agrees with the claim.'}
  reproduced: {trust: reproduction, above: recomputed, description: 'The same estimate from the same code and data.'}
  robust: {trust: reproduction, above: reproduced, description: 'Reproduced, and its sign and significance hold under every declared variation.'}
```

The step's command follows from its inputs: required inputs become arguments, optional ones options.

```console
$ veriphy layers step recompute gdp.csv real_gdp cagr --claimed 0.016 --claim gdp-growth
recompute gdp.csv: agrees
  found 0.0159639, the claim says 0.016 (tolerance 0.0005)
  level: recomputed (reproduction)
  record: .veriphy/runs/recompute/….json
```

A step that compares grants its level only when the comparison runs and agrees. `tolerance: reported` accepts any
value that rounds to the figure the claim reports: half a unit in its last digit. A number, such as `0.005`, fixes the
tolerance instead.

A pack of your own is the same files in a directory of the project, named by path, with its function in a module
beside the `pack.yaml` (`function: tables:statistic`): the directory is on the import path. A subfield of your own
pack goes in a directory inside it, and builds on it with no `requires`:

```text
packs/oncology/pack.yaml
packs/oncology/radiotherapy/pack.yaml     # packs: [./packs/oncology/radiotherapy] brings oncology too
```

### A check as a command

A check can also be a program, run once per call. The `statistics` pack runs the authors' own analysis this way, in a
fresh Python process, so nothing they import leaks into Veriphy:

```yaml
tools:
  python:
    contract: files              # run once per call; the primitive's command names its files
    run: ['{python}', '{pack}/primitives/runner.py']
    version: {command: [--version]}
    timeout: 600

primitives:
  analysis.exec:
    tool: python
    trust: reproduction
    command: ['{file:script}', '{file:data}', '{seed}', '{out}', '{file:variation}']
```

`{pack}` is the pack's directory and `{python}` the Python that runs Veriphy; the program writes its result, as JSON,
to `{out}`. A program that answers in words of its own, such as `found` or `missing`, names the one that means success
with `accepts: [found]` on the step. Without it, `veriphy config check` refuses the step, since every answer would
grant the level.

### What a pack can declare

| Section | Declares |
|---|---|
| `levels` | what a successful check establishes: `trust`, `above`, `description` |
| `tools` | external programs: `run`, `pin`, `version`, `timeout` |
| `primitives` | single operations: a Python `function`, or a `tool` with its `command`; `trust`, `input` and `output` schemas |
| `steps` | checks that are recorded: `kind`, `primitive`, `inputs`, `grants`, `compare`, `accepts`, `seed`, `status`, `help` |
| `scopes` | what a step's digest covers for an input, beyond a value, a file or a directory |
| `conventions` | aspects whose choices exclude each other |
| `workflows` | the order of steps, and what a status does next |
| `commands` | the pack's own programs, run as `veriphy pack <pack> <program>` |
| `requires` | the packs it builds on |

The [configuration reference](../overview/reference.md#packyaml) lists every field. Playbooks and skills go in the pack's `agents/`
directory. Python code is imported only when it's used, so a pack whose tools are missing still loads, and
`veriphy layers primitive list` shows what can't run.

### Publishing a pack

A pack used by one project can live in it and be named by path. To share one, publish a Python package that holds the
`pack.yaml` and declares an entry point:

```toml
[project.entry-points."veriphy.packs"]
epidemiology = "veriphy_epidemiology"
```

After `pip install veriphy-epidemiology`, workspaces name it as `packs: [epidemiology]`.
