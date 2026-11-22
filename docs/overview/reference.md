# Reference

## Commands

Every command takes `--help`, and `veriphy --root <dir> …` runs in another workspace.

```text
veriphy layers primitive list | describe <name> | run <name> --input <file>
veriphy layers step <step> <arguments> [--json] [--rerun]
veriphy layers step list | records [<digest>] [--step <step>]
veriphy layers claims levels | impact | clashes | excludes | confirm | slice | plan | recheck | axioms | vocabulary | checker
veriphy layers workflow list | next <workflow> <target> | run <workflow> <target> [--<input> <value> …]
veriphy layers agents list | path [--pack <pack>] | show <name> | copy <name>
veriphy config show | check
veriphy pack list | <pack> <program> …
veriphy help
```

| Command | Does |
|---|---|
| `veriphy layers primitive list` | every primitive, its trust class, its pack, and whether it can run here |
| `veriphy layers primitive describe <name>` | a primitive's tool, pin, parts and schemas |
| `veriphy layers primitive run <name> --input <file>` | runs one primitive on a JSON input, writing no record |
| `veriphy layers step <step> …` | runs a step and records it; its arguments come from its declaration |
| `veriphy layers step list` | the workspace's steps, with their kind and pack |
| `veriphy layers step records` | the records, or one, by the start of its digest |
| `veriphy layers claims levels [--source s]` | each claim's own and effective level, and what caps it |
| `veriphy layers claims impact <source> <convention>` | every claim that rests on a convention |
| `veriphy layers claims clashes` | claims resting on conventions that exclude each other |
| `veriphy layers claims excludes [--confirm]` | proposes the exclusions between conventions, and records them |
| `veriphy layers claims confirm <source> <subject> <predicate> <object>` | moves a triple to the source's human file |
| `veriphy layers claims slice <source> <claim>` | what an agent needs to work on one claim |
| `veriphy layers claims plan [--against HEAD]` | what an edit to the sources changes in the claims |
| `veriphy layers claims recheck <run>` | checks a stored reasoning run again |
| `veriphy layers claims checker build \| path` | sets up the reasoner and `oo-horn`, or prints where `oo-horn` is |
| `veriphy layers workflow list` | the workspace's workflows and their steps |
| `veriphy layers workflow next <workflow> <target>` | the next step, from the target's records, with the command to type |
| `veriphy layers workflow run <workflow> <target>` | runs the steps that need no agent, until one does |
| `veriphy layers agents path [--pack p]` | where a pack's playbooks are |
| `veriphy config show` | the configuration the packs and `veriphy.yaml` resolve to, with each entry's origin |
| `veriphy config check` | collisions, unresolved names, levels outside one order, steps granting what they can't |
| `veriphy pack list` | the workspace's packs, each after the packs it requires |
| `veriphy pack math certificates list \| show \| tests` | the project's saved certificate scripts and test records |
| `veriphy pack math translations list \| show` | the Lean-to-Sage translation entries in force |

Steps exit with 0 when they accept, 1 when they refuse or find a counterexample, 2 on bad usage and 3 when the result
is unchecked or undecided.

## Steps

| Step | Pack | Kind | Grants |
|---|---|---|---|
| `record-statement <file> [--by name]` | all | agent | |
| `record-proof <file> [--by name]` | `math` | agent | |
| `record-claims <file> [--by name]` | all | agent | |
| `validate` | all | evidence | |
| `reason` | all | check | |
| `appendix <source> [--format markdown\|latex]` | all | derived | |
| `check <file>` | `math` | check | |
| `levels <module> [--prefix p …]` | `math` | derived | the levels Lean reads |
| `sample <file> <declaration> [--informal t] [--values n] [--points json] [--seed s]` | `math` | evidence | |
| `check-concepts <thesaurus>` | all | evidence | |
| `check-factorization <number> <claimed>` | `number-theory` | check | `oracle-test` |
| `check-class-number <polynomial> <claimed>` | `number-theory` | check | `oracle-test` |
| `check-group <group> <property> <claimed>` | `group-theory` | check | `oracle-test` |
| `check-graph <graph> <property> <claimed>` | `graph-theory` | check | `oracle-test` |
| `reproduce <script> <data> [--sha256 d] [--claimed v] [--claim c] [--seed s]` | `statistics` | check | `reproduced` |
| `robustness <script> <data> --variation v … [--sha256 d] [--claim c] [--seed s]` | `statistics` | check | `robust` |
| `check-p-value <test> <statistic> <claimed> [--df d] [--tails 1]` | `statistics` | evidence | |
| `check-mean <mean> <n> [--items k]` | `statistics` | evidence | |
| `check-reliability <data> --item c … [--claimed a]` | `social-science` | evidence | |
| `recompute <data> <column> <statistic> [--claimed v] [--periods n]` | `economics` | check | `recomputed` |
| `check-regression <data> <formula> <coefficient> [--entity e --time t] [--covariance c] [--claimed v]` | `econometrics` | check | `recomputed` |
| `check-hazard-ratio <data> <duration> <event> --covariate c … [--claimed v]` | `epidemiology` | check | `recomputed` |
| `check-median-survival <data> <duration> <event> [--group col=value] [--claimed v]` | `epidemiology` | check | `recomputed` |
| `check-units <formula> --unit s=u …` | `physics` | check | `dimensionally-consistent` |
| `check-constant <name> [--claimed v]` | `physics` | evidence | |
| `check-prediction <observable> <claimed> [--uncertainty u] [--coefficient c=v …]` | `particle-physics` | check | `prediction-recomputed` |
| `run-coefficients <coefficient> <to-scale> --coefficient c=v … [--claimed v]` | `particle-physics` | check | `prediction-recomputed` |
| `check-pdg <particle> <property> <claimed>` | `particle-physics` | evidence | |
| `check-metric <coordinates> <metric> <property>` | `general-relativity` | check | `curvature-checked` |
| `check-sequence <fasta> [--length n] [--gc f] [--motif m] [--protein p]` | `life-sciences` | check | `sequence-checked` |
| `check-variant <vcf> <variant> [--sample s] [--genotype g]` | `genomics` | check | `genomic-data-checked` |
| `check-coverage <alignments> <region> [--quality q] [--claimed d]` | `genomics` | check | `genomic-data-checked` |
| `check-molecule <smiles> [--formula f] [--mass m]` | `chemistry` | check | `structure-checked` |
| `check-reaction <reaction>` | `chemistry` | check | `structure-checked` |

A number a claim reports keeps its digits: with `tolerance: reported`, `--claimed 0.080` agrees within 0.0005 and
`--claimed 20` within 0.5.

## Extras

Each pack's libraries install with its extra: `pip install 'veriphy[<pack>]'`, or `veriphy[all]` for every pack.

| Extra | Installs |
|---|---|
| `statistics` | pandas, SciPy, statsmodels |
| `social-science` | `statistics`, pingouin |
| `economics` | `statistics` |
| `econometrics` | `economics`, linearmodels |
| `epidemiology` | `statistics`, lifelines |
| `physics` | pint, SciPy |
| `particle-physics` | `physics`, flavio, wilson, particle |
| `general-relativity` | `physics`, EinsteinPy, SymPy |
| `life-sciences` | Biopython, pronto |
| `genomics` | `life-sciences`, pysam |
| `chemistry` | RDKit |

The `math` pack's SageMath is the Python Veriphy is installed into, and its Lean library a Lake dependency.

## `veriphy.yaml`

A workspace's file has the same sections as a `pack.yaml`, plus `packs`. Every key is optional:

```yaml
version: 1
packs: [physics, chemistry, ./packs/mine]   # shipped packs by name, others by path or entry point
levels:
  structure-checked: {above: dimensionally-consistent}   # settle the order between two packs' levels
tools:
  python: {timeout: 1200}                    # change any entry a pack declares
```

Without the file, a workspace uses `packs: [math]`.

## `pack.yaml`

```yaml
version: 1
name: <pack>
requires: [<pack>, …]     # besides the pack it is nested in, which it always builds on
```

### `levels`

```yaml
levels:
  <level>: {trust: kernel | checker | reproduction | oracle, above: <level>, description: <text>}
```

### `tools`

```yaml
tools:
  <tool>:
    contract: files                    # a command run once per call, writing one JSON result to {out}
    run: [<program>, <argument>, …]    # {python} is Veriphy's Python, {pack} the pack's directory,
                                       # {env:NAME|default} a variable
    pin: {version: <v>} | {commit: <sha>, sha256: <hash>} | {image: <name>@sha256:<digest>}
    version: {command: [<argument>, …], pattern: <regular expression>}
    timeout: <seconds>
```

### `primitives`

```yaml
primitives:
  <name>:
    function: <module>:<function>      # a Python function, called in-process
    # or
    tool: <tool>
    command: [<argument>, …]           # {input}, {out}, {seed}, {file:<input>}
    trust: kernel | checker | reproduction | oracle | measurement | search
    seed: param | placeholder          # how a random primitive takes its seed
    input: <JSON Schema>
    output: <JSON Schema>
  <name>: {composite: <module>}        # several primitives combined, written in Python
```

### `steps`

```yaml
steps:
  <step>:
    kind: check | evidence | derived | agent
    primitive: <primitive>             # none for an agent step
    help: <one line>
    grants: <level>
    compare: {field: <output>, against: <input>, tolerance: <number> | reported}
    accepts: [<status>, …]             # the tool's words for success, when they aren't Veriphy's
    status: <output field>             # where the status is, `status` by default
    seed: true                         # the step takes --seed, which enters the digest
    inputs:
      <input>:
        scope: value | file | files | <scope>   # what the record's digest covers
        path: true                     # resolved from the workspace root
        optional: true                 # an option rather than an argument
        type: string | integer | number | json
        default: <value>
        many: true                     # repeatable, collecting a list
        flag: --<spelling>
        record: true                   # kept in the record, not sent to the primitive
        help: <one line>
  <step>: {code: <module>}             # a step written in Python, which registers itself
```

### `scopes`, `conventions`, `workflows`, `commands`

```yaml
scopes:
  <scope>: {function: <module>:<function>}     # takes the workspace root and the value
conventions:
  <aspect>: [<convention>, <convention>, …]    # choices that exclude each other
workflows:
  <workflow>:
    - <step>
    - <step>: {<status>: stop | <step>, attempts: <n>, exhausted: stop | <step>, when: {without: <trust class>}}
commands:
  <program>: {command: <module>:<attribute>, help: <one line>}   # veriphy pack <pack> <program>
```

## Environment variables

| Variable | Effect |
|---|---|
| `VERIPHY_GRAPH_SETUP` | `off` stops the claim graph fetching or building its reasoner and checker |
| `VERIPHY_OO_HORN` | use this `oo-horn` binary |
| `VERIPHY_SAGE_CMD` | the `sage` executable, if it isn't on `PATH` (the `math` pack) |
| `VERIPHY_SAGE_SESSION` | a development copy of the Sage session's entry point (the `math` pack) |
| `VERIPHY_SAGE_TIMEOUT` | seconds allowed per Sage request, 150 by default (the `math` pack) |

## Files

| Path | Holds |
|---|---|
| `veriphy.yaml` | the workspace's packs and changes to them; it marks the workspace's root |
| `.veriphy/runs/` | the records, out of git |
| `.veriphy/graph/sources/` | the claim graph's sources, one file per source and provenance |
| `.veriphy/graph/runs/` | the reasoning runs and their certificates |
| `.veriphy/graph/appendix/` | the verification appendices |
| `.veriphy/certificates/` | the `math` pack's saved certificate scripts |
| `.veriphy/translations/` | the `math` pack's project translation entries |
