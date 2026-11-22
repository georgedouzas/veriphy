# Design

## Context

The layered architecture kept the old names as thin wrappers: Python alias modules re-exporting the new ones, Lean
syntaxes the new forms expand to, a verb table, the `proof` variable in scripts and the Sage session's earlier wire format.

## Decisions

- **The new Lean forms own the implementation.** `veriphy certify`, `#veriphy test`, `#veriphy sample` and
  `#veriphy translations check` are macros over `sage_run`, `sage_test`, `#veriphy_meaning` and
  `#veriphy_check_translations`. Each becomes an `elab_rules` calling the core function the old syntax called
  (`sageRunCore`, the test, meaning and check elaborators), and the old syntax is deleted. The Sage-free verbs in
  `Kit/Operation.lean` get the same treatment.
- **The proof-term marker stays.** `veriphy_certified` is how `#veriphy levels` sees that a recipe built a proof; it
  is not an old name, and saved proofs emitted by `veriphy certify` use it.
- **Unknown, not redirected.** A removed name fails the way any unknown name fails (unknown syntax, unknown command,
  `ModuleNotFoundError`), so no table of old names survives.
- **Invalid request, not parse error.** A JSON object without `"jsonrpc": "2.0"` is valid JSON, so the Sage session
  answers -32600 (invalid request), as JSON-RPC 2.0 defines.

## Risks

- Saved proofs in other projects (`sage_run file "…"`) and saved scripts importing `veriphy.toolkit` stop working.
  The changelog lists each rename, and the replacements are one-to-one.
