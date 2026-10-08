/-
`sage_sum` / `#sage_sum`: closed forms of range sums.

The division of labor is sharper here than for the other tactics: *discovery*
needs Sage (`#sage_sum "k^2"` prints the closed form of `∑_{k<n} k²`), but the
*proof* needs no certificate at all — once the closed form is in the goal,
induction + `ring1` is a complete, kernel-only check. So `sage_sum n` never
talks to the daemon, and committed proofs are Sage-free by construction.

Works over fields (the closed forms have rational coefficients); for `ℕ`-valued
sums state the theorem over `ℚ` with casts.
-/
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Tactic.Ring
import Veriphy.Translate

namespace Veriphy

open Lean Bridge

/-- `sage_sum n` — prove `∑ k ∈ Finset.range n, f k = F n` (with `F` the
correct closed form, e.g. found by `#sage_sum`) by induction on `n`:
both the base case and `F (n+1) - F n = f n` close by `ring1`. -/
macro "sage_sum " x:ident : tactic =>
  `(tactic|
    (induction $x:ident with
      | zero => rw [Finset.sum_range_zero]; try push_cast
                ring1
      | succ n ih => rw [Finset.sum_range_succ, ih]; try push_cast
                     ring1))

private def termToString (t : Bridge.Term) : String :=
  match t.exps with
  | [0] => t.coeff
  | [1] => s!"{t.coeff} * n"
  | [e] => s!"{t.coeff} * n^{e}"
  | _ => "?"

/-- `#sage_sum "k^2"` — ask Sage for the closed form of `∑_{k=0}^{n-1} f k`
and print a ready-to-prove theorem skeleton (proof: `sage_sum n`). -/
elab "#sage_sum " summand:str : command => do
  let cf ← Bridge.sumClosedForm summand.getString
  let pretty := String.intercalate " + " (cf.map termToString)
  logInfo s!"∑ k ∈ Finset.range n, {summand.getString} = {pretty}\n\
    example (n : ℕ) : ∑ k ∈ Finset.range n, ((k : ℚ))… = {pretty} := by sage_sum n"

end Veriphy
