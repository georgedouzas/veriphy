# Proposal

## Why

The commands were named after how Veriphy works, not after what they do. `meaning` samples a statement, `vary` tests
robustness, and `formalize`, `prove` and `extract` only record a file an agent wrote. `validate`, `reason` and the
appendix had two commands each. `reproduce` made the user type a SHA-256, `vary` took JSON on the command line, and
`workflow run` took `--input name=value`. The output (`check: accepted` and a hashed path) said neither what was
checked nor what to do next. The README and the guide could only document these names, so they read as cryptic too.

## What Changes

- **BREAKING** Renames, the same in the shell, in Python and in Lean:
  - the step `meaning` is `sample` (`#veriphy sample c` in Lean; the composite primitive `sample`; the Sage method
    `sample`);
  - the step `level` is `levels` (`#veriphy levels P`; the primitive `lean.levels`);
  - the step `vary` is `robustness`, taking `--variation "<formula>"`, once per variation;
  - the agent steps `formalize`, `prove` and `extract` are `record-statement`, `record-proof` and `record-claims`;
  - the step `report` is `appendix`.
- **BREAKING** `veriphy layers claims` drops `validate`, `reason` and `appendix`: the steps of those names run them,
  and record them.
- `reproduce` computes the data's SHA-256 and records it; `--sha256` refuses data whose digest differs.
- A comparison grants its level only when it ran and agreed, and `tolerance: reported` accepts any value that rounds
  to the figure the claim reports.
- A step names its tool's words for success with `accepts`, and `config check` refuses a granting step over a tool with
  words of its own that names none, as it refuses any unknown field of a step or an input.
- A level a record grants to a claim is asserted in the claim graph, so the checked reasoning and every effective
  level take it into account.
- Every command reports a Veriphy error or a missing file in one line, with exit status 1, not a traceback.
- `veriphy layers workflow run <workflow> <target>` takes each step input as an option (`--declaration t`).
- Every step prints, in plain words, what it checked, the result with its details, the level with its trust class,
  and the record; a workflow command prints the next step as the exact command to run. `--json` is unchanged.
- The README and the guide are rewritten around tasks: a first session, then one section per task, then reference.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `core/step-records`: the step command's output.
- `core/workflows`: step inputs as options, and the next step as a command.
- `certificates/meaning-check`: the `sample` step and `#veriphy sample`.
- `core/steps`: comparison, accepted statuses.
- `research/certified-graph-reasoning`: levels from records in the reasoning.

## Impact

- Packs: `core`, `lean`, `math` and `reproduction` (`pack.yaml` and code); the Lean commands and bridge; the Sage
  methods.
- `veriphy.steps._cli`, `veriphy.workflows`, `veriphy.claims._cli`.
- Skills, playbooks, the README, the guide, the pack pages, CI and the tests.
