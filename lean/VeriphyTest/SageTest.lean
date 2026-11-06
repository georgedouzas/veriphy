/-
`sage_test` tests: claims tested at instances a script chooses. Needs a local Sage with `veriphy` installed, as
`VeriphyTest/SageRun.lean`; the runs write their records to `.veriphy/tests/`.
-/
import Mathlib.LinearAlgebra.Matrix.Trace
import Mathlib.Analysis.SpecialFunctions.Exp
import Veriphy

namespace SageTestTest

theorem traceDouble (n : ℕ) (A : Matrix (Fin n) (Fin n) ℚ) : Matrix.trace (A + A) = 2 * Matrix.trace A := by
  rw [Matrix.trace_add]; ring

theorem sqNonneg' (x : ℚ) : 0 ≤ x ^ 2 := sq_nonneg x

theorem expGe (x : ℝ) : 1 + x ≤ Real.exp x := by
  have := Real.add_one_le_exp x
  linarith

/-- A proposition with no proof: tested, not proved. -/
def addZero : Prop := ∀ n : ℕ, n + 0 = n

end SageTestTest

-- the template on a statement over `n` and `A`: default instances (`n = 0` among them), each kernel-checked
#guard_msgs (warning, error, drop info) in
sage_test SageTestTest.traceDouble file "trace_double_test.sage"

-- a circular instance and a non-closing one are rejected, the other three accepted
/--
warning: sage_test: an instance is rejected:
  at #[5]: the proof depends on `SageTestTest.sqNonneg'` (through [SageTestTest.sqNonneg']), so it tests nothing
---
warning: sage_test: an instance is rejected:
  at #[2]: the block does not close the instance
-/
#guard_msgs (warning, error, drop info) in
sage_test SageTestTest.sqNonneg' "
instances = [kernel_instance('0', proof='norm_num', edge=True), kernel_instance('3', proof='norm_num'),
  kernel_instance('-1/2', proof='norm_num'), kernel_instance('5', proof='exact SageTestTest.sqNonneg\\' 5'),
  kernel_instance('2', proof='skip')]"

-- too few accepted instances: the run fails and lists the rejected ones
/--
error: sage_test: a test needs 3 accepted instances, one of them an edge case; it has 1
rejected:
  at #[2]: the block does not close the instance
-/
#guard_msgs (warning, error, drop info) in
sage_test SageTestTest.sqNonneg' "instances = [kernel_instance('0', proof='norm_num', edge=True), kernel_instance('2', proof='skip')]"

-- a definition of type `Prop`
#guard_msgs (warning, error, drop info) in
sage_test SageTestTest.addZero "instances = [kernel_instance(str(n), proof='rfl', edge=(n == 0)) for n in range(3)]"

-- oracle instances, evaluated in interval arithmetic: the level is `oracle-test`
#guard_msgs (warning, error, drop info) in
sage_test SageTestTest.expGe "
R = RealIntervalField(64)
instances = [oracle_instance(str(x), lhs=1 + R(x), rhs=R(x).exp(), relation='<=', edge=(x == 0))
  for x in (0, 1, -2, QQ(1) / 2)]"

-- a floating-point comparison is refused, naming the instance
/--
error: sage daemon error: test: CertificateError: the instance at ['1']: floating-point values cannot decide it; use exact or interval ones
-/
#guard_msgs (warning, error, drop info) in
sage_test SageTestTest.expGe "instances = [oracle_instance('1', lhs=RDF(2), rhs=RDF(1).exp(), relation='<=')]"

-- the template, unedited, asks for the proof
/--
error: sage daemon error: test: AssertionError: fill in PROOF (and CASES, unless the default instances fit the binders) in a copy
-/
#guard_msgs (warning, error, drop info) in
sage_test SageTestTest.addZero file "prompts/recipes/templates/test_fallback.sage"

-- the levels the runs recorded
/--
info: SageTestTest.addZero: kernel-test
SageTestTest.expGe: oracle-test
SageTestTest.sqNonneg': kernel-test
SageTestTest.traceDouble: kernel-test
-/
#guard_msgs in
#veriphy_levels SageTestTest
