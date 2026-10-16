/-
Packaging lemmas for linear algebra over explicit vectors and matrices.

The certificates Sage computes become finite checks through these lemmas: a non-singular minor gives linear
independence and a lower bound on the rank, a factorisation `A = B * C` an upper bound, a vector a functional sends to
`1` the dimension of its kernel, and an explicit congruence a signature. Each lemma uses the standard axioms only.
-/
import Mathlib.LinearAlgebra.Matrix.Rank
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Mathlib.LinearAlgebra.Dimension.Constructions
import Mathlib.LinearAlgebra.FiniteDimensional.Lemmas

namespace Veriphy.Linear

open Module

variable {K : Type*} [Field K] {m n k r : ℕ}

/-- Rows with a non-singular minor on the columns `s` are linearly independent. -/
theorem linearIndependent_of_minor (v : Fin k → Fin n → K) (s : Fin k → Fin n)
    (h : (Matrix.of fun i j => v i (s j)).det ≠ 0) : LinearIndependent K v := by
  -- the projection on the columns `s` sends the rows to the rows of the minor, which are independent
  apply LinearIndependent.of_comp (LinearMap.funLeft K K s)
  exact Matrix.linearIndependent_rows_of_isUnit
    ((Matrix.isUnit_iff_isUnit_det _).2 (isUnit_iff_ne_zero.2 h))

/-- A factorisation `A = B * C` through `Fin r` bounds the rank by `r`. -/
theorem rank_le_of_factor (A : Matrix (Fin m) (Fin n) K) (B : Matrix (Fin m) (Fin r) K)
    (C : Matrix (Fin r) (Fin n) K) (h : A = B * C) : A.rank ≤ r := by
  rw [h]
  exact (Matrix.rank_mul_le_right B C).trans (Matrix.rank_le_height C)

/-- A non-singular `k × k` minor bounds the rank from below by `k`. -/
theorem le_rank_of_minor (A : Matrix (Fin m) (Fin n) K) (rows : Fin k → Fin m) (cols : Fin k → Fin n)
    (h : (Matrix.of fun i j => A (rows i) (cols j)).det ≠ 0) : k ≤ A.rank := by
  have hind : LinearIndependent K fun i => A (rows i) := linearIndependent_of_minor _ cols h
  rw [Matrix.rank_eq_finrank_span_row]
  calc k = finrank K (Submodule.span K (Set.range fun i => A (rows i))) := by
        rw [finrank_span_eq_card hind, Fintype.card_fin]
    _ ≤ finrank K (Submodule.span K (Set.range A)) :=
        Submodule.finrank_mono (Submodule.span_mono (by rintro _ ⟨i, rfl⟩; exact ⟨rows i, rfl⟩))

/-- The span of an independent family has its size as dimension. -/
theorem finrank_span_of_minor (v : Fin k → Fin n → K) (s : Fin k → Fin n)
    (h : (Matrix.of fun i j => v i (s j)).det ≠ 0) : finrank K (Submodule.span K (Set.range v)) = k := by
  rw [finrank_span_eq_card (linearIndependent_of_minor v s h), Fintype.card_fin]

/-- A functional that takes the value `1` has a kernel of codimension one. -/
theorem finrank_ker_add_one {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V]
    (f : V →ₗ[K] K) (v : V) (hv : f v = 1) : finrank K (LinearMap.ker f) + 1 = finrank K V := by
  have hsurj : LinearMap.range f = ⊤ := by
    refine LinearMap.range_eq_top.2 fun c => ⟨c • v, ?_⟩
    rw [map_smul, hv, smul_eq_mul, mul_one]
  have := LinearMap.finrank_range_add_finrank_ker f
  rw [hsurj, finrank_top, finrank_self] at this
  omega

/-- The dimension of an intersection from two bounds: a subspace `X ≤ U ⊓ W` of dimension `d`, and a subspace
`Y ≤ U ⊔ W` of dimension `s` with `finrank U + finrank W = s + d`. -/
theorem finrank_inf_of_bounds {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V]
    (U W X Y : Submodule K V) {a b s d : ℕ} (hU : finrank K U = a) (hW : finrank K W = b)
    (hX : X ≤ U ⊓ W) (hXd : finrank K X = d) (hY : Y ≤ U ⊔ W) (hYs : finrank K Y = s) (h : a + b = s + d) :
    finrank K ↥(U ⊓ W) = d := by
  have hsum := Submodule.finrank_sup_add_finrank_inf_eq U W
  have hlo := Submodule.finrank_mono hX
  have hsup := Submodule.finrank_mono hY
  omega

/-- `S` has signature `(p, q, z)`: an invertible `P` makes `Pᵀ * S * P` the diagonal matrix of `d`, with `p`
positive, `q` negative and `z` zero entries. Sylvester's law of inertia makes the counts independent of `P`; this
statement does not assert it. -/
def HasSignature {R : Type*} [Field R] [LinearOrder R] {n : ℕ} (S : Matrix (Fin n) (Fin n) R) (p q z : ℕ) : Prop :=
  ∃ (P : Matrix (Fin n) (Fin n) R) (d : Fin n → R), P.det ≠ 0 ∧ P.transpose * S * P = Matrix.diagonal d ∧
    (Finset.univ.filter fun i => 0 < d i).card = p ∧ (Finset.univ.filter fun i => d i < 0).card = q ∧
    (Finset.univ.filter fun i => d i = 0).card = z

end Veriphy.Linear
