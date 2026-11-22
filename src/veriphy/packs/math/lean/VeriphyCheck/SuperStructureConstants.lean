/-
Lie superalgebras given by structure constants, checked by kernel evaluation.

A table `c i j k` with parities `p` defines the graded bracket `[eᵢ, eⱼ} = ∑ k, c i j k • eₖ`. The super-Jacobi
identity on a basis triple, at coordinate `m`, is
`(-1)^(|i||k|) [eᵢ, [eⱼ, eₖ}} + (-1)^(|j||i|) [eⱼ, [eₖ, eᵢ}} + (-1)^(|k||j|) [eₖ, [eᵢ, eⱼ}} = 0`.
`superJacobi_of_check` proves it for every triple from one kernel evaluation. For a family `c₀ + α c₁` (such as
`D(2,1;α)`), the identity is quadratic in `α`, and `superJacobi_affine` proves it for every `α` in any field of
characteristic zero from the checks at `α = 0`, `1` and `-1`.
-/
import VeriphyCheck.StructureConstants
import Mathlib.Data.Rat.Cast.CharZero

namespace VeriphyCheck

variable {R : Type*} [CommRing R] {n : ℕ}

/-- The sign `(-1)^(|i||j|)` of the graded bracket. -/
def gsign (p : Fin n → Bool) (i j : Fin n) : R := if p i && p j then -1 else 1

/-- The super-Jacobi sum with the inner brackets from `a` and the outer ones from `b`; `superJacobiAt` is the
diagonal `a = b = c`. -/
def superJacobiBil (a b : Fin n → Fin n → Fin n → R) (p : Fin n → Bool) (i j k m : Fin n) : R :=
  ∑ l, (gsign p i k * (a j k l * b i l m) + gsign p j i * (a k i l * b j l m) + gsign p k j * (a i j l * b k l m))

/-- The super-Jacobi sum of the basis triple `(i, j, k)` at coordinate `m`. -/
def superJacobiAt (c : Fin n → Fin n → Fin n → R) (p : Fin n → Bool) (i j k m : Fin n) : R :=
  superJacobiBil c c p i j k m

/-- The super-Jacobi sum is invariant under rotating the triple. -/
theorem superJacobiAt_rotate (c : Fin n → Fin n → Fin n → R) (p : Fin n → Bool) (i j k m : Fin n) :
    superJacobiAt c p j k i m = superJacobiAt c p i j k m := by
  unfold superJacobiAt superJacobiBil
  exact Finset.sum_congr rfl fun _ _ => by ring

/-- The identity on every triple follows from the triples whose first index is the smallest. -/
theorem superJacobi_of_min {c : Fin n → Fin n → Fin n → R} {p : Fin n → Bool}
    (h : ∀ i j k m, i ≤ j → i ≤ k → superJacobiAt c p i j k m = 0) (i j k m : Fin n) :
    superJacobiAt c p i j k m = 0 := by
  rcases le_total i j with hij | hji <;> rcases le_total i k with hik | hki <;> rcases le_total j k with hjk | hkj
  all_goals first
    | exact h i j k m ‹_› ‹_›
    | (rw [← superJacobiAt_rotate]; exact h j k i m ‹_› (by omega))
    | (rw [← superJacobiAt_rotate, ← superJacobiAt_rotate]; exact h k i j m (by omega) (by omega))

variable [DecidableEq R]

/-- The super-Jacobi identity holds on every basis triple. -/
def superJacobiCheck (c : Fin n → Fin n → Fin n → R) (p : Fin n → Bool) : Bool :=
  allEntries fun i j => (List.finRange n).all fun k => (List.finRange n).all fun m =>
    sumFin (fun l => gsign p i k * (c j k l * c i l m) + gsign p j i * (c k i l * c j l m) +
      gsign p k j * (c i j l * c k l m)) == 0

theorem superJacobi_of_check {c : Fin n → Fin n → Fin n → R} {p : Fin n → Bool} (h : superJacobiCheck c p = true)
    (i j k m : Fin n) : superJacobiAt c p i j k m = 0 := by
  have := of_allEntries h i j
  simp only [List.all_eq_true, List.mem_finRange, true_implies, beq_iff_eq] at this
  rw [superJacobiAt, superJacobiBil, ← sumFin_eq]
  exact this k m

omit [DecidableEq R] in
/-- The super-Jacobi sum of `c₀ + α c₁` is quadratic in `α`. -/
theorem superJacobiAt_affine (c₀ c₁ : Fin n → Fin n → Fin n → R) (α : R) (p : Fin n → Bool) (i j k m : Fin n) :
    superJacobiAt (fun i j k => c₀ i j k + α * c₁ i j k) p i j k m =
      superJacobiBil c₀ c₀ p i j k m + α * (superJacobiBil c₀ c₁ p i j k m + superJacobiBil c₁ c₀ p i j k m) +
        α ^ 2 * superJacobiBil c₁ c₁ p i j k m := by
  simp only [superJacobiAt, superJacobiBil, Finset.mul_sum, ← Finset.sum_add_distrib]
  exact Finset.sum_congr rfl fun _ _ => by ring

omit [DecidableEq R] in
theorem superJacobiBil_map {S : Type*} [CommRing S] (f : R →+* S) (a b : Fin n → Fin n → Fin n → R)
    (p : Fin n → Bool) (i j k m : Fin n) :
    f (superJacobiBil a b p i j k m) =
      superJacobiBil (fun i j k => f (a i j k)) (fun i j k => f (b i j k)) p i j k m := by
  simp only [superJacobiBil, map_sum, map_add, map_mul, gsign]
  refine Finset.sum_congr rfl fun _ _ => ?_
  split_ifs <;> simp

/-- The super-Jacobi identity for every member `c₀ + α c₁` of a family, in any field of characteristic zero, from the
identity over ℚ at `α = 0`, `1` and `-1`. -/
theorem superJacobi_affine_of {c₀ c₁ : Fin n → Fin n → Fin n → ℚ} {p : Fin n → Bool}
    (h₀ : ∀ i j k m, superJacobiAt c₀ p i j k m = 0)
    (h₁ : ∀ i j k m, superJacobiAt (fun i j k => c₀ i j k + 1 * c₁ i j k) p i j k m = 0)
    (h₂ : ∀ i j k m, superJacobiAt (fun i j k => c₀ i j k + -1 * c₁ i j k) p i j k m = 0)
    {K : Type*} [Field K] [CharZero K] (α : K) (i j k m : Fin n) :
    superJacobiAt (fun i j k => (c₀ i j k : K) + α * (c₁ i j k : K)) p i j k m = 0 := by
  have e₀ := h₀ i j k m
  have e₁ := h₁ i j k m
  have e₂ := h₂ i j k m
  rw [superJacobiAt_affine] at e₁ e₂ ⊢
  rw [superJacobiAt] at e₀
  have hB : superJacobiBil c₀ c₁ p i j k m + superJacobiBil c₁ c₀ p i j k m = 0 := by
    linear_combination (e₁ - e₂) / 2
  have hC : superJacobiBil c₁ c₁ p i j k m = 0 := by linear_combination (e₁ + e₂) / 2 - e₀
  have cast := fun (a b : Fin n → Fin n → Fin n → ℚ) => superJacobiBil_map (Rat.castHom K) a b p i j k m
  simp only [Rat.coe_castHom] at cast
  rw [← cast, ← cast, ← cast, ← cast, e₀, ← Rat.cast_add, hB, hC]
  simp

/-- The super-Jacobi identity for every member `c₀ + α c₁` of a family, from the kernel checks at `α = 0`, `1` and
`-1`. -/
theorem superJacobi_affine {c₀ c₁ : Fin n → Fin n → Fin n → ℚ} {p : Fin n → Bool}
    (h₀ : superJacobiCheck c₀ p = true) (h₁ : superJacobiCheck (fun i j k => c₀ i j k + 1 * c₁ i j k) p = true)
    (h₂ : superJacobiCheck (fun i j k => c₀ i j k + -1 * c₁ i j k) p = true)
    {K : Type*} [Field K] [CharZero K] (α : K) (i j k m : Fin n) :
    superJacobiAt (fun i j k => (c₀ i j k : K) + α * (c₁ i j k : K)) p i j k m = 0 :=
  superJacobi_affine_of (superJacobi_of_check h₀) (superJacobi_of_check h₁) (superJacobi_of_check h₂) α i j k m

/-! ## Sparse tables

A table with few nonzero constants (`F(4)` has 1320 of 64000) is given by its rows `r i j`, the nonzero
coefficients of `[eᵢ, eⱼ}` as `(k, c)` pairs. The check builds, for each triple, the list of contributions to the
super-Jacobi sum and verifies it vanishes coordinate by coordinate: its cost follows the nonzero products, not `n⁵`.
-/

namespace Sparse

variable {R : Type*} [CommRing R] {n : ℕ}

/-- The value at `m` of a sparse vector: the sum of its coefficients at `m`. -/
def at_ (v : List (Fin n × R)) (m : Fin n) : R := v.foldr (fun x s => (if x.1 = m then x.2 else 0) + s) 0

/-- The dense table of a sparse one. -/
def table (r : Fin n → Fin n → List (Fin n × R)) : Fin n → Fin n → Fin n → R := fun i j m => at_ (r i j) m

theorem at_nil (m : Fin n) : at_ ([] : List (Fin n × R)) m = 0 := rfl

theorem at_cons (x : Fin n × R) (v : List (Fin n × R)) (m : Fin n) :
    at_ (x :: v) m = (if x.1 = m then x.2 else 0) + at_ v m := rfl

theorem at_append (v w : List (Fin n × R)) (m : Fin n) : at_ (v ++ w) m = at_ v m + at_ w m := by
  induction v with
  | nil => simp [at_nil]
  | cons x v ih => rw [List.cons_append, at_cons, at_cons, ih, add_assoc]

theorem at_scale (a : R) (v : List (Fin n × R)) (m : Fin n) :
    at_ (v.map fun y => (y.1, a * y.2)) m = a * at_ v m := by
  induction v with
  | nil => simp [at_nil]
  | cons x v ih =>
    rw [List.map_cons, at_cons, at_cons, ih, mul_add]
    split_ifs <;> simp

/-- `∑ l, (value at l) * f l` is the sum over the sparse entries. -/
theorem sum_at_mul (v : List (Fin n × R)) (f : Fin n → R) :
    ∑ l, at_ v l * f l = v.foldr (fun x s => x.2 * f x.1 + s) 0 := by
  induction v with
  | nil => simp [at_nil]
  | cons x v ih =>
    simp only [at_cons, add_mul, Finset.sum_add_distrib, ite_mul, zero_mul, Finset.sum_ite_eq, Finset.mem_univ,
      ite_true, List.foldr_cons, ih]

/-- The contributions of `s • [e_a, [e_b, e_c}}`. -/
def nested (r : Fin n → Fin n → List (Fin n × R)) (s : R) (a b c : Fin n) : List (Fin n × R) :=
  (r b c).flatMap fun x => (r a x.1).map fun y => (y.1, s * (x.2 * y.2))

theorem at_nested (r : Fin n → Fin n → List (Fin n × R)) (s : R) (a b c m : Fin n) :
    at_ (nested r s a b c) m = s * ∑ l, table r b c l * table r a l m := by
  simp only [table, sum_at_mul, nested]
  induction r b c with
  | nil => simp [at_nil]
  | cons x v ih =>
    rw [List.flatMap_cons, at_append, ih, List.foldr_cons, mul_add]
    congr 1
    have := at_scale (s * x.2) (r a x.1) m
    simp only [mul_assoc] at this ⊢
    rw [← this]

/-- The contributions to the super-Jacobi sum of the triple `(i, j, k)`. -/
def jacobiList (r : Fin n → Fin n → List (Fin n × R)) (p : Fin n → Bool) (i j k : Fin n) : List (Fin n × R) :=
  nested r (gsign p i k) i j k ++ nested r (gsign p j i) j k i ++ nested r (gsign p k j) k i j

theorem at_jacobiList (r : Fin n → Fin n → List (Fin n × R)) (p : Fin n → Bool) (i j k m : Fin n) :
    at_ (jacobiList r p i j k) m = superJacobiAt (table r) p i j k m := by
  rw [jacobiList, at_append, at_append, at_nested, at_nested, at_nested, superJacobiAt, superJacobiBil,
    Finset.mul_sum, Finset.mul_sum, Finset.mul_sum, ← Finset.sum_add_distrib, ← Finset.sum_add_distrib]

variable [DecidableEq R]

/-- Every coordinate a sparse vector mentions has value zero (so every coordinate has). -/
def isZero (v : List (Fin n × R)) : Bool := v.all fun x => at_ v x.1 == 0

omit [DecidableEq R] in
theorem at_of_not_mem (v : List (Fin n × R)) (m : Fin n) (h : ∀ x ∈ v, x.1 ≠ m) : at_ v m = 0 := by
  induction v with
  | nil => rfl
  | cons x v ih =>
    have hx := h x (by simp)
    rw [at_cons, ih fun y hy => h y (by simp [hy])]
    simp [hx]

theorem at_of_isZero {v : List (Fin n × R)} (h : isZero v = true) (m : Fin n) : at_ v m = 0 := by
  by_cases hm : ∃ x ∈ v, x.1 = m
  · obtain ⟨x, hx, rfl⟩ := hm
    simp only [isZero, List.all_eq_true, beq_iff_eq] at h
    exact h x hx
  · exact at_of_not_mem v m fun x hx hxm => hm ⟨x, hx, hxm⟩

/-- The super-Jacobi identity holds on every basis triple of the sparse table whose first index is the smallest
(the others follow by rotation). -/
def superJacobiCheck (r : Fin n → Fin n → List (Fin n × R)) (p : Fin n → Bool) : Bool :=
  (List.finRange n).all fun i => ((List.finRange n).filter (i ≤ ·)).all fun j =>
    ((List.finRange n).filter (i ≤ ·)).all fun k => isZero (jacobiList r p i j k)

theorem superJacobi_of_check {r : Fin n → Fin n → List (Fin n × R)} {p : Fin n → Bool}
    (h : superJacobiCheck r p = true) (i j k m : Fin n) : superJacobiAt (table r) p i j k m = 0 := by
  refine superJacobi_of_min (fun i j k m hij hik => ?_) i j k m
  simp only [superJacobiCheck, List.all_eq_true, List.mem_finRange, List.mem_filter, true_and,
    decide_eq_true_eq, true_implies] at h
  rw [← at_jacobiList]
  exact at_of_isZero (h i j hij k hik) m

/-- The rows of `c₀ + t c₁`, from the rows of `c₀` and `c₁`. -/
def combine (r₀ r₁ : Fin n → Fin n → List (Fin n × R)) (t : R) : Fin n → Fin n → List (Fin n × R) :=
  fun i j => r₀ i j ++ (r₁ i j).map fun y => (y.1, t * y.2)

omit [DecidableEq R] in
theorem table_combine (r₀ r₁ : Fin n → Fin n → List (Fin n × R)) (t : R) :
    table (combine r₀ r₁ t) = fun i j k => table r₀ i j k + t * table r₁ i j k := by
  funext i j k
  simp only [table, combine, at_append, at_scale]

/-- The super-Jacobi identity for every member of a sparse family `c₀ + α c₁`, from the kernel checks at
`α = 0`, `1` and `-1`. -/
theorem superJacobi_affine {r₀ r₁ : Fin n → Fin n → List (Fin n × ℚ)} {p : Fin n → Bool}
    (h₀ : superJacobiCheck r₀ p = true) (h₁ : superJacobiCheck (combine r₀ r₁ 1) p = true)
    (h₂ : superJacobiCheck (combine r₀ r₁ (-1)) p = true)
    {K : Type*} [Field K] [CharZero K] (α : K) (i j k m : Fin n) :
    superJacobiAt (fun i j k => ((table r₀ i j k : ℚ) : K) + α * ((table r₁ i j k : ℚ) : K)) p i j k m = 0 := by
  have e₁ := superJacobi_of_check h₁
  have e₂ := superJacobi_of_check h₂
  rw [table_combine] at e₁ e₂
  exact superJacobi_affine_of (superJacobi_of_check h₀) e₁ e₂ α i j k m

end Sparse

end VeriphyCheck
