---
name: research
description: Verify a research source (a LaTeX or Markdown draft, a chapter or a paper) with Veriphy's research claim graph — extract its claims, conventions and dependencies, triage them, prove or test them with their graph slices as context, export the Lean results, and report every claim's effective verification level, clashes and suspects in a verification appendix, with each graph conclusion checked by the Lean checker oo-horn. Use when asked to verify, check or audit a paper, a chapter or a set of results as a whole.
---

First resolve the **Veriphy repo root**, in this order:

1. `$VERIPHY_HOME`, if set;
2. `${CLAUDE_PLUGIN_ROOT}`, when this skill runs from the installed plugin
   (the plugin root *is* a clone of the Veriphy repo);
3. otherwise ask the user where they cloned Veriphy.

Verify the installation once per session: `sage -python -m veriphy.graph --help`
runs. If it does not, ask the user to run `sage -pip install 'veriphy[graph]'`,
the only installation command. The first `reason` sets up the reasoner and the
checker by itself and says so, which takes minutes where the checker is built.

Then follow the playbook at `<root>/prompts/research.md` exactly as written:
extract → validate → triage → prove with slices → export → reason and report.
Extraction follows `<root>/prompts/research/extraction.md`, triage follows
`<root>/prompts/research/triage.md`, and proving follows the `prove` skill.

Hard rules:
- Write only `.agent.ttl` files. Confirming an assertion is the user's act.
- Report a graph conclusion with the checker's verdict word, or as `unchecked`.
  Never report the absence of a clash as checked.
- Never report a claim as proved when its effective level is below `certificate`.
