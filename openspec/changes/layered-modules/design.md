# Design

## Context

`veriphy` has 15,000 lines in nine subpackages. `core` imports nothing; `toolkit` and `graph` import only `core`;
`oracle`, `translations` and `prompts` import `toolkit`; `steps` imports `graph`. The daemon is started as
`sage -python -m veriphy.sage_server` by installed Lean libraries, and skills run `python -m veriphy.prompts path` and
`python -m veriphy.graph`. Sage scripts and tests import `veriphy.toolkit`.

## Goals / Non-Goals

**Goals:**

- A module's path names its layer, and its imports respect the layers, checked by a test.
- Every user-visible path keeps working for one minor release.

**Non-Goals:**

- New behaviour. The operation API, primitives as descriptors and declared steps are later changes.
- Splitting the claim graph's reasoning into primitives. It depends on the vocabulary, and stays in `veriphy.claims`
  until `primitives` gives it a schema.

## Decisions

### D1. Moves with `git mv`, one subpackage at a time

Each move keeps history and is followed by the test suite. Internal imports are rewritten to the new paths, never to
the aliases.

### D2. Aliases are thin modules

An alias module imports the new module, copies its public names, and warns with `DeprecationWarning` once per
process. Running an alias as a program (`python -m veriphy.graph`) runs the new program. A test lists every alias and
checks that it exposes the same names as its target.

### D3. The import rule is a test, not a tool

The test parses every module with `ast`, maps each `veriphy.*` import to a layer (`core` is −1, the facades
`veriphy`, `veriphy.script` and `veriphy.__main__` are exempt, aliases are exempt), and fails naming the module, the
import and both layers. A pack module's layer is the subpackage it sits in.

### D4. Registration instead of imports

`veriphy.steps` exposes `register(step)`. Each layer module and pack registers its steps when imported, and
`veriphy.__main__` imports them all before running the command, so `veriphy.steps` itself imports no higher layer.

### D5. `veriphy.script` is a facade

Until `operation-api` defines the script contract, `veriphy.script` re-exports the `math` pack's script helpers, so
`from veriphy.script import *` gives scripts what `veriphy.toolkit` gave them.

## Risks / Trade-offs

- [Installed Lean libraries start the old daemon path] → `veriphy.sage_server` stays as an alias program for one
  minor release, and the bridge in this release starts the new path.
- [A large diff] → It is moves and import rewrites only, and the suite passes after each subpackage.
