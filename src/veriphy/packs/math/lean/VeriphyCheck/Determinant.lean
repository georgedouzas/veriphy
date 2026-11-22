/-
Determinants and inverses checked by kernel evaluation.

A determinant is certified by an LU factorization `A = L * U` with `L` lower and `U` upper triangular: the kernel
checks the product and the zero patterns, and `det A` is the product of the two diagonals. An integer matrix is
factored over ℚ, and the result is transported back by the cast. An inverse is certified by the product `A * B = 1`.
-/
import VeriphyCheck.Matrix
import Mathlib.LinearAlgebra.Matrix.Block
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Mathlib.Data.Rat.Cast.CharZero

namespace VeriphyCheck

open Matrix

variable {R : Type*} [CommRing R] {n : ℕ}

/-- `∏ i, M i i`, computed by a fold the kernel evaluates. -/
def diagProd (M : Matrix (Fin n) (Fin n) R) : R := (List.finRange n).foldr (fun i p => M i i * p) 1

theorem diagProd_eq (M : Matrix (Fin n) (Fin n) R) : diagProd M = ∏ i, M i i := by
  rw [Fin.prod_univ_def, diagProd]
  induction (List.finRange n) with
  | nil => simp
  | cons k ks ih => simp [List.foldr, ih]

variable [DecidableEq R]

/-- Every entry above the diagonal is zero. -/
def lowerCheck (L : Matrix (Fin n) (Fin n) R) : Bool := allEntries fun i j => !decide (i < j) || L i j == 0

/-- Every entry below the diagonal is zero. -/
def upperCheck (U : Matrix (Fin n) (Fin n) R) : Bool := allEntries fun i j => !decide (j < i) || U i j == 0

theorem upperTriangular_of_check {U : Matrix (Fin n) (Fin n) R} (h : upperCheck U = true) :
    U.BlockTriangular id := by
  intro i j hji
  have := of_allEntries h i j
  simp only [Bool.or_eq_true, Bool.not_eq_true', decide_eq_false_iff_not, beq_iff_eq] at this
  exact this.resolve_left (not_not.mpr hji)

theorem lowerTriangular_of_check {L : Matrix (Fin n) (Fin n) R} (h : lowerCheck L = true) :
    L.BlockTriangular OrderDual.toDual := by
  intro i j hji
  have := of_allEntries h i j
  simp only [Bool.or_eq_true, Bool.not_eq_true', decide_eq_false_iff_not, beq_iff_eq] at this
  exact this.resolve_left (not_not.mpr hji)

/-- `det A = ∏ L i i * ∏ U i i` for an LU factorization the kernel checks. -/
theorem det_eq_of_lu {A L U : Matrix (Fin n) (Fin n) R} (hmul : mulCheck L U A = true) (hl : lowerCheck L = true)
    (hu : upperCheck U = true) : A.det = diagProd L * diagProd U := by
  rw [← mul_eq_of_check hmul, det_mul, det_of_isLowerTriangular L (lowerTriangular_of_check hl),
    det_of_isUpperTriangular (upperTriangular_of_check hu), diagProd_eq, diagProd_eq]

/-- The determinant of an integer matrix from an LU factorization over ℚ, with the value checked too:
`(by decide +kernel)` for each hypothesis. -/
theorem det_eq_of_lu_int {A : Matrix (Fin n) (Fin n) ℤ} {L U : Matrix (Fin n) (Fin n) ℚ} {d : ℤ}
    (hmul : mulCheck L U (A.map (Int.cast : ℤ → ℚ)) = true) (hl : lowerCheck L = true) (hu : upperCheck U = true)
    (hd : (diagProd L * diagProd U == (d : ℚ)) = true) : A.det = d := by
  have hq : (A.map (Int.cast : ℤ → ℚ)).det = (d : ℚ) := by
    rw [det_eq_of_lu hmul hl hu]
    exact beq_iff_eq.mp hd
  rw [← Int.cast_det] at hq
  exact_mod_cast hq

/-- `A⁻¹ = B` from the product `A * B = 1`, which the kernel checks. -/
theorem inv_eq_of_check {A B : Matrix (Fin n) (Fin n) R} (h : mulCheck A B 1 = true) : A⁻¹ = B :=
  inv_eq_right_inv (mul_eq_of_check h)

end VeriphyCheck
