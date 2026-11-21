---
name: certify
description: Build a kernel-checked certificate for one Lean goal with Veriphy's `veriphy certify` tactic — Sage finds the data (multipliers, squares, cofactors, witnesses, closed forms, intermediate forms), Lean checks the emitted proof. Reuses the project's saved scripts in .veriphy/certificates/ before following a recipe. Use for the computational core of a proof, or when the prove workflow reaches step 3c.
---

Find the playbooks once per session: `sage -python -m veriphy agents path` prints
the directory, written `<prompts>` below. They ship with the installed `veriphy`
package, so they always match its toolkit. If the command fails, ask the user to
run `sage -pip install veriphy` and stop.

Then follow `<prompts>/certify.md` exactly: inspect the problem, reuse a saved
script (`sage -python -m veriphy certificates list`), or else adapt the matching
recipe from `<prompts>/recipes/` (read only that one; copy its template with
`sage -python -m veriphy agents copy recipes/templates/<name>`), run it with
`veriphy certify`, iterate on the combined feedback, commit the emitted replacement, and
keep the script in the project's `.veriphy/certificates/`.

Hard rules:
- Scripts belong to the project being proved (`.veriphy/certificates/`), never to Veriphy.
- A function Veriphy does not translate gets an entry in the project's
  `.veriphy/translations/`, checked with `#veriphy translations check`; never
  edit Veriphy's own tables.
- Commit only the emitted `Try this:` block; never a `veriphy certify` call.
- If the toolkit cannot express the certificate, report
  `blocked-missing-building-block` naming the missing primitive or emitter.
- When no certificate is feasible, test the claim with `#veriphy test` (the `test_fallback` recipe) and name
  its level (`kernel-test` or `oracle-test`); a test is never a certificate.
