# Configuration

This page lists every field of the two configuration files, `veriphy.yaml` and `pack.yaml`, and the environment
variables and files Veriphy uses. The [commands](commands.md) page lists every command, and
[installation](install.md) every extra.

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

## Numbers in claims

A number given to `--claimed` keeps its digits. With `tolerance: reported`, `--claimed 0.080` agrees within 0.0005
and `--claimed 20` within 0.5.
