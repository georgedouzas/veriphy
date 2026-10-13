/-
Multiplicity-free fusion data, with mathlib only.

A recipe asset: a project copies this file to `.veriphy/lean/VeriphyAssets/FusionData.lean` (see the user guide). It
states the data of a multiplicity-free (braided) fusion category in a basis, until mathlib has an equivalent:

* labels `L` (simple objects), a unit and duals;
* fusion multiplicities `N a b c ∈ {0, 1}` (`a ⊗ b` contains `c`);
* F-symbols `F a b c d e f = (F^{abc}_d)_{ef}`, R-symbols `R a b c = R^{ab}_c` and their inverses `Rinv` in a
  commutative ring `K` (a field in practice), zero on inadmissible labels.

The pentagon and hexagon equations are propositions over all labels; the inverse braiding is data, with
`R * Rinv = 1` on admissible labels a checked proposition, so no field inverse is needed. `GaugeRelated` states that
two data differ by a change of basis of the splitting spaces.

Explicit data are checked by the kernel in two steps. The equations are pruned to admissible labels (`PentagonOn`,
`HexagonOneOn`, `HexagonTwoOn`), every other term vanishing because F-symbols vanish on inadmissible labels
(`pentagon_of_on`). Values in a number field `ℚ(ζ)` with `ζ ^ m = r` are given by rational coefficients on
`1, ζ, …` (`RepData`, `Coeffs`), which the kernel multiplies cheaply; `RepData.isBraidedFusion` then gives the
equations at every such `ζ` in every `ℚ`-algebra, so data over `ℚ(ζ₁₆)` hold over `ℂ` at `exp (2πi/16)` and at its
Galois conjugates.
-/
import Mathlib.Algebra.Algebra.Rat
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Algebra.Order.Field.Rat
import Mathlib.Data.Fintype.Basic
import Mathlib.Tactic.Ring

namespace FusionData

/-- Multiplicity-free fusion data with labels `L` over a field `K`. -/
structure Data (L K : Type*) where
  /-- The unit object. -/
  unit : L
  /-- The dual of each object. -/
  dual : L → L
  /-- `N a b c`: the multiplicity of `c` in `a ⊗ b`, 0 or 1. -/
  N : L → L → L → ℕ
  /-- `F a b c d e f = (F^{abc}_d)_{ef}`: from `(a ⊗ b → e) ⊗ c → d` to `a ⊗ (b ⊗ c → f) → d`. -/
  F : L → L → L → L → L → L → K
  /-- `R a b c = R^{ab}_c`, the braiding of `a ⊗ b → c`. -/
  R : L → L → L → K
  /-- The inverse braiding `(R^{ab}_c)⁻¹`. -/
  Rinv : L → L → L → K

variable {L K : Type*} [Fintype L] [DecidableEq L] [CommRing K] (D : Data L K)

/-- The fusion rules are associative: `Σₑ Nᵃᵇₑ Nᵉᶜ_d = Σ_f Nᵇᶜ_f Nᵃᶠ_d`. -/
def Associative : Prop :=
  ∀ a b c d, ∑ e, D.N a b e * D.N e c d = ∑ f, D.N b c f * D.N a f d

/-- The unit fuses trivially on both sides. -/
def HasUnit : Prop :=
  ∀ a b, D.N D.unit a b = (if a = b then 1 else 0) ∧ D.N a D.unit b = (if a = b then 1 else 0)

/-- Every object fuses with its dual to the unit, once. -/
def HasDuals : Prop :=
  ∀ a, D.N a (D.dual a) D.unit = 1

/-- The pentagon equations, `(F^{fcd}_e)_{gl} (F^{abl}_e)_{fk} = Σₕ (F^{abc}_g)_{fh} (F^{ahd}_e)_{gk} (F^{bcd}_k)_{hl}`.
-/
def Pentagon : Prop :=
  ∀ a b c d e f g k l, D.F f c d e g l * D.F a b l e f k = ∑ h, D.F a b c g f h * D.F a h d e g k * D.F b c d k h l

/-- The first hexagon, `R^{ca}_e (F^{acb}_d)_{eg} R^{cb}_g = Σ_f (F^{cab}_d)_{ef} R^{cf}_d (F^{abc}_d)_{fg}`. -/
def HexagonOne : Prop :=
  ∀ a b c d e g, D.R c a e * D.F a c b d e g * D.R c b g = ∑ f, D.F c a b d e f * D.R c f d * D.F a b c d f g

/-- The second hexagon, with the inverse braiding. -/
def HexagonTwo : Prop :=
  ∀ a b c d e g, D.Rinv a c e * D.F a c b d e g * D.Rinv b c g =
    ∑ f, D.F c a b d e f * D.Rinv f c d * D.F a b c d f g

/-- `Rinv` inverts `R` on admissible labels. -/
def InverseBraiding : Prop :=
  ∀ a b c, D.N a b c ≠ 0 → D.R a b c * D.Rinv a b c = 1

/-- Fusion data: a fusion ring with associativity, unit and duals, and the pentagon. -/
def IsFusion : Prop :=
  Associative D ∧ HasUnit D ∧ HasDuals D ∧ Pentagon D

/-- Braided fusion data: a fusion ring with associativity, unit and duals, the pentagon and both hexagons. -/
def IsBraidedFusion : Prop :=
  Associative D ∧ HasUnit D ∧ HasDuals D ∧ Pentagon D ∧ InverseBraiding D ∧ HexagonOne D ∧ HexagonTwo D

/-- `D'` is `D` in another gauge `u` (invertible on admissible labels, with inverse `uinv`):
`(F'^{abc}_d)_{ef} u^{bc}_f u^{af}_d = u^{ab}_e u^{ec}_d (F^{abc}_d)_{ef}` and `R'^{ab}_c u^{ab}_c = u^{ba}_c R^{ab}_c`. -/
def GaugeRelated (D' : Data L K) (u uinv : L → L → L → K) : Prop :=
  D'.N = D.N ∧ (∀ a b c, D.N a b c ≠ 0 → u a b c * uinv a b c = 1) ∧
    (∀ a b c d e f, D'.F a b c d e f * (u b c f * u a f d) = u a b e * u e c d * D.F a b c d e f) ∧
    ∀ a b c, D'.R a b c * u a b c = u b a c * D.R a b c

/-! ### Pruned equations

The F-symbols vanish on inadmissible labels, so every term of a pentagon equation vanishes unless six multiplicities
are nonzero, and every term of a hexagon equation unless two are. The pruned forms quantify over those admissible
labels only, the implications short-circuiting the kernel's enumeration; they imply the full equations. -/

/-- F-symbols vanish on inadmissible labels. -/
def FSupported : Prop :=
  ∀ a b c d e f, D.F a b c d e f ≠ 0 → D.N a b e ≠ 0 ∧ D.N e c d ≠ 0 ∧ D.N b c f ≠ 0 ∧ D.N a f d ≠ 0

/-- The pentagon equations on admissible labels. -/
def PentagonOn : Prop :=
  ∀ a b f, D.N a b f ≠ 0 → ∀ c g, D.N f c g ≠ 0 → ∀ d e, D.N g d e ≠ 0 → ∀ l, D.N c d l ≠ 0 → ∀ k, D.N b l k ≠ 0 →
    D.N a k e ≠ 0 → D.F f c d e g l * D.F a b l e f k = ∑ h, D.F a b c g f h * D.F a h d e g k * D.F b c d k h l

/-- The first hexagon on admissible labels. -/
def HexagonOneOn : Prop :=
  ∀ e b d, D.N e b d ≠ 0 → ∀ a g, D.N a g d ≠ 0 → ∀ c,
    D.R c a e * D.F a c b d e g * D.R c b g = ∑ f, D.F c a b d e f * D.R c f d * D.F a b c d f g

/-- The second hexagon on admissible labels. -/
def HexagonTwoOn : Prop :=
  ∀ e b d, D.N e b d ≠ 0 → ∀ a g, D.N a g d ≠ 0 → ∀ c,
    D.Rinv a c e * D.F a c b d e g * D.Rinv b c g = ∑ f, D.F c a b d e f * D.Rinv f c d * D.F a b c d f g

variable {D}

theorem F_eq_zero (hF : FSupported D) {a b c d e f : L}
    (h : D.N a b e = 0 ∨ D.N e c d = 0 ∨ D.N b c f = 0 ∨ D.N a f d = 0) : D.F a b c d e f = 0 := by
  by_contra hne
  obtain ⟨h₁, h₂, h₃, h₄⟩ := hF a b c d e f hne
  omega

theorem pentagon_of_on (hF : FSupported D) (h : PentagonOn D) : Pentagon D := by
  intro a b c d e f g k l
  by_cases h₁ : D.N a b f = 0
  · simp [F_eq_zero hF (Or.inl h₁)]
  by_cases h₂ : D.N f c g = 0
  · simp [F_eq_zero hF (Or.inl h₂), F_eq_zero hF (Or.inr (Or.inl h₂))]
  by_cases h₃ : D.N g d e = 0
  · simp [F_eq_zero hF (Or.inr (Or.inl h₃))]
  by_cases h₄ : D.N c d l = 0
  · simp [F_eq_zero hF (Or.inr (Or.inr (Or.inl h₄)))]
  by_cases h₅ : D.N b l k = 0
  · simp [F_eq_zero hF (Or.inr (Or.inr (Or.inl h₅))), F_eq_zero hF (Or.inr (Or.inr (Or.inr h₅)))]
  by_cases h₆ : D.N a k e = 0
  · simp [F_eq_zero hF (Or.inr (Or.inr (Or.inr h₆)))]
  exact h a b f h₁ c g h₂ d e h₃ l h₄ k h₅ h₆

theorem hexagonOne_of_on (hF : FSupported D) (h : HexagonOneOn D) : HexagonOne D := by
  intro a b c d e g
  by_cases h₁ : D.N e b d = 0
  · simp [F_eq_zero hF (Or.inr (Or.inl h₁))]
  by_cases h₂ : D.N a g d = 0
  · simp [F_eq_zero hF (Or.inr (Or.inr (Or.inr h₂)))]
  exact h e b d h₁ a g h₂ c

theorem hexagonTwo_of_on (hF : FSupported D) (h : HexagonTwoOn D) : HexagonTwo D := by
  intro a b c d e g
  by_cases h₁ : D.N e b d = 0
  · simp [F_eq_zero hF (Or.inr (Or.inl h₁))]
  by_cases h₂ : D.N a g d = 0
  · simp [F_eq_zero hF (Or.inr (Or.inr (Or.inr h₂)))]
  exact h e b d h₁ a g h₂ c

variable (D)

/-- What the kernel checks for fusion data: the fusion ring, the support of the F-symbols and the pruned pentagon. -/
def FusionCheck : Prop :=
  Associative D ∧ HasUnit D ∧ HasDuals D ∧ FSupported D ∧ PentagonOn D

/-- What the kernel checks for braided fusion data: `FusionCheck` and the inverse braiding and pruned hexagons. -/
def BraidedFusionCheck : Prop :=
  FusionCheck D ∧ InverseBraiding D ∧ HexagonOneOn D ∧ HexagonTwoOn D

variable {D}

theorem IsFusion.of_check (h : FusionCheck D) : IsFusion D :=
  ⟨h.1, h.2.1, h.2.2.1, pentagon_of_on h.2.2.2.1 h.2.2.2.2⟩

theorem IsBraidedFusion.of_check (h : BraidedFusionCheck D) : IsBraidedFusion D :=
  let ⟨⟨h₁, h₂, h₃, hF, h₅⟩, h₆, h₇, h₈⟩ := h
  ⟨h₁, h₂, h₃, pentagon_of_on hF h₅, h₆, hexagonOne_of_on hF h₇, hexagonTwo_of_on hF h₈⟩

variable (D)

/-! Explicit data over a ring with decidable equality decide every check (`decide +kernel`). -/

section Decidable

variable [DecidableEq K]

instance : Decidable (Associative D) := by unfold Associative; infer_instance
instance : Decidable (HasUnit D) := by unfold HasUnit; infer_instance
instance : Decidable (HasDuals D) := by unfold HasDuals; infer_instance
instance : Decidable (InverseBraiding D) := by unfold InverseBraiding; infer_instance
instance : Decidable (FSupported D) := by unfold FSupported; infer_instance
instance : Decidable (PentagonOn D) := by unfold PentagonOn; infer_instance
instance : Decidable (HexagonOneOn D) := by unfold HexagonOneOn; infer_instance
instance : Decidable (HexagonTwoOn D) := by unfold HexagonTwoOn; infer_instance
instance : Decidable (FusionCheck D) := by unfold FusionCheck; infer_instance
instance : Decidable (BraidedFusionCheck D) := by unfold BraidedFusionCheck; infer_instance

end Decidable

/-! ### Exact values on a power basis

A value in `ℚ(ζ)` with `ζ ^ m = r` rational is a list of rational coefficients on `1, ζ, ζ², …`. The kernel multiplies
such lists cheaply (zero is the empty list and short-circuits), reducing by `ζ ^ m = r`, and `Coeffs.eval ζ` sends them
into any `ℚ`-algebra with such a `ζ`, respecting sums and products. Data given by coefficients (`RepData`) are thus
checked once, by the kernel, and hold for every `ζ` with `ζ ^ m = r`: over `ℂ` for `ζ = exp (2πi/16)` and also at its
Galois conjugates. -/

namespace Coeffs

/-- The sum of coefficient lists. -/
def add : List ℚ → List ℚ → List ℚ
  | [], l => l
  | a :: l, [] => a :: l
  | a :: l, b :: l' => (a + b) :: add l l'

/-- A rational multiple of a coefficient list. -/
def smul (q : ℚ) (l : List ℚ) : List ℚ :=
  l.map (q * ·)

/-- The product of coefficient lists, as polynomials in `ζ`. -/
def mul : List ℚ → List ℚ → List ℚ
  | [], _ => []
  | a :: l, l' => add (smul a l') (0 :: mul l l')

/-- The reduction of a list by `ζ ^ m = r`, once: enough after one product of reduced lists. -/
def reduce (m : ℕ) (r : ℚ) (l : List ℚ) : List ℚ :=
  add (l.take m) (smul r (l.drop m))

/-- The product of coefficient lists, reduced by `ζ ^ m = r`. -/
def mulMod (m : ℕ) (r : ℚ) (x y : List ℚ) : List ℚ :=
  reduce m r (mul x y)

/-- The difference of coefficient lists. -/
def sub (x y : List ℚ) : List ℚ :=
  add x (smul (-1) y)

/-- The sum of a family of coefficient lists indexed by `Fin n`. -/
def sum {n : ℕ} (f : Fin n → List ℚ) : List ℚ :=
  (List.ofFn f).foldr add []

/-- Every coefficient vanishes. -/
def IsZero (l : List ℚ) : Prop :=
  ∀ q ∈ l, q = 0

instance (l : List ℚ) : Decidable (IsZero l) := by unfold IsZero; infer_instance

variable {K : Type*} [CommRing K] [Algebra ℚ K] (ζ : K)

/-- The value `Σ lᵢ ζⁱ` of a coefficient list. -/
def eval : List ℚ → K
  | [] => 0
  | a :: l => algebraMap ℚ K a + ζ * eval l

@[simp] theorem eval_nil : eval ζ [] = 0 := rfl

@[simp] theorem eval_cons (a : ℚ) (l : List ℚ) : eval ζ (a :: l) = algebraMap ℚ K a + ζ * eval ζ l := rfl

theorem eval_add : ∀ x y : List ℚ, eval ζ (add x y) = eval ζ x + eval ζ y
  | [], l => by simp [add]
  | a :: l, [] => by simp [add]
  | a :: l, b :: l' => by simp only [add, eval_cons, eval_add l l', map_add]; ring

theorem eval_smul (q : ℚ) : ∀ l : List ℚ, eval ζ (smul q l) = algebraMap ℚ K q * eval ζ l
  | [] => by simp [smul]
  | a :: l => by
    have := eval_smul q l
    simp only [smul, List.map_cons, eval_cons, map_mul] at this ⊢
    rw [this]; ring

theorem eval_mul (y : List ℚ) : ∀ x : List ℚ, eval ζ (mul x y) = eval ζ x * eval ζ y
  | [] => by simp [mul]
  | a :: l => by simp only [mul, eval_add, eval_smul, eval_cons, eval_mul y l, map_zero]; ring

theorem eval_take_drop : ∀ (m : ℕ) (l : List ℚ), eval ζ l = eval ζ (l.take m) + ζ ^ m * eval ζ (l.drop m)
  | 0, l => by simp
  | _ + 1, [] => by simp
  | m + 1, a :: l => by simp only [List.take_succ_cons, List.drop_succ_cons, eval_cons, eval_take_drop m l]; ring

variable {ζ} {m : ℕ} {r : ℚ}

theorem eval_mulMod (hζ : ζ ^ m = algebraMap ℚ K r) (x y : List ℚ) :
    eval ζ (mulMod m r x y) = eval ζ x * eval ζ y := by
  rw [mulMod, reduce, eval_add, eval_smul, ← hζ, ← eval_take_drop, eval_mul]

theorem eval_sub (x y : List ℚ) : eval ζ (sub x y) = eval ζ x - eval ζ y := by
  simp [sub, eval_add, eval_smul]; ring

theorem eval_sum : ∀ {n : ℕ} (f : Fin n → List ℚ), eval ζ (sum f) = ∑ i, eval ζ (f i)
  | 0, f => by simp [sum]
  | n + 1, f => by
    have := eval_sum (fun i : Fin n => f i.succ)
    simp only [sum, List.ofFn_succ, List.foldr_cons, eval_add, Fin.sum_univ_succ] at this ⊢
    rw [this]

theorem eval_eq_zero : ∀ {l : List ℚ}, IsZero l → eval ζ l = 0
  | [], _ => rfl
  | a :: l, h => by
    rw [eval_cons, h a List.mem_cons_self, eval_eq_zero fun q hq => h q (List.mem_cons_of_mem a hq)]
    simp

theorem eq_of_isZero_sub {x y : List ℚ} (h : IsZero (sub x y)) : eval ζ x = eval ζ y :=
  sub_eq_zero.mp ((eval_sub x y).symm.trans (eval_eq_zero h))

end Coeffs

open Coeffs

/-- Multiplicity-free fusion data on labels `Fin n` with values given by coefficient lists on a power basis. -/
structure RepData (n : ℕ) where
  /-- The unit object. -/
  unit : Fin n
  /-- The dual of each object. -/
  dual : Fin n → Fin n
  /-- `N a b c`: the multiplicity of `c` in `a ⊗ b`, 0 or 1. -/
  N : Fin n → Fin n → Fin n → ℕ
  /-- The F-symbols' coefficients. -/
  F : Fin n → Fin n → Fin n → Fin n → Fin n → Fin n → List ℚ
  /-- The R-symbols' coefficients. -/
  R : Fin n → Fin n → Fin n → List ℚ
  /-- The inverse R-symbols' coefficients. -/
  Rinv : Fin n → Fin n → Fin n → List ℚ

namespace RepData

variable {n : ℕ} (E : RepData n) (m : ℕ) (r : ℚ)

/-- The fusion data with values at `ζ`. -/
def toData {K : Type*} [CommRing K] [Algebra ℚ K] (ζ : K) : Data (Fin n) K :=
  ⟨E.unit, E.dual, E.N, fun a b c d e f => eval ζ (E.F a b c d e f), fun a b c => eval ζ (E.R a b c),
    fun a b c => eval ζ (E.Rinv a b c)⟩

/-- F-symbols vanish on inadmissible labels. -/
def FSupported : Prop :=
  ∀ a b c d e f, ¬ IsZero (E.F a b c d e f) → E.N a b e ≠ 0 ∧ E.N e c d ≠ 0 ∧ E.N b c f ≠ 0 ∧ E.N a f d ≠ 0

/-- The pentagon equations on admissible labels, in coefficients. -/
def PentagonOn : Prop :=
  ∀ a b f, E.N a b f ≠ 0 → ∀ c g, E.N f c g ≠ 0 → ∀ d e, E.N g d e ≠ 0 → ∀ l, E.N c d l ≠ 0 → ∀ k, E.N b l k ≠ 0 →
    E.N a k e ≠ 0 → IsZero (sub (mulMod m r (E.F f c d e g l) (E.F a b l e f k))
      (sum fun h => mulMod m r (mulMod m r (E.F a b c g f h) (E.F a h d e g k)) (E.F b c d k h l)))

/-- The inverse braiding on admissible labels, in coefficients. -/
def InverseBraiding : Prop :=
  ∀ a b c, E.N a b c ≠ 0 → IsZero (sub (mulMod m r (E.R a b c) (E.Rinv a b c)) [1])

/-- The first hexagon on admissible labels, in coefficients. -/
def HexagonOneOn : Prop :=
  ∀ e b d, E.N e b d ≠ 0 → ∀ a g, E.N a g d ≠ 0 → ∀ c,
    IsZero (sub (mulMod m r (mulMod m r (E.R c a e) (E.F a c b d e g)) (E.R c b g))
      (sum fun f => mulMod m r (mulMod m r (E.F c a b d e f) (E.R c f d)) (E.F a b c d f g)))

/-- The second hexagon on admissible labels, in coefficients. -/
def HexagonTwoOn : Prop :=
  ∀ e b d, E.N e b d ≠ 0 → ∀ a g, E.N a g d ≠ 0 → ∀ c,
    IsZero (sub (mulMod m r (mulMod m r (E.Rinv a c e) (E.F a c b d e g)) (E.Rinv b c g))
      (sum fun f => mulMod m r (mulMod m r (E.F c a b d e f) (E.Rinv f c d)) (E.F a b c d f g)))

/-- `E'` is `E` in the gauge `U` with inverse `Uinv`, in coefficients. -/
def GaugeCheck (E' : RepData n) (U Uinv : Fin n → Fin n → Fin n → List ℚ) : Prop :=
  E'.N = E.N ∧ (∀ a b c, E.N a b c ≠ 0 → IsZero (sub (mulMod m r (U a b c) (Uinv a b c)) [1])) ∧
    (∀ a b c d e f, IsZero (sub (mulMod m r (E'.F a b c d e f) (mulMod m r (U b c f) (U a f d)))
      (mulMod m r (mulMod m r (U a b e) (U e c d)) (E.F a b c d e f)))) ∧
    ∀ a b c, IsZero (sub (mulMod m r (E'.R a b c) (U a b c)) (mulMod m r (U b a c) (E.R a b c)))

/-- The fusion ring: associativity, unit and duals (these involve the multiplicities only). -/
def IsFusionRing : Prop :=
  Associative (E.toData (0 : ℚ)) ∧ HasUnit (E.toData (0 : ℚ)) ∧ HasDuals (E.toData (0 : ℚ))

/-- What the kernel checks for fusion data in coefficients. -/
def FusionCheck : Prop :=
  E.IsFusionRing ∧ E.FSupported ∧ E.PentagonOn m r

/-- What the kernel checks for braided fusion data in coefficients. -/
def BraidedFusionCheck : Prop :=
  E.FusionCheck m r ∧ E.InverseBraiding m r ∧ E.HexagonOneOn m r ∧ E.HexagonTwoOn m r

instance : Decidable E.IsFusionRing := by unfold IsFusionRing; infer_instance
instance : Decidable E.FSupported := by unfold FSupported; infer_instance
instance : Decidable (E.PentagonOn m r) := by unfold PentagonOn; infer_instance
instance : Decidable (E.InverseBraiding m r) := by unfold InverseBraiding; infer_instance
instance : Decidable (E.HexagonOneOn m r) := by unfold HexagonOneOn; infer_instance
instance : Decidable (E.HexagonTwoOn m r) := by unfold HexagonTwoOn; infer_instance
instance : Decidable (E.FusionCheck m r) := by unfold FusionCheck; infer_instance
instance : Decidable (E.BraidedFusionCheck m r) := by unfold BraidedFusionCheck; infer_instance
instance (E' : RepData n) (U Uinv : Fin n → Fin n → Fin n → List ℚ) : Decidable (E.GaugeCheck m r E' U Uinv) := by
  unfold GaugeCheck; infer_instance

variable {E m r} {K : Type*} [CommRing K] [Algebra ℚ K] {ζ : K}

theorem fSupported (h : E.FSupported) : FusionData.FSupported (E.toData ζ) := fun a b c d e f hne =>
  h a b c d e f fun hz => hne (eval_eq_zero hz)

theorem fusionRing (h : E.IsFusionRing) :
    Associative (E.toData ζ) ∧ HasUnit (E.toData ζ) ∧ HasDuals (E.toData ζ) :=
  h

theorem pentagon (hζ : ζ ^ m = algebraMap ℚ K r) (hF : E.FSupported) (h : E.PentagonOn m r) :
    Pentagon (E.toData ζ) := by
  refine pentagon_of_on (fSupported hF) fun a b f h₁ c g h₂ d e h₃ l h₄ k h₅ h₆ => ?_
  have := eq_of_isZero_sub (ζ := ζ) (h a b f h₁ c g h₂ d e h₃ l h₄ k h₅ h₆)
  simpa only [toData, eval_mulMod hζ, eval_sum] using this

theorem isFusion (hζ : ζ ^ m = algebraMap ℚ K r) (h : E.FusionCheck m r) : IsFusion (E.toData ζ) :=
  let ⟨⟨h₁, h₂, h₃⟩, hF, hP⟩ := h
  ⟨h₁, h₂, h₃, pentagon hζ hF hP⟩

theorem isBraidedFusion (hζ : ζ ^ m = algebraMap ℚ K r) (h : E.BraidedFusionCheck m r) :
    IsBraidedFusion (E.toData ζ) := by
  obtain ⟨⟨⟨h₁, h₂, h₃⟩, hF, hP⟩, hI, hO, hT⟩ := h
  refine ⟨h₁, h₂, h₃, pentagon hζ hF hP, fun a b c hn => ?_, hexagonOne_of_on (fSupported hF) ?_,
    hexagonTwo_of_on (fSupported hF) ?_⟩
  · simpa [toData, eval_mulMod hζ] using eq_of_isZero_sub (ζ := ζ) (hI a b c hn)
  · intro e b d h₁ a g h₂ c
    simpa only [toData, eval_mulMod hζ, eval_sum] using eq_of_isZero_sub (ζ := ζ) (hO e b d h₁ a g h₂ c)
  · intro e b d h₁ a g h₂ c
    simpa only [toData, eval_mulMod hζ, eval_sum] using eq_of_isZero_sub (ζ := ζ) (hT e b d h₁ a g h₂ c)

theorem gaugeRelated (hζ : ζ ^ m = algebraMap ℚ K r) {E' : RepData n} {U Uinv : Fin n → Fin n → Fin n → List ℚ}
    (h : E.GaugeCheck m r E' U Uinv) :
    GaugeRelated (E.toData ζ) (E'.toData ζ) (fun a b c => eval ζ (U a b c)) (fun a b c => eval ζ (Uinv a b c)) := by
  obtain ⟨hN, hI, hF, hR⟩ := h
  refine ⟨hN, fun a b c hn => ?_, fun a b c d e f => ?_, fun a b c => ?_⟩
  · simpa [eval_mulMod hζ] using eq_of_isZero_sub (ζ := ζ) (hI a b c hn)
  · simpa only [toData, eval_mulMod hζ] using eq_of_isZero_sub (ζ := ζ) (hF a b c d e f)
  · simpa only [toData, eval_mulMod hζ] using eq_of_isZero_sub (ζ := ζ) (hR a b c)

end RepData

/-- The trivial category (one object, everything 1) is braided fusion. -/
theorem trivial_isBraidedFusion :
    IsBraidedFusion (⟨(), id, fun _ _ _ => 1, fun _ _ _ _ _ _ => 1, fun _ _ _ => 1, fun _ _ _ => 1⟩ : Data Unit ℚ) := by
  refine ⟨fun _ _ _ _ => ?_, fun _ _ => ?_, fun _ => ?_, fun _ _ _ _ _ _ _ _ _ => ?_, fun _ _ _ _ => ?_,
    fun _ _ _ _ _ _ => ?_, fun _ _ _ _ _ _ => ?_⟩ <;> simp

end FusionData
