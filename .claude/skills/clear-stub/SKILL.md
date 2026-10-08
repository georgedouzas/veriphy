---
name: clear-stub
description: Clear one Physlib informal_lemma stub end to end — formalize the statement, validate it numerically via Sage, prove it (mathlib tactics + Veriphy sage_* certificate tactics), verify with lake build, log the outcome in bench/ledger.md, and open a PR. Use when asked to work on Physlib stubs, the formalization backlog, or "clear a stub".
---

Follow the playbook in `prompts/clear-stub.md` at the repo root, exactly as
written. It defines the loop (pick → formalize → lie-detect → compile-fix →
prove → verify → log → PR), the proof-attempt budget, and the outcome taxonomy
for `bench/ledger.md`.

Hard rules the playbook imposes:
- Never invent a *definition*; flag it for human design review and pick
  another stub.
- Never commit a proof containing `sorry` or a live Sage call; only
  `Try this:` reconstructed proofs may land.
- A failed stub is a required ledger row, not a silent skip — the failure
  taxonomy (mathlib gap vs missing tactic vs suspect statement) is the
  project's primary output.
