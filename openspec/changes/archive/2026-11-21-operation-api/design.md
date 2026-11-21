# Design

## Context

After `layered-modules`, the step registry holds every step, and `veriphy.script` re-exports the `math` pack's helpers.
`sage_run` is a tactic that runs a script and closes the goal with the term the script sets as `proof`; `sage_test` is
a command that tests a claim at instances. The daemon runs a script with the helpers and the goal's sides (`lhs`,
`rhs`, `problem`) bound as globals.

## Goals / Non-Goals

**Goals:**

- One way to call an operation from each surface, and the same verb names on all of them.
- One way to write a script, in any language.

**Non-Goals:**

- Removing the old names in this release. They warn for one minor release.
- New operations. Every verb here exists today under another name, apart from `formalize` and `extract`, which are
  named now and recorded by `declarative-steps`.

## Decisions

### D1. Tactic for goals, command for claims

A tactic acts on the current goal, so `veriphy certify` and `veriphy search` are tactics. A command acts on a named
claim or the project, so `meaning`, `test`, `level`, `export` and the translation verbs are `#veriphy` commands. The
verb is a non-reserved keyword after `veriphy`, so a pack can add one with an `elab_rules` entry, and `#veriphy help`
lists what is registered.

### D2. The result has one shape

`Result` has `verb`, `target`, `status`, `outputs`, `level` and `record`, the last two `None` for primitives and
evidence. The shell prints the record's path and status, or the record with `--json`, and exits by the status as the
step command does.

### D3. A script is a function

```python
SCRIPT = {"name": "sos", "serves": "certify", "inputs": {"degree": "int"}}

def run(goal: Goal, inputs: dict) -> Result:
    ...
    return found(proof)
```

`goal` is the goal proposition scripts already see (`goal.poly`, `goal.rel`, `goal.text`, `goal.expr`), so a
template's body keeps its meaning inside `run`; the whole problem stays bound as `problem`. `found(x)` carries the
artifact the verb needs (a proof term for `certify`, instances for `test`), `refuted(values)` says the goal is false
at the values, and `unknown(reason)` says nothing was found. For `certify`, `found` leads to Lean's check, `refuted`
to the status `counterexample` and `unknown` to `unknown`.

### D4. Inline scripts are bodies

`veriphy certify "return found(tactic(nlinarith_hint(goal)))"` runs the text as the body of `run`, with `goal` and
`inputs` bound. A body that assigns `proof` instead is the deprecated form, accepted as `found(proof)` with a warning.

### D5. Old names are syntax aliases

`sage_run` and the `#veriphy_*` commands stay as syntax that expands to the new form and logs a deprecation warning
naming it. The deprecated tests in `VeriphyTest` keep one test per old name, and every other test uses the new forms.

## Risks / Trade-offs

- [The deprecation warnings change `#guard_msgs` output in users' tests] → The warning names the new form, so the fix
  is mechanical, and the old forms keep elaborating.
- [Templates are rewritten] → Each template is exercised by a Lean test, so the rewrite is checked by the suite.
