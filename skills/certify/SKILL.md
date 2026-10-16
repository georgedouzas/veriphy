---
name: certify
description: Build a kernel-checked certificate for one Lean goal with Veriphy's sage_run — Sage finds the data (multipliers, squares, cofactors, witnesses, closed forms, intermediate forms), Lean checks the emitted proof. Reuses the project's saved scripts in .veriphy/certificates/ before following a recipe. Use for the computational core of a proof, or when the prove workflow reaches step 3c.
---

Resolve the Veriphy repo root as the `prove` skill does (`$VERIPHY_HOME`, else
`${CLAUDE_PLUGIN_ROOT}`, else ask). Then follow `<root>/prompts/certify.md`
exactly: inspect the problem, reuse a saved script
(`sage -python -m veriphy.certificates list`), or else adapt the matching recipe
from `<root>/prompts/recipes/` (read only that one), run it with `sage_run`,
iterate on the combined feedback, commit the emitted replacement, and save the
script in the project's `.veriphy/certificates/`.

Hard rules:
- Scripts belong to the project being proved (`.veriphy/certificates/`), never to Veriphy.
- A function Veriphy does not translate gets an entry in the project's
  `.veriphy/translations/`, checked with `#veriphy_check_translations`; never
  edit Veriphy's own tables.
- Commit only the emitted `Try this:` block; never a `sage_run` call.
- If the toolkit cannot express the certificate, report
  `blocked-missing-building-block` naming the missing primitive or emitter.
- When no certificate is feasible, test the claim with `sage_test` (the `test_fallback` recipe) and name
  its level (`kernel-test` or `oracle-test`); a test is never a certificate.
