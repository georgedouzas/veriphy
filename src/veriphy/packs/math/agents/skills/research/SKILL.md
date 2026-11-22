---
name: research
description: Verify a research source (a LaTeX or Markdown draft, a chapter or a paper) with Veriphy's research claim graph — extract its claims, conventions and dependencies, triage them, prove or test them with their graph slices as context, export the Lean results, and report every claim's effective verification level, clashes and suspects in a verification appendix, with each graph conclusion checked by the Lean checker oo-horn. Use when asked to verify, check or audit a paper, a chapter or a set of results as a whole.
---

Find the playbooks once per session: `sage -python -m veriphy layers agents path` prints
the directory, written `<prompts>` below. They ship with the installed `veriphy`
package, so they always match its toolkit. If the command fails, ask the user to
run `sage -pip install veriphy` and stop.

The claim graph comes with every install. The first `reason` sets up the
reasoner and the checker by itself and says so, which takes minutes where the
checker is built.

Sequence the work with the `verify-paper` workflow: `veriphy layers workflow next verify-paper <source>` names the next step, and
`veriphy layers workflow run verify-paper <source>` runs the steps that are not yours until it needs you.

Then follow `<prompts>/research.md` exactly as written:
extract → validate → triage → prove with slices → export → reason and report.
Extraction follows `<prompts>/research/extraction.md`, triage follows
`<prompts>/research/triage.md`, and proving follows the `prove` skill.

Hard rules:
- Write only `.agent.ttl` files. Confirming an assertion is the user's act.
- Report a graph conclusion with the checker's verdict word, or as `unchecked`.
  Never report the absence of a clash as checked.
- Never report a claim as proved when its effective level is below `lean-proof`.
