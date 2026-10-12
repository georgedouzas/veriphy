---
name: prove
description: Produce a machine-verified Lean proof of a physics or math statement the user supplies — formal Lean, an informal statement to formalize first, or a backlog item from a repo the user provides. Uses mathlib tactics plus certificates it builds with Veriphy's sage_run and recipes (Sage untrusted, kernel-checked), validates statements numerically before proving, and reports proved / blocked / statement-suspect back to the user. Use when asked to prove, verify, or formalize a statement.
---

First resolve the **Veriphy repo root**, in this order:

1. `$VERIPHY_HOME`, if set;
2. `${CLAUDE_PLUGIN_ROOT}`, when this skill runs from the installed plugin
   (the plugin root *is* a clone of the Veriphy repo);
3. otherwise ask the user where they cloned Veriphy.

Verify the installation once per session: the Sage daemon answers
`echo '{"id":1,"method":"ping"}' | sage -python -m veriphy.sage_server`, and
the Lean workspace you prove in requires Veriphy and builds. If either fails,
walk the user through the Setup section of the repo's README.md instead of
proceeding.

Then follow the playbook at `<root>/prompts/prove.md` exactly as written:
formalize (with round-trip and numeric lie detection) → compile-fix → prove →
verify → report. For step 3c (building a certificate) follow the `certify`
skill (`<root>/prompts/certify.md`).

Hard rules:
- The user supplies the target and owns the outcome. Never open PRs, commit to
  target repos beyond what was asked, or keep score anywhere.
- Never invent a *definition*; flag it to the user and stop.
- The final proof must contain no `sorry` and no live Sage call — only the
  Sage-free `Try this:` replacements `sage_run` emits.
- Certificate scripts go in the project's `certificates/`, never in Veriphy.
- A failure is a report (`blocked-library-gap` / `blocked-missing-building-block` /
  `statement-suspect`), stated precisely, not a silent stop.
