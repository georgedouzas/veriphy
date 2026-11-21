---
name: prove
description: Produce a machine-verified Lean proof of a physics or math statement the user supplies — formal Lean, an informal statement to formalize first, or a backlog item from a repo the user provides. Uses mathlib tactics plus certificates it builds with Veriphy's `veriphy certify` tactic and recipes (Sage untrusted, kernel-checked), validates statements numerically before proving, and reports proved / blocked / statement-suspect back to the user. Use when asked to prove, verify, or formalize a statement.
---

Find the playbooks once per session: `sage -python -m veriphy layers agents path` prints
the directory, written `<prompts>` below. They ship with the installed `veriphy`
package, so they always match its toolkit. If the command fails, ask the user to
run `sage -pip install veriphy` and stop.

Verify the installation once per session: the Sage session answers
`echo '{"id":1,"method":"ping"}' | sage -python -m veriphy.packs.math.primitives.sage`, and
the Lean workspace you prove in requires Veriphy and builds. If either fails,
walk the user through the README's install section instead of proceeding.

Sequence the work with the `prove-claim` workflow: `veriphy layers workflow next prove-claim <file>` names the next step, and
`veriphy layers workflow run prove-claim <file> --input declaration=<name>` runs the steps that are not yours until it needs you
(`formalize`, `prove`: record your file with `veriphy layers step <step> <file> --by agent`). Take no step it did not name.

Then follow the playbook at `<prompts>/prove.md` exactly as written:
formalize (with round-trip and numeric lie detection) → compile-fix → prove →
verify → report. For step 3c (building a certificate) follow the `certify`
skill (`<prompts>/certify.md`).

Hard rules:
- The user supplies the target and owns the outcome. Never open PRs, commit to
  target repos beyond what was asked, or keep score anywhere.
- Never invent a *definition*; flag it to the user and stop.
- When the claim is in the workspace's research claim graph, state it under the
  conventions its slice names (`veriphy layers claims slice <source> <label>`).
- The final proof must contain no `sorry` and no live Sage call — only the
  Sage-free `Try this:` replacements `veriphy certify` emits.
- Certificate scripts go in the project's `.veriphy/certificates/`, never in Veriphy.
- A failure is a report (`blocked-library-gap` / `blocked-missing-building-block` /
  `statement-suspect`), stated precisely, not a silent stop.
- Recipe selection runs first. Only when no certificate is feasible does `#veriphy test` check the claim,
  and the report names its level (`tested`, with `kernel-test` or `oracle-test`), never `proved`.
