/-
Lie algebras given by structure constants, checked by kernel evaluation.

A table `c i j k` defines the bracket `⁅x, y⁆ m = ∑ i, ∑ j, x i * y j * c i j m` on `Fin n → R`. The checks are
antisymmetry of the table and the Jacobi identity on basis triples; their soundness theorems give `⁅x, x⁆ = 0` and
the Jacobi identity for all vectors, by trilinearity.
-/
import VeriphyCheck.Matrix
import Mathlib.Tactic.LinearCombination
import Mathlib.Tactic.Ring

namespace VeriphyCheck

variable {R : Type*} [CommRing R] {n : ℕ}

/-- The bracket defined by structure constants. -/
def scBracket (c : Fin n → Fin n → Fin n → R) (x y : Fin n → R) : Fin n → R :=
  fun m => ∑ i, ∑ j, x i * y j * c i j m

/-- `∑ i, f i`, computed by a fold the kernel evaluates. -/
def sumFin (f : Fin n → R) : R := dot f (fun _ => 1)

theorem sumFin_eq (f : Fin n → R) : sumFin f = ∑ i, f i := by simp [sumFin, dot_eq]

/-- The Jacobi sum of the basis triple `(i, j, k)` at coordinate `m`. -/
def jacobiAt (c : Fin n → Fin n → Fin n → R) (i j k m : Fin n) : R :=
  ∑ l, (c j k l * c i l m + c k i l * c j l m + c i j l * c k l m)

variable [DecidableEq R]

/-- The table is antisymmetric: `c i j m = -c j i m`. -/
def antisymmCheck (c : Fin n → Fin n → Fin n → R) : Bool :=
  allEntries fun i j => (List.finRange n).all fun m => c i j m == -c j i m

/-- The Jacobi identity holds on every basis triple. -/
def jacobiCheck (c : Fin n → Fin n → Fin n → R) : Bool :=
  allEntries fun i j => (List.finRange n).all fun k => (List.finRange n).all fun m =>
    sumFin (fun l => c j k l * c i l m + c k i l * c j l m + c i j l * c k l m) == 0

theorem jacobiAt_of_check {c : Fin n → Fin n → Fin n → R} (h : jacobiCheck c = true) (i j k m : Fin n) :
    jacobiAt c i j k m = 0 := by
  have := of_allEntries h i j
  simp only [List.all_eq_true, List.mem_finRange, true_implies, beq_iff_eq] at this
  rw [jacobiAt, ← sumFin_eq]
  exact this k m

omit [DecidableEq R] in
theorem scBracket_scBracket (c : Fin n → Fin n → Fin n → R) (x y z : Fin n → R) (m : Fin n) :
    scBracket c x (scBracket c y z) m = ∑ i, ∑ j, ∑ k, x i * y j * z k * ∑ l, c j k l * c i l m := by
  simp only [scBracket, Finset.mul_sum, Finset.sum_mul]
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun j _ => ?_
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun k _ => Finset.sum_congr rfl fun l _ => ?_
  ring

theorem jacobi_of_check {c : Fin n → Fin n → Fin n → R} (h : jacobiCheck c = true) (x y z : Fin n → R) :
    scBracket c x (scBracket c y z) + scBracket c y (scBracket c z x) + scBracket c z (scBracket c x y) = 0 := by
  funext m
  simp only [Pi.add_apply, Pi.zero_apply, scBracket_scBracket]
  -- the second and third terms, re-indexed to run over (i, j, k) for (x, y, z)
  have h2 : ∑ j, ∑ k, ∑ i, y j * z k * x i * ∑ l, c k i l * c j l m =
      ∑ i, ∑ j, ∑ k, x i * y j * z k * ∑ l, c k i l * c j l m := by
    calc ∑ j, ∑ k, ∑ i, y j * z k * x i * ∑ l, c k i l * c j l m
        = ∑ j, ∑ i, ∑ k, y j * z k * x i * ∑ l, c k i l * c j l m :=
          Finset.sum_congr rfl fun _ _ => Finset.sum_comm
      _ = ∑ i, ∑ j, ∑ k, y j * z k * x i * ∑ l, c k i l * c j l m := Finset.sum_comm
      _ = ∑ i, ∑ j, ∑ k, x i * y j * z k * ∑ l, c k i l * c j l m :=
          Finset.sum_congr rfl fun _ _ => Finset.sum_congr rfl fun _ _ => Finset.sum_congr rfl fun _ _ => by ring
  have h3 : ∑ k, ∑ i, ∑ j, z k * x i * y j * ∑ l, c i j l * c k l m =
      ∑ i, ∑ j, ∑ k, x i * y j * z k * ∑ l, c i j l * c k l m := by
    calc ∑ k, ∑ i, ∑ j, z k * x i * y j * ∑ l, c i j l * c k l m
        = ∑ i, ∑ k, ∑ j, z k * x i * y j * ∑ l, c i j l * c k l m := Finset.sum_comm
      _ = ∑ i, ∑ j, ∑ k, z k * x i * y j * ∑ l, c i j l * c k l m :=
          Finset.sum_congr rfl fun _ _ => Finset.sum_comm
      _ = ∑ i, ∑ j, ∑ k, x i * y j * z k * ∑ l, c i j l * c k l m :=
          Finset.sum_congr rfl fun _ _ => Finset.sum_congr rfl fun _ _ => Finset.sum_congr rfl fun _ _ => by ring
  rw [h2, h3, ← Finset.sum_add_distrib, ← Finset.sum_add_distrib]
  refine Finset.sum_eq_zero fun i _ => ?_
  rw [← Finset.sum_add_distrib, ← Finset.sum_add_distrib]
  refine Finset.sum_eq_zero fun j _ => ?_
  rw [← Finset.sum_add_distrib, ← Finset.sum_add_distrib]
  refine Finset.sum_eq_zero fun k _ => ?_
  have hj := jacobiAt_of_check h i j k m
  rw [jacobiAt, Finset.sum_add_distrib, Finset.sum_add_distrib] at hj
  linear_combination x i * y j * z k * hj

/-- `⁅x, x⁆ = 0` from an antisymmetric table, over a domain of characteristic zero (`ℤ`, `ℚ`, `ℝ`, `ℂ`, number
fields): the sum equals its own negative. -/
theorem bracket_self_of_check [IsDomain R] [CharZero R] {c : Fin n → Fin n → Fin n → R}
    (h : antisymmCheck c = true) (x : Fin n → R) : scBracket c x x = 0 := by
  funext m
  have hc : ∀ i j, c i j m = -c j i m := fun i j => by
    have := of_allEntries h i j
    simp only [List.all_eq_true, List.mem_finRange, true_implies, beq_iff_eq] at this
    exact this m
  simp only [scBracket, Pi.zero_apply]
  set S := ∑ i, ∑ j, x i * x j * c i j m
  have hneg : S = -S := by
    calc S = ∑ i, ∑ j, x j * x i * c j i m := Finset.sum_comm
      _ = ∑ i, ∑ j, -(x i * x j * c i j m) :=
          Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => by rw [hc j i]; ring
      _ = -S := by simp only [S, Finset.sum_neg_distrib]
  have h2 : (2 : R) * S = 0 := by linear_combination hneg
  exact (mul_eq_zero.mp h2).resolve_left two_ne_zero

end VeriphyCheck
