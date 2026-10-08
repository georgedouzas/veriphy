---
name: prove
description: Produce a machine-verified Lean proof of a physics or math statement the user supplies — formal Lean, an informal statement to formalize first, or a backlog item from a repo the user provides. Uses mathlib tactics plus Veriphy's sage_* certificate tactics (Sage untrusted, kernel-checked), validates statements numerically before proving, and reports proved / blocked / statement-suspect back to the user. Use when asked to prove, verify, or formalize a statement.
---

Follow the playbook in `prompts/prove.md` at the repo root, exactly as written:
formalize (with round-trip and numeric lie detection) → compile-fix → prove →
verify → report.

Hard rules:
- The user supplies the target and owns the outcome. Never open PRs, commit to
  target repos beyond what was asked, or keep score anywhere.
- Never invent a *definition*; flag it to the user and stop.
- The final proof must contain no `sorry` and no live Sage call — only the
  Sage-free `Try this:` replacements the tactics emit.
- A failure is a report (`blocked-library-gap` / `blocked-missing-tactic` /
  `statement-suspect`), stated precisely, not a silent stop.
