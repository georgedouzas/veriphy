/-
The old names of the tactic and commands keep working for one minor release, each warning with its new form, and a
script that assigns `proof` or `instances` instead of returning works with a note. Needs a local Sage with `veriphy`,
as `VeriphyTest/SageRun.lean`.
-/
import Mathlib.Tactic.Ring
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import Veriphy

namespace DeprecatedTest

theorem double (n : ℕ) : n + n = 2 * n := by ring

def selfSub : Prop := ∀ x : ℚ, x - x = 0

end DeprecatedTest

/--
warning: `sage_run "…"` is deprecated: use `veriphy certify "…"`; the old form goes in the next minor release
---
warning: veriphy certify: assigning `proof` is deprecated: return found(proof) from run(goal, inputs), or `return` inline
-/
#guard_msgs (warning, error, drop info) in
example (a b : ℚ) (h : a = b) : a - b = 0 := by
  sage_run "proof = 'linear_combination h'"

/--
warning: `sage_run file "…"` is deprecated: use `veriphy certify "….sage"`; the old form goes in the next minor release
-/
#guard_msgs (warning, error, drop info) in
example (a b : ℚ) : 0 ≤ (a - b) ^ 2 := by
  sage_run file "src/veriphy/packs/math/agents/recipes/templates/sos.sage"

/--
warning: `sage_test c "…"` is deprecated: use `#veriphy test c "…"`; the old form goes in the next minor release
---
warning: veriphy test: assigning `instances` is deprecated: return found(instances) from run(goal, inputs), or `return` inline
-/
#guard_msgs (warning, error, drop info) in
sage_test DeprecatedTest.double "instances = [kernel_instance(str(n), proof='rfl', edge=(n == 0)) for n in range(3)]"

/--
warning: `#veriphy_meaning` is deprecated: use `#veriphy meaning`; the old form goes in the next minor release
-/
#guard_msgs (warning, error, drop info) in
#veriphy_meaning DeprecatedTest.selfSub

/--
warning: `#veriphy_levels` is deprecated: use `#veriphy level`; the old form goes in the next minor release
-/
#guard_msgs (warning, error, drop info) in
#veriphy_levels DeprecatedTest

/--
warning: `#veriphy_graph` is deprecated: use `#veriphy export`; the old form goes in the next minor release
-/
#guard_msgs (warning, error, drop info) in
#veriphy_graph DeprecatedTest

/--
warning: `#veriphy_translate` is deprecated: use `#veriphy translate`; the old form goes in the next minor release
-/
#guard_msgs (warning, error, drop info) in
#veriphy_translate fun x : ℝ => Real.sin x

/--
warning: `#veriphy_tables` is deprecated: use `#veriphy translations`; the old form goes in the next minor release
-/
#guard_msgs (warning, error, drop info) in
#veriphy_tables

/--
warning: `#veriphy_coverage` is deprecated: use `#veriphy coverage`; the old form goes in the next minor release
-/
#guard_msgs (warning, error, drop info) in
#veriphy_coverage [DeprecatedTest]

/--
warning: `#veriphy_check_translations` is deprecated: use `#veriphy translations check`; the old form goes in the next minor release
-/
#guard_msgs (warning, error, drop info) in
#veriphy_check_translations

-- the new forms warn about nothing
#guard_msgs (warning, error, drop info) in
example (a b : ℚ) (h : a = b) : a - b = 0 := by
  veriphy certify "return found('linear_combination h')"

#guard_msgs (warning, error, drop info) in
#veriphy test DeprecatedTest.double "return found([kernel_instance(str(n), proof='rfl', edge=(n == 0)) for n in range(3)])"

#guard_msgs (warning, error, drop info) in
#veriphy level DeprecatedTest

-- `veriphy search` shows what a script finds and leaves the goal open
/--
info: veriphy search: the script found
linear_combination h
-/
#guard_msgs (info, error, drop warning) in
example (a b : ℚ) (h : a = b) : a - b = 0 := by
  veriphy search "return found('linear_combination h')"
  linear_combination h

/--
info: veriphy certify "<script>"   close the goal with the proof a script finds (a tactic)
veriphy search "<script>"    show what a proof script finds, closing nothing (a tactic)
#veriphy meaning c            test the statement of c at seeded values
#veriphy test c "<script>"    check c at instances, by the kernel or Sage
#veriphy level p …            the level of each theorem under the prefixes
#veriphy export p …           the formalized claims under the prefixes, for the claim graph
#veriphy translate t          how a term reaches Sage
#veriphy translations [check] the translation tables in force, or a check of the project's entries
#veriphy coverage [p, …]      how much of a corpus's goals the translation reaches
A script is inline, or the name of a saved `.sage` file in `.veriphy/certificates/`.
-/
#guard_msgs in
#veriphy help
