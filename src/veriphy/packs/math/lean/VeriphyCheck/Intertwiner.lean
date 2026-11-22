/-
Intertwiners of matrix representations as natural transformations.

A representation of a group `G` is a functor from its one-object category, and a natural transformation between two
such functors is a matrix `T` with `T * ρ g = σ g * T` for every morphism `g`. When `S` generates `G`, the squares for
the generators suffice: each is a matrix identity the kernel checks (`mul_eq_mul_of_check`), and
`intertwines_of_closure` extends them to every element. `matrixRep` and `repHom` package the result as a morphism of
mathlib's `Rep`, which is equivalent to the functor category, and `repIso` as an isomorphism given an explicit inverse.
-/
import Mathlib.RepresentationTheory.Rep.Basic
import Mathlib.LinearAlgebra.Matrix.ToLin
import Mathlib.Algebra.Group.Subgroup.Lattice

namespace VeriphyCheck

universe u

variable {G : Type*} [Group G] {n m : Type u} [Fintype n] [DecidableEq n] [Fintype m] [DecidableEq m]
  {R : Type u} [CommRing R]

/-- A matrix intertwining two matrix representations on a generating set intertwines them on every element. -/
theorem intertwines_of_closure (ρ : G →* Matrix n n R) (σ : G →* Matrix m m R) (T : Matrix m n R) {S : Set G}
    (hS : Subgroup.closure S = ⊤) (h : ∀ s ∈ S, T * ρ s = σ s * T) (g : G) : T * ρ g = σ g * T := by
  have hg : g ∈ Subgroup.closure S := hS ▸ Subgroup.mem_top g
  induction hg using Subgroup.closure_induction with
  | mem x hx => exact h x hx
  | one => simp
  | mul x y _ _ hx hy => rw [map_mul, map_mul, ← Matrix.mul_assoc, hx, Matrix.mul_assoc, hy, Matrix.mul_assoc]
  | inv x _ hx =>
    calc T * ρ x⁻¹ = σ x⁻¹ * σ x * T * ρ x⁻¹ := by rw [← map_mul, inv_mul_cancel, map_one, Matrix.one_mul]
      _ = σ x⁻¹ * (T * ρ x) * ρ x⁻¹ := by rw [hx, Matrix.mul_assoc (σ x⁻¹)]
      _ = σ x⁻¹ * T := by rw [Matrix.mul_assoc, Matrix.mul_assoc, ← map_mul, mul_inv_cancel, map_one, Matrix.mul_one]

/-- The representation of `G` on column vectors given by a matrix representation. -/
noncomputable def matrixRep (ρ : G →* Matrix n n R) : Representation R G (n → R) :=
  (Matrix.toLinAlgEquiv' : Matrix n n R ≃ₐ[R] Module.End R (n → R)).toRingEquiv.toMonoidHom.comp ρ

/-- An intertwining matrix as an intertwining map. -/
noncomputable def intertwiningMap (ρ : G →* Matrix n n R) (σ : G →* Matrix m m R) (T : Matrix m n R)
    (hT : ∀ g, T * ρ g = σ g * T) : (matrixRep ρ).IntertwiningMap (matrixRep σ) :=
  { Matrix.toLin' T with
    isIntertwining' := fun g => by
      change Matrix.toLin' T ∘ₗ Matrix.toLin' (ρ g) = Matrix.toLin' (σ g) ∘ₗ Matrix.toLin' T
      rw [← Matrix.toLin'_mul, ← Matrix.toLin'_mul, hT] }

/-- An intertwining matrix as a morphism of representations: a natural transformation between the functors. -/
noncomputable def repHom (ρ : G →* Matrix n n R) (σ : G →* Matrix m m R) (T : Matrix m n R)
    (hT : ∀ g, T * ρ g = σ g * T) : Rep.of (matrixRep ρ) ⟶ Rep.of (matrixRep σ) :=
  Rep.ofHom (intertwiningMap ρ σ T hT)

/-- The inverse of an invertible intertwining matrix intertwines the other way. -/
theorem intertwines_inv (ρ : G →* Matrix n n R) (σ : G →* Matrix m m R) {T : Matrix m n R} {U : Matrix n m R}
    (hT : ∀ g, T * ρ g = σ g * T) (hTU : T * U = 1) (hUT : U * T = 1) (g : G) : U * σ g = ρ g * U :=
  calc U * σ g = U * σ g * (T * U) := by rw [hTU, Matrix.mul_one]
    _ = U * (T * ρ g) * U := by rw [hT g]; simp only [Matrix.mul_assoc]
    _ = ρ g * U := by rw [← Matrix.mul_assoc, hUT, Matrix.one_mul]

/-- An invertible intertwining matrix as an isomorphism of representations: a natural isomorphism. -/
noncomputable def repIso (ρ : G →* Matrix n n R) (σ : G →* Matrix m m R) {T : Matrix m n R} {U : Matrix n m R}
    (hT : ∀ g, T * ρ g = σ g * T) (hTU : T * U = 1) (hUT : U * T = 1) :
    Rep.of (matrixRep ρ) ≅ Rep.of (matrixRep σ) where
  hom := repHom ρ σ T hT
  inv := repHom σ ρ U (intertwines_inv ρ σ hT hTU hUT)
  hom_inv_id := by
    apply Rep.Hom.ext
    apply Representation.IntertwiningMap.ext
    change Matrix.toLin' U ∘ₗ Matrix.toLin' T = LinearMap.id
    rw [← Matrix.toLin'_mul, hUT, Matrix.toLin'_one]
  inv_hom_id := by
    apply Rep.Hom.ext
    apply Representation.IntertwiningMap.ext
    change Matrix.toLin' T ∘ₗ Matrix.toLin' U = LinearMap.id
    rw [← Matrix.toLin'_mul, hTU, Matrix.toLin'_one]

end VeriphyCheck
