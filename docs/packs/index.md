# Packs

A pack brings one field to Veriphy. It is a directory with a `pack.yaml` that declares how the field checks its
claims: the tools it runs, the operations on them, the steps that record each check, the levels a check can grant, the
conventions its claims assume, and the workflows that order the steps. Beside it sit any Python functions the pack
needs and the playbooks its agents follow.

Veriphy itself is not a pack: records, the claim graph, workflows and the agent steps (`record-statement`,
`record-proof`, `record-claims`) are in every workspace, whatever its packs.

## The shipped packs

| Pack | Field | Steps | Levels | Needs |
|---|---|---|---|---|
| [`math`](math.md) | mathematics, and mathematical physics, in Lean | `check`, `levels`, `sample`, `record-proof` | `oracle-test` < `kernel-test` < `lean-proof` < `certificate` | Lean, SageMath |
| [`social-science`](social_science.md) | studies with data: their analysis, its robustness, their constructs | `reproduce`, `robustness`, `check-concepts` | `reproduced` < `robust` | Python |

## Choosing packs

A workspace names its packs in `veriphy.yaml`, at its root:

```yaml
version: 1
packs: [social-science]
```

Without a `veriphy.yaml`, a workspace uses `math`. That is the default for a Lean project.

A pack is named in one of three ways:

- the name of a shipped pack: `math`, `social-science`;
- the name a Python package registers under the `veriphy.packs` entry point, for a pack published on PyPI;
- the path of a directory holding a `pack.yaml`: `./packs/economics`, for a pack of your own.

`veriphy pack list` shows the packs a workspace uses, and `veriphy config show` shows everything they declare, with
the pack each entry comes from. `veriphy config check` checks that it all fits together.

## Combining packs

A workspace can use several packs. A study in economics that cites a theorem might use:

```yaml
version: 1
packs: [math, ./packs/economics]
```

Packs are applied in order, each after the packs it `requires`. When two packs that don't require each other declare
the same entry, `veriphy config check` names both, and the workspace decides by declaring that entry itself.

The levels of a workspace form one order, from `none` up, so that a claim's effective level, the lowest among
everything it rests on, is well defined. Each pack places its levels with `above`. Two packs that each put a level
directly above `none` leave the order open:

```console
$ veriphy config check
config: levels quoted and recomputed are both directly above 'none': set one's `above`
```

The workspace settles it:

```yaml
version: 1
packs: [./packs/economics, ./packs/history]
levels:
  quoted: {above: recomputed}
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

- **What is checked?** A statistic recomputed from data, a passage found in a source, a proof accepted by Lean.
- **What does a successful check establish?** That becomes a level, with a trust class saying what kind of evidence it
  is. A level must be one the check can establish: a recomputation can't grant a proof.
- **What do claims assume?** Choices that exclude each other, such as two editions of a text or two measures of one
  construct, become conventions.

The two examples below are complete packs, in
[`docs/examples/packs/`](https://github.com/georgedouzas/veriphy/tree/main/docs/examples/packs), and Veriphy's test
suite runs them.

### Economics: recompute a statistic

A paper reports the mean growth of the countries in its table. The `economics` pack recomputes such a statistic from
the published data and compares it with the claim. The check is a Python function, so there is nothing to install:

```python
# economics_functions.py
import csv
from pathlib import Path


def mean(inputs):
    with Path(inputs['data']).open(newline='') as handle:
        values = [float(row[inputs['column']]) for row in csv.DictReader(handle)]
    return {'status': 'reported', 'mean': sum(values) / len(values), 'rows': len(values)}
```

The `pack.yaml` declares a level, the function as a primitive, and a step over it:

```yaml
version: 1
name: economics

levels:
  recomputed:
    trust: reproduction        # the same number again from the same data: evidence of the reproduction kind
    above: none
    description: The statistic was recomputed from the published data and agrees with the claim.

primitives:
  table.mean:
    function: economics_functions:mean
    trust: reproduction
    input:
      type: object
      required: [data, column]
      properties: {data: {type: string}, column: {type: string}}
    output:
      type: object
      required: [status, mean, rows]

steps:
  recompute:
    kind: check
    primitive: table.mean
    grants: recomputed
    compare: {field: mean, against: claimed, tolerance: 0.005}
    help: recompute the mean of a column from the data, and compare it with the value the claim reports
    inputs:
      data: {scope: file, path: true, help: the published data, as CSV}
      column: {help: the column}
      claimed: {type: number, optional: true, record: true, help: the mean the claim reports}
      claim: {optional: true, record: true, help: 'the claim, so its level follows the record'}

workflows:
  check-table: [record-claims, recompute]
```

The step's command follows from its inputs: required inputs become arguments, optional ones options.

```console
$ veriphy layers step recompute table.csv growth --claimed 3.03 --claim mean-growth
recompute table.csv: agrees
  found 3.033333333333333, the claim says 3.03 (tolerance 0.005)
  level: recomputed (reproduction)
$ veriphy layers step recompute table.csv growth --claimed 3.5
recompute table.csv: differs from the claim
  found 3.033333333333333, the claim says 3.5 (tolerance 0.005)
```

A step that compares grants its level only when the comparison runs and agrees. `tolerance: reported` would instead
accept any value that rounds to the figure the claim reports, as the `social-science` pack does.

### History: find a quotation in its source

A biography quotes a letter. The `history` pack checks that the quoted passage appears, word for word, in the source
it is attributed to. This time the check is a command-line tool, `find_quote.py`, shipped beside the `pack.yaml`. It
reads its input from a JSON file and writes its result to another:

```yaml
version: 1
name: history

levels:
  quoted:
    trust: checker             # a deterministic check of a fact about the source
    above: none
    description: The passage appears word for word in the cited source.

conventions:
  edition: [first-edition, second-edition]

tools:
  find-quote:
    contract: files            # run once per call: reads {input}, writes {out}
    run: ['{python}', '{pack}/find_quote.py']

primitives:
  quote.find:
    tool: find-quote
    command: ['{input}', '{out}']
    trust: checker
    input:
      type: object
      required: [source, passage]
      properties: {source: {type: string}, passage: {type: string}}
    output:
      type: object
      required: [status]
      properties: {status: {enum: [found, missing]}, line: {type: integer}}

steps:
  verify-quote:
    kind: check
    primitive: quote.find
    grants: quoted
    accepts: [found]           # the tool's own word for success; anything else is refused
    help: check that a passage appears, word for word, in its source
    inputs:
      source: {scope: file, path: true, help: the source, as plain text}
      passage: {help: the quoted passage}
      claim: {optional: true, record: true, help: 'the claim, so its level follows the record'}
```

```console
$ veriphy layers step verify-quote novel.txt "best of times, it was the worst"
verify-quote novel.txt: found
  level: quoted (checker)
$ veriphy layers step verify-quote novel.txt "age of wisdom"
verify-quote novel.txt: refused
  the tool said: missing
```

The tool answers `found` or `missing`, words Veriphy doesn't know, so the step says which one means success with
`accepts`. Without it, `veriphy config check` refuses the pack, since every answer would grant the level.

The `edition` convention lets claims say which edition they quote. A claim resting on quotations from both editions
is then reported as a clash in the claim graph.

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

The [reference](../overview/reference.md#packyaml) lists every field. Playbooks and skills go in the pack's `agents/`
directory. Python code is imported only when it's used, so a pack whose tools are missing still loads, and
`veriphy layers primitive list` shows what can't run.

### Publishing a pack

A pack used by one project can live in it and be named by path. To share one, publish a Python package that holds the
`pack.yaml` and declares an entry point:

```toml
[project.entry-points."veriphy.packs"]
economics = "veriphy_economics"
```

After `pip install veriphy-economics`, workspaces name it as `packs: [economics]`.
