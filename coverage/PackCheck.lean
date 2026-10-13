/-
Checks of the `physlib` pack against the pinned Physlib: the pack activates, every constant it names exists
(no problem is reported), and Physlib's derivative notations translate.
-/
import Physlib
import Veriphy

/--
info: mathlib: 26 functions, 2 constants, 5 coercions, 9 rewrites
physlib: 2 functions, 0 constants, 1 coercions, 6 rewrites
-/
#guard_msgs in
#veriphy_tables

variable (t₀ : Time) (p : Space 2)

-- `∂ₜ`: the derivative is taken in the time coordinate, at the number `t₀.val`
/--
info: sage: diff((d0_)^(2), d0_).subs({d0_: x0})
atoms:
  x0 := t₀.val : ℝ
conditions:
-/
#guard_msgs in
#veriphy_translate Time.deriv (fun t : Time => t.val ^ 2) t₀

-- `∂[0]`: the partial derivative in the first coordinate, every coordinate then set to the point's
/--
info: sage: diff(((c0_)^(2) * c1_), c0_).subs({c0_: x0, c1_: x1})
atoms:
  x0 := p.val 0 : ℝ
  x1 := p.val 1 : ℝ
conditions:
-/
#guard_msgs in
#veriphy_translate Space.deriv 0 (fun x : Space 2 => x 0 ^ 2 * x 1) p

-- `∂ₜ` of an unknown trajectory: the derivative of a Sage symbolic function, at the number `t₀.val` throughout
/--
info: sage: (diff(F_x(s_), s_, 1).subs({s_: x0}) + (2 * F_x(x0)))
atoms:
  x0 := t₀.val : ℝ
conditions:
-/
#guard_msgs in
variable (x : Time → ℝ) in
#veriphy_translate Time.deriv x t₀ + 2 * x t₀
