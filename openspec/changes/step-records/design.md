# Design

## Context

Graph reasoning already stores runs under a digest of the asserted triples (`asserted.sha256`, `run.json`), and
`sage_test` already writes a seeded record per claim. Lean commands report through messages. `veriphy.core` holds the
workspace helpers and the named exceptions. There is no `python -m veriphy` entry point.

## Goals / Non-Goals

**Goals:**

- One record format and one command for every step that exists today, with replay.
- A record is enough to tell what ran, on what, with which versions, and what came out.

**Non-Goals:**

- The configuration file and tool pinning (`workspace-config`, `tool-contracts`). Until then the record carries the
  versions Veriphy finds.
- The `meaning` step, the R pack and workflows, which have their own changes.
- Removing the existing commands.

## Decisions

### D1. The digest covers content, not paths

The digest is the SHA-256 of a canonical JSON object: the step name, each input as the SHA-256 of its content (a
file, a Lean declaration's statement and proof term, a set of triples), the config digest and the seed. The config
digest is a fixed value derived from Veriphy's version until `workspace-config` lands. Paths are recorded but do not
enter the digest, so moving a file does not invalidate its record.

### D2. A record is written for every outcome

Failures, refusals and timeouts are records too, with the status that says which. A record is never edited. A rerun
with `--rerun` writes nothing new when the output matches, and writes a new record beside the old one, with a suffix,
when it differs, so a changed result is visible.

### D3. Four kinds, and only checks and derived steps carry a level

`agent` steps write an artifact. `evidence` steps find candidates or measure. `check` steps ask a trusted tool.
`derived` steps compute from other records. A record of kind `agent` or `evidence` has no `level` field. This is the
rule that later lets any field add heuristic tools without weakening a level.

### D4. Lean steps run `lake env lean` on a generated file

`elaborate` and `level` write a small Lean file under `.veriphy/runs/tmp/` that imports the target module and runs
the command (`#print axioms`, `#veriphy_levels`), run `lake env lean` from the workspace root, and parse the messages.
One Lean process per step call is the cost, and it keeps Lean's own checking authoritative.

### D5. `reason` points to its certificate

The graph certificate directory stays where it is, because `oo-horn` checks that layout. The step record's outputs
name the directory and the verdict, and its digest is the existing asserted-triples digest combined with the rules
digest.

### D6. Exit codes

0 when the step completed with an accepting status, 1 when the tool refused or found a counterexample, 2 on bad usage,
3 when the result is unchecked. These match the graph commands.

## Risks / Trade-offs

- [Records accumulate] → They are small JSON files. `python -m veriphy records --prune` removes records no current
  input refers to.
- [A Lean process per call is slow] → Replay makes the second call free, and the agent calls Lean steps rarely.
