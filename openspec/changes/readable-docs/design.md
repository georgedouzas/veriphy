# Design

## Model

The model is scikit-learn's documentation. Its tour shows one small thing per section: a sentence, code, and the
result. The user guide explains, and the API reference is generated. Veriphy's pages follow the same split:

| Page | Job |
|---|---|
| Home (README) | what Veriphy does, one check, install, links |
| Install | pip, extras, Sage and Lean for `math`, the Claude Code plugin |
| Getting started | a ten-minute tour: check a number, read the record, see the level, follow a workflow, check how claims fit |
| Tutorial | every command, in order, on the example study |
| User guide | numbered chapters: checks and records, levels, workflows, the claim graph, packs, writing a pack, agents, Python |
| Commands | generated from click |
| Configuration | `veriphy.yaml`, `pack.yaml`, environment variables, files |
| Packs | one page per pack, unchanged in form |

## The example

The tutorial uses the social-science study in `docs/examples/social-science/` for three reasons:

- It needs no Sage and no Lean, only `veriphy[social-science]`.
- It has a claim (`claim.json`), a script, data, a thesaurus and an extracted chapter, so every layer has something to
  work on.
- The `math` pack's commands need Lean and Sage, so they stay on the math page.

## Executed sessions

`tests/docs/test_console.py` runs the docs' console sessions:

- **Parsing.** It reads the `console` blocks of `getting_started.md` and `tutorial.md`. A line starting with `$ `
  is a command, and the lines after it, up to the next command, are its expected output.
- **Running.** It runs the commands with bash in one temporary workspace per page, holding the example's files and a
  git repository, so `claims plan --against HEAD` works.
- **Matching.** It escapes the expected text, turns `…` into a lazy wildcard, and matches the whole output.
  Exit statuses are not compared, because the text says what happened.
- **Skipping.** When `oo-horn` is not set up, the test is skipped. CI sets up the checker, so the test runs there.
- **Coverage.** The coverage test walks the click tree and requires each command path to appear in the tutorial, or
  on the math page for commands only the math pack has. Step commands are checked for the tutorial's packs.

## Generated commands page

`docs/generate_cli.py` runs under `gen-files`, and writes `overview/commands.md`:

- It walks the CLI in a temporary workspace that selects every shipped pack, so every step appears.
- Each command gets a heading, its usage, its help text and a table of its options.
- Because the levels of all packs together don't form one order, the walk loads the steps only. Loading steps does not
  check the level order.
