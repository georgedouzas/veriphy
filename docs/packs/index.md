# Packs

A pack brings a field to Veriphy: its tools, the primitives and steps over them, the levels they grant, its
conventions, its workflows and its agents' playbooks. The [guide](../overview/user_guide.md#writing-a-pack) explains how
to write one. Veriphy ships four:

| Pack | Requires | Steps | Levels (trust class) | Workflows | Skills |
|---|---|---|---|---|---|
| `core` | | `extract`, `formalize`, `validate`, `reason`, `report` | `none` | | |
| [`lean`](lean.md) | `core` | `check`, `level` | `lean-proof` (kernel) | | |
| [`math`](math.md) | `lean` | `meaning`, `prove` | `oracle-test` (oracle), `kernel-test`, `certificate` (kernel) | `prove-claim`, `verify-paper` | `prove`, `certify`, `research` |
| [`reproduction`](reproduction.md) | `core` | `reproduce`, `vary` | `reproduced`, `robust` (reproduction) | `reproduce-analysis` | `reproduce` |

`core` holds the [claim graph](../overview/user_guide.md#the-claim-graph) and the agent steps every field uses. A
workspace with no `veriphy.yaml` selects `math`, and so `lean` and `core`. `veriphy pack list` lists a workspace's
packs, each after the packs it requires.
