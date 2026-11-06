/-
Matrix identities checked by kernel evaluation.

Each check is a decidable proposition about the entries of square matrices over a commutative ring with decidable
equality, computed by folds over `List.finRange n`; a soundness theorem turns it into the mathlib statement. A proof
is `VeriphyCheck.mul_eq_of_check (by decide +kernel)`: the kernel evaluates the check (with its accelerated natural
number arithmetic), so no `native_decide` and no axiom beyond the standard ones is involved. The matrices are taken
from the goal itself, `!![…]` literals included.
-/
import Mathlib.Data.Matrix.Mul
import Mathlib.LinearAlgebra.Matrix.Trace
import Mathlib.Algebra.Lie.OfAssociative

namespace VeriphyCheck

open Matrix

variable {R : Type*} [CommRing R] {n : ℕ}

/-- `∑ k, f k * g k`, computed by a fold the kernel evaluates. -/
def dot (f g : Fin n → R) : R := (List.finRange n).foldr (fun k s => f k * g k + s) 0

theorem dot_eq (f g : Fin n → R) : dot f g = ∑ k, f k * g k := by
  rw [Fin.sum_univ_def, dot]
  induction (List.finRange n) with
  | nil => simp
  | cons k ks ih => simp [List.foldr, ih]

/-- `p i j` for every pair of indices, computed by `List.all` (which the kernel evaluates directly). -/
def allEntries (p : Fin n → Fin n → Bool) : Bool :=
  (List.finRange n).all fun i => (List.finRange n).all fun j => p i j

theorem of_allEntries {p : Fin n → Fin n → Bool} (h : allEntries p = true) (i j : Fin n) : p i j = true := by
  simp only [allEntries, List.all_eq_true, List.mem_finRange, true_implies] at h
  exact h i j

/-- `∑ k, xs k * ys k` over two lists, by a fold the kernel evaluates. -/
def dotList : List R → List R → R
  | x :: xs, y :: ys => x * y + dotList xs ys
  | _, _ => 0

/-- The entries of a vector, as a list (read once, so later accesses do not walk a `!![…]` literal again). -/
def toList (f : Fin n → R) : List R := (List.finRange n).map f

theorem dotList_toList (f g : Fin n → R) : dotList (toList f) (toList g) = dot f g := by
  simp only [toList, dot]
  induction (List.finRange n) with
  | nil => rfl
  | cons k ks ih => simp [List.map, dotList, ih]

/-- The rows of `A`, as lists. -/
def rowLists (A : Matrix (Fin n) (Fin n) R) : List (List R) := (List.finRange n).map fun i => toList (A i)

/-- The columns of `A`, as lists. -/
def colLists (A : Matrix (Fin n) (Fin n) R) : List (List R) := (List.finRange n).map fun j => toList (fun k => A k j)

omit [CommRing R] in
theorem rowLists_getD (A : Matrix (Fin n) (Fin n) R) (i : Fin n) : (rowLists A).getD i [] = toList (A i) := by
  simp [rowLists, List.getD_eq_getElem?_getD]

omit [CommRing R] in
theorem colLists_getD (A : Matrix (Fin n) (Fin n) R) (j : Fin n) :
    (colLists A).getD j [] = toList (fun k => A k j) := by
  simp [colLists, List.getD_eq_getElem?_getD]

variable [DecidableEq R]

/-- Every entry of `A * B` equals that of `C`: rows of `A` and columns of `B` are read once, so the check costs
`n³` ring operations. -/
def mulCheck (A B C : Matrix (Fin n) (Fin n) R) : Bool :=
  let rows := rowLists A
  let cols := colLists B
  allEntries fun i j => dotList (rows.getD i []) (cols.getD j []) == C i j

theorem mul_eq_of_check {A B C : Matrix (Fin n) (Fin n) R} (h : mulCheck A B C = true) : A * B = C := by
  ext i j
  have := of_allEntries h i j
  rw [beq_iff_eq, rowLists_getD, colLists_getD, dotList_toList] at this
  rw [Matrix.mul_apply, ← this, dot_eq]

/-- Every entry of `A * B` equals that of `C * D`: an intertwining `T * ρ x = σ x * T`, or a change of basis
`ρ x * P = P * B`, at `2n³` ring operations. -/
def mulMulCheck (A B C D : Matrix (Fin n) (Fin n) R) : Bool :=
  let rowsA := rowLists A
  let colsB := colLists B
  let rowsC := rowLists C
  let colsD := colLists D
  allEntries (n := n) fun i j =>
    dotList (rowsA.getD i []) (colsB.getD j []) == dotList (rowsC.getD i []) (colsD.getD j [])

theorem mul_eq_mul_of_check {A B C D : Matrix (Fin n) (Fin n) R} (h : mulMulCheck A B C D = true) :
    A * B = C * D := by
  ext i j
  have := of_allEntries h i j
  rw [beq_iff_eq, rowLists_getD, colLists_getD, dotList_toList, rowLists_getD, colLists_getD, dotList_toList] at this
  rw [Matrix.mul_apply, Matrix.mul_apply, ← dot_eq, ← dot_eq, this]

/-- Every entry of `A * B - B * A` equals that of `C`, at `2n³` ring operations. -/
def bracketCheck (A B C : Matrix (Fin n) (Fin n) R) : Bool :=
  let rowsA := rowLists A
  let colsA := colLists A
  let rowsB := rowLists B
  let colsB := colLists B
  allEntries fun i j =>
    dotList (rowsA.getD i []) (colsB.getD j []) - dotList (rowsB.getD i []) (colsA.getD j []) == C i j

theorem commutator_eq_of_check {A B C : Matrix (Fin n) (Fin n) R} (h : bracketCheck A B C = true) :
    A * B - B * A = C := by
  ext i j
  have := of_allEntries h i j
  rw [beq_iff_eq, rowLists_getD, colLists_getD, rowLists_getD, colLists_getD, dotList_toList,
    dotList_toList] at this
  rw [Matrix.sub_apply, Matrix.mul_apply, Matrix.mul_apply, ← this, dot_eq, dot_eq]

theorem bracket_eq_of_check {A B C : Matrix (Fin n) (Fin n) R} (h : bracketCheck A B C = true) : ⁅A, B⁆ = C := by
  rw [Ring.lie_def, commutator_eq_of_check h]

theorem commute_of_check {A B : Matrix (Fin n) (Fin n) R} (h : bracketCheck A B 0 = true) : A * B = B * A :=
  sub_eq_zero.mp (commutator_eq_of_check h)

/-- The diagonal of `A` sums to `c`. -/
def traceCheck (A : Matrix (Fin n) (Fin n) R) (c : R) : Bool :=
  dot (fun k => A k k) (fun _ => 1) == c

theorem trace_eq_of_check {A : Matrix (Fin n) (Fin n) R} {c : R} (h : traceCheck A c = true) : A.trace = c := by
  rw [traceCheck, beq_iff_eq] at h
  rw [← h, dot_eq, Matrix.trace]
  simp

/-- Every entry of `A` equals that of `B`. -/
def eqCheck (A B : Matrix (Fin n) (Fin n) R) : Bool := allEntries fun i j => A i j == B i j

omit [CommRing R] in
theorem eq_of_check {A B : Matrix (Fin n) (Fin n) R} (h : eqCheck A B = true) : A = B := by
  ext i j
  exact beq_iff_eq.mp (of_allEntries h i j)

/-! ### Certificates carrying their data

For large matrices the certificate states the rows of `A`, the columns of `B` and the rows of `C` as list literals,
so the main check walks lists structurally; three equality checks tie the lists to the goal's matrices. -/

/-- Each row's dot products with every column match the corresponding row of the product. -/
def rowCheck (r : List R) : List (List R) → List R → Bool
  | c :: cs, x :: xs => dotList r c == x && rowCheck r cs xs
  | [], [] => true
  | _, _ => false

/-- `rows · cols = product`, walking the three lists. -/
def listMulCheck (cols : List (List R)) : List (List R) → List (List R) → Bool
  | r :: rs, p :: ps => rowCheck r cols p && listMulCheck cols rs ps
  | [], [] => true
  | _, _ => false

theorem rowCheck_get {r : List R} {cols : List (List R)} {p : List R} (h : rowCheck r cols p = true) :
    cols.length = p.length ∧ ∀ j < cols.length, dotList r (cols.getD j []) = p.getD j 0 := by
  induction cols generalizing p with
  | nil => cases p <;> simp_all [rowCheck]
  | cons c cs ih =>
    cases p with
    | nil => simp [rowCheck] at h
    | cons x xs =>
      simp only [rowCheck, Bool.and_eq_true, beq_iff_eq] at h
      obtain ⟨h1, h2⟩ := ih h.2
      refine ⟨by simp [h1], fun j hj => ?_⟩
      cases j with
      | zero => simpa using h.1
      | succ j => simpa using h2 j (by simpa using hj)

theorem listMulCheck_get {cols rows prod : List (List R)} (h : listMulCheck cols rows prod = true) :
    rows.length = prod.length ∧
      ∀ i < rows.length, cols.length = (prod.getD i []).length ∧
        ∀ j < cols.length, dotList (rows.getD i []) (cols.getD j []) = (prod.getD i []).getD j 0 := by
  induction rows generalizing prod with
  | nil => cases prod <;> simp_all [listMulCheck]
  | cons r rs ih =>
    cases prod with
    | nil => simp [listMulCheck] at h
    | cons p ps =>
      simp only [listMulCheck, Bool.and_eq_true] at h
      obtain ⟨h1, h2⟩ := ih h.2
      refine ⟨by simp [h1], fun i hi => ?_⟩
      cases i with
      | zero => simpa using rowCheck_get h.1
      | succ i => simpa using h2 i (by simpa using hi)

omit [CommRing R] [DecidableEq R] in
theorem rowLists_length (A : Matrix (Fin n) (Fin n) R) : (rowLists A).length = n := by simp [rowLists]

omit [CommRing R] [DecidableEq R] in
theorem colLists_length (A : Matrix (Fin n) (Fin n) R) : (colLists A).length = n := by simp [colLists]

omit [DecidableEq R] in
theorem toList_getD (f : Fin n → R) (j : Fin n) : (toList f).getD j 0 = f j := by
  simp [toList, List.getD_eq_getElem?_getD]

/-- `A * B = C` from list data: the rows of `A`, the columns of `B` and the rows of `C` are the given lists,
and the lists multiply. -/
theorem mul_eq_of_lists {A B C : Matrix (Fin n) (Fin n) R} {rows cols prod : List (List R)}
    (hA : rowLists A = rows) (hB : colLists B = cols) (hC : rowLists C = prod)
    (h : listMulCheck cols rows prod = true) : A * B = C := by
  subst hA hB hC
  obtain ⟨_, h2⟩ := listMulCheck_get h
  ext i j
  have hij := (h2 i (by simp [rowLists_length])).2 j (by simp [colLists_length])
  rw [rowLists_getD, colLists_getD, rowLists_getD, toList_getD, dotList_toList, dot_eq] at hij
  rw [Matrix.mul_apply, hij]

/-! ### Matrices built from lists

`ofLists n rows` is the matrix whose rows are the lists, built from vector conses exactly as a `!![…]` literal is,
so a goal's literal and the certificate's matrix agree by unfolding (`rfl`), not entry by entry. -/

/-- The vector of the first `n` entries of a list (zeros past its end), as nested `vecCons`. -/
def listVec : (n : ℕ) → List R → Fin n → R
  | 0, _ => Matrix.vecEmpty
  | n + 1, x :: xs => Matrix.vecCons x (listVec n xs)
  | n + 1, [] => Matrix.vecCons 0 (listVec n [])

omit [DecidableEq R] in
theorem listVec_apply : ∀ (n : ℕ) (l : List R) (i : Fin n), listVec n l i = l.getD i 0
  | 0, _, i => i.elim0
  | n + 1, x :: xs, i => by
    refine Fin.cases ?_ (fun j => ?_) i
    · simp [listVec]
    · simp [listVec, listVec_apply n xs j]
  | n + 1, [], i => by
    refine Fin.cases ?_ (fun j => ?_) i
    · simp [listVec]
    · simp [listVec, listVec_apply n [] j]

/-- The `n × n` matrix whose rows are the given lists. -/
def ofLists (n : ℕ) (rows : List (List R)) : Matrix (Fin n) (Fin n) R :=
  Matrix.of (listVec n (rows.map (listVec n)))

omit [DecidableEq R] in
theorem ofLists_apply (rows : List (List R)) (i j : Fin n) :
    ofLists n rows i j = (rows.getD i []).getD j 0 := by
  simp only [ofLists, Matrix.of_apply, listVec_apply]
  rw [List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD]
  cases h : rows[(i : ℕ)]? with
  | none => simp [List.getElem?_map, h]
  | some r => simp [List.getElem?_map, h, listVec_apply, List.getD_eq_getElem?_getD]

/-- The columns of a list of rows, each of length `n`. -/
def columns (n : ℕ) (rows : List (List R)) : List (List R) :=
  (List.range n).map fun j => rows.map fun r => r.getD j 0

/-- `rows` has `n` rows of `n` entries. -/
def square (n : ℕ) (rows : List (List R)) : Bool := rows.length == n && rows.all (·.length == n)

omit [DecidableEq R] in
theorem dotList_getD : ∀ (n : ℕ) (r c : List R), r.length = n → c.length = n →
    dotList r c = ∑ k : Fin n, r.getD k 0 * c.getD k 0
  | 0, r, c, hr, hc => by
    rw [List.length_eq_zero_iff] at hr hc
    subst hr hc
    simp [dotList]
  | n + 1, x :: xs, y :: ys, hr, hc => by
    rw [Fin.sum_univ_succ]
    simp only [List.length_cons, add_left_inj] at hr hc
    simp [dotList, dotList_getD n xs ys hr hc]
  | n + 1, [], _, hr, _ => by simp at hr
  | n + 1, _ :: _, [], _, hc => by simp at hc

omit [DecidableEq R] in
theorem getD_map_getD (l : List (List R)) (j k : ℕ) :
    (l.map fun r => r.getD j 0).getD k 0 = (l.getD k []).getD j 0 := by
  cases h : l[k]? <;> simp [List.getD_eq_getElem?_getD, List.getElem?_map, h]

/-- `ofLists n rows₁ * ofLists n rows₂ = ofLists n prod`, from the list data. -/
theorem ofLists_mul {rows₁ rows₂ prod : List (List R)}
    (hsq : (square n rows₁ && square n rows₂ && square n prod) = true)
    (h : listMulCheck (columns n rows₂) rows₁ prod = true) :
    ofLists n rows₁ * ofLists n rows₂ = ofLists n prod := by
  simp only [square, Bool.and_eq_true, beq_iff_eq, List.all_eq_true] at hsq
  obtain ⟨⟨⟨h1, h1r⟩, h2, h2r⟩, h3, h3r⟩ := hsq
  obtain ⟨_, hrows⟩ := listMulCheck_get h
  ext i j
  have hi : (i : ℕ) < rows₁.length := by simp [h1]
  have hj : (j : ℕ) < (columns n rows₂).length := by simp [columns]
  have hij := (hrows i hi).2 j hj
  rw [Matrix.mul_apply, ofLists_apply, ← hij]
  have hrow : (rows₁.getD i []).length = n := by
    rw [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem hi]; exact h1r _ (List.getElem_mem hi)
  have hcol : ((columns n rows₂).getD j []).length = n := by
    simp [columns, List.getD_eq_getElem?_getD, h2]
  rw [dotList_getD n _ _ hrow hcol]
  refine Finset.sum_congr rfl fun k _ => ?_
  rw [ofLists_apply, ofLists_apply]
  congr 1
  rw [← getD_map_getD]
  simp [columns, List.getD_eq_getElem?_getD, List.getElem?_map]

/-! ### Packed rows

A certificate row of integers is one natural number: entry `k` is digit `k` in base `2 ^ width`, minus `offset`.
The kernel decodes it with its accelerated division, so a large certificate elaborates `n` numerals, not `n²`. -/

/-- The `n` integers packed in `code`, peeled one digit at a time (no large powers are formed). -/
def unpack (width offset : ℕ) : ℕ → ℕ → List ℤ
  | 0, _ => []
  | n + 1, code => ((code % 2 ^ width : ℕ) - (offset : ℤ)) :: unpack width offset n (code / 2 ^ width)

/-- The rows packed in `codes`. -/
def unpackRows (width offset n : ℕ) (codes : List ℕ) : List (List ℤ) := codes.map (unpack width offset n)

end VeriphyCheck
