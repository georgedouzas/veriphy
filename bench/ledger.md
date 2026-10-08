# Stub ledger

One row per attempted Physlib stub. This table — especially its failures — is
the project's primary measurement: stubs cleared per dollar, and the ranked map
of which mathlib gaps and missing Sage tactics block physics formalization.

Outcomes: `cleared` | `blocked-mathlib-gap` | `blocked-missing-tactic` | `statement-suspect`

| Date | Stub | Outcome | What was missing | Time | ~Cost |
|------|------|---------|------------------|------|-------|
| 2026-10-08 | `HiggsField.Potential.isBounded_iff_of_𝓵_zero` (tag 6V2K5) | cleared | nothing — no sage tactic needed; attainability API (`const`/`ofReal`) existed, `nlinarith` closed both branches; 1 compile-fix round (`const_normSq` simp lemma) | ~45 min (incl. toolchain setup) | ~$2 |
