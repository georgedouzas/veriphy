/-
Symbolic translation: Lean terms → Sage symbolic-ring expressions, with typed atoms and the domain
conditions (denominators nonzero, `sqrt` arguments nonnegative, `log` arguments positive) a Lean check
of a proof built from them will need.

The function, constant and coercion entries are data (`Veriphy.Kit.Table`, after LeanSage's `ExprToAST.lean`);
`abs` is translated as the absolute value of the argument's own type (LeanSage maps it to `Int.natAbs`).

Nothing here is trusted: a mistranslation makes the emitted proof fail in Lean, never prove
something else.
-/
import Veriphy.Translate
import Veriphy.Kit.Table

namespace Veriphy

open Lean Meta

/-- A symbolic expression over the problem's atoms, rendered to Sage syntax for the daemon. -/
inductive SymExpr
  | num (n : Int) (d : Nat)
  | atom (i : Nat)
  /-- A variable bound by a range sum or product, or the polynomial variable `X`. -/
  | bvar (name : String)
  | add (a b : SymExpr)
  | sub (a b : SymExpr)
  | mul (a b : SymExpr)
  | div (a b : SymExpr)
  | neg (a : SymExpr)
  | pow (a b : SymExpr)
  | mod (a b : SymExpr)
  /-- A one-argument function of the table (`sqrt`, `exp`, `log`, …, `abs`). -/
  | fn (name : String) (arg : SymExpr)
  /-- A function of the table with several arguments (`binomial`, `log` to a base, …). -/
  | call (name : String) (args : List SymExpr)
  /-- `pi` or `I`. -/
  | const (name : String)
  /-- `∑ k ∈ Finset.range n, body`, or the product with `isSum := false`. -/
  | rangeOp (isSum : Bool) (k : String) (n body : SymExpr)
  /-- `∑ k ∈ Finset.Icc lo hi, body` (and `Ico`, `univ` over `Fin n`), bounds inclusive; `isSum := false` for products. -/
  | interval (isSum : Bool) (k : String) (lo hi body : SymExpr)
  | matrix (rows : List (List SymExpr))
  /-- A method applied to its first argument in Sage (`det`, `trace`, `transpose`, `inverse`, polynomial
  `coefficient`, `degree`, evaluation). -/
  | method (name : String) (self : SymExpr) (args : List SymExpr)
  /-- A sub-expression computed at another Lean type (`ℕ`, `ℤ`) than its context, such as the `n % 7` inside
  `((n % 7 : ℕ) : ℝ)`; the rendering restores the cast. -/
  | typed (ty : String) (e : SymExpr)
  deriving Inhabited, Repr

/-- Sage syntax for a symbolic expression. -/
partial def SymExpr.toSage : SymExpr → String
  | .num n 1 => if n < 0 then s!"({n})" else s!"{n}"
  | .num n d => s!"({n}/{d})"
  | .atom i => s!"x{i}"
  | .bvar k => k
  | .add a b => s!"({a.toSage} + {b.toSage})"
  | .sub a b => s!"({a.toSage} - {b.toSage})"
  | .mul a b => s!"({a.toSage} * {b.toSage})"
  | .div a b => s!"({a.toSage} / {b.toSage})"
  | .neg a => s!"(-{a.toSage})"
  | .pow a b => s!"({a.toSage})^({b.toSage})"
  | .mod a b => s!"mod({a.toSage}, {b.toSage})"
  | .fn f a => s!"{f}({a.toSage})"
  | .call f as => s!"{f}(" ++ ", ".intercalate (as.map (·.toSage)) ++ ")"
  | .const c => c
  | .rangeOp true k n body => s!"sum({body.toSage}, {k}, 0, {n.toSage} - 1)"
  | .rangeOp false k n body => s!"product({body.toSage}, {k}, 0, {n.toSage} - 1)"
  | .interval true k lo hi body => s!"sum({body.toSage}, {k}, {lo.toSage}, {hi.toSage})"
  | .interval false k lo hi body => s!"product({body.toSage}, {k}, {lo.toSage}, {hi.toSage})"
  | .matrix rows =>
    let row (r : List SymExpr) := "[" ++ ", ".intercalate (r.map (·.toSage)) ++ "]"
    "matrix(SR, [" ++ ", ".intercalate (rows.map row) ++ "])"
  | .method m self args =>
    s!"({self.toSage}).{m}(" ++ ", ".intercalate (args.map (·.toSage)) ++ ")"
  | .typed ty e => s!"typed({e.toSage}, '{ty}')"

/-- The kind of domain condition an expression needs. -/
inductive DomainKind | ne | nonneg | pos | le
  deriving BEq, Inhabited, Repr

/-- `e ≠ 0`, `0 ≤ e` or `0 < e` (a denominator, a `sqrt`, a `log`), or `e ≤ bound` for `le` (ℕ subtraction,
inverse-trigonometric domains). -/
structure Condition where
  term : Expr
  kind : DomainKind
  bound : Option Expr := none
  deriving Inhabited

/-- The translation state: the atom table (shared with the polynomial translator), the bound variables
in scope and the conditions met so far. -/
structure SymState where
  atoms : Array Expr
  bound : Array (Expr × String) := #[]
  conditions : Array Condition := #[]
  /-- The translation tables in force, core first. -/
  tables : Tables := [coreTable]

abbrev SymM := StateRefT SymState MetaM

private def note (term : Expr) (kind : DomainKind) (bound : Option Expr := none) : SymM Unit :=
  modify fun s => { s with conditions := s.conditions.push { term, kind, bound } }

/-- An entry's operand: an argument `#i`, or an integer numeral at the type of the arguments. -/
private def operand? (spec : String) (operands : Array Expr) : MetaM (Option Expr) := do
  if spec.startsWith "#" then return (spec.drop 1).toString.toNat?.bind (operands[·]?)
  let some ty ← operands[0]?.mapM inferType | return none
  let some n := spec.toInt? | return none
  let lit ← mkAppOptM ``OfNat.ofNat #[ty, mkRawNatLit n.natAbs, none]
  if n < 0 then return some (← mkAppM ``Neg.neg #[lit]) else return some lit

/-- Record the single-argument conditions an entry imposes on its operands. -/
private def noteConditions (entry : FunctionEntry) (operands : Array Expr) : SymM Unit := do
  for c in entry.conditions do
    if c.kind == "le" then
      let (some l, some r) := (c.lhs, c.rhs) | continue
      let (some a, some b) := (← operand? l operands, ← operand? r operands) | continue
      note a .le b
      continue
    let some i := c.arg | continue
    let some x := operands[i]? | continue
    match c.kind with
    | "ne" =>
      match c.rhs with
      | some r => if let some b ← operand? r operands then note x .ne b
      | none => note x .ne
    | "nonneg" => note x .nonneg
    | "pos" => note x .pos
    | _ => pure ()

/-- Register `e` as an atom, reusing a definitionally equal one. -/
private def symAtom (e : Expr) : SymM SymExpr := do
  let s ← get
  for h : i in [0:s.atoms.size] do
    if ← withReducible (isDefEq s.atoms[i] e) then return .atom i
  set { s with atoms := s.atoms.push e }
  return .atom s.atoms.size

private def lastArg (e : Expr) : Expr := e.getAppArgs.back!

/-- The rows of a `Matrix.of ![![…], …]` literal, as nested `vecCons` lists. -/
private partial def vecList (e : Expr) : Option (List Expr) :=
  match e.getAppFnArgs with
  | (`Matrix.vecCons, #[_, _, x, rest]) => (x :: ·) <$> vecList rest
  | (`Matrix.vecEmpty, _) => some []
  | _ => none

/-- The Lean type class of an atom: `ℕ`, `ℤ`, `ℚ`, `ℝ`, `ℂ`, `matrix` or `other`. -/
def atomType (a : Expr) : MetaM String := do
  let ty ← whnfR (← inferType a)
  if ty.isAppOf `Matrix then return "matrix"
  match ty.constName? with
  | some ``Nat => return "ℕ"
  | some ``Int => return "ℤ"
  | some ``Rat => return "ℚ"
  | some `Real => return "ℝ"
  | some `Complex => return "ℂ"
  | _ => return "other"

/-- Translate a Lean term to a symbolic expression; anything outside the coverage list becomes an atom. -/
partial def exprToSym (e : Expr) : SymM SymExpr := do
  if let some n := natLit? e then return .num n 1
  if e.isFVar then
    if let some (_, k) := (← get).bound.find? (·.1 == e) then return .bvar k
  let (f, args) := e.getAppFnArgs
  let tables := (← get).tables
  if let some entry := tables.function? f then
    if entry.arity ≥ 1 && args.size ≥ entry.arity then
      let operands := args.extract (args.size - entry.arity) args.size
      noteConditions entry operands
      if entry.arity == 1 then return .fn entry.sage (← exprToSym operands[0]!)
      return .call entry.sage (← operands.toList.mapM exprToSym)
  if let some c := tables.constant? f then
    if args.isEmpty then return .const c.sage
  if tables.isCoercion f && args.size ≥ 1 then
    let x := lastArg e
    let inner ← exprToSym x
    -- a compound ℕ or ℤ computation cast into a field keeps its type, so the rendering can restore the cast
    let compound := !(inner matches .atom _ | .bvar _ | .num _ _)
    let srcTy ← atomType x
    if compound && (srcTy == "ℕ" || srcTy == "ℤ") then return .typed srcTy inner
    return inner
  match f, args with
  | ``HAdd.hAdd, #[_, _, _, _, a, b] => return .add (← exprToSym a) (← exprToSym b)
  | ``HSub.hSub, #[_, _, _, _, a, b] => return .sub (← exprToSym a) (← exprToSym b)
  | ``HMul.hMul, #[ty, _, _, _, a, b] =>
    if ty.isAppOf `Matrix then return .method "__mul__" (← exprToSym a) [← exprToSym b]
    return .mul (← exprToSym a) (← exprToSym b)
  | ``HDiv.hDiv, #[_, _, _, _, a, b] =>
    if natLit? b |>.isNone then note b .ne
    return .div (← exprToSym a) (← exprToSym b)
  | ``Inv.inv, #[ty, _, a] =>
    if ty.isAppOf `Matrix then return .method "inverse" (← exprToSym a) []
    if natLit? a |>.isNone then note a .ne
    return .div (.num 1 1) (← exprToSym a)
  | ``Neg.neg, #[_, _, a] => return .neg (← exprToSym a)
  | ``HPow.hPow, #[α, β, _, _, a, b] =>
    -- a real exponent is `Real.rpow`: Lean's value for a negative base differs from Sage's
    if (← whnfR β).isConstOf `Real && (← whnfR α).isConstOf `Real then
      let positiveNumeral := match natLit? b with | some n => decide (n > 0) | none => false
      note a (if positiveNumeral then .nonneg else .pos)
    return .pow (← exprToSym a) (← exprToSym b)
  | ``HMod.hMod, #[_, _, _, _, a, b] => return .mod (← exprToSym a) (← exprToSym b)
  | `abs, #[_, _, _, a] => return .fn "abs" (← exprToSym a)
  | `Finset.sum, #[_, _, _, s, body] | `Finset.prod, #[_, _, _, s, body] =>
    let isSum := f == `Finset.sum
    let .lam k ty b bi := body | return ← symAtom e
    -- the inclusive bounds of the index set, or `none` for a set outside the coverage list
    let bounds? : Option (Expr × Option Expr × Bool) := match s.getAppFnArgs with
      | (`Finset.range, #[n]) => some (n, none, true)
      | (`Finset.Icc, #[_, _, _, lo, hi]) => some (lo, some hi, false)
      | (`Finset.Ico, #[_, _, _, lo, hi]) => some (lo, some hi, true)
      | (`Finset.univ, #[α, _]) => match α.getAppFnArgs with
        | (`Fin, #[n]) => some (n, none, true)
        | _ => none
      | _ => none
    let some (a, b?, exclusive) := bounds? | return ← symAtom e
    let taken := (← get).bound.map (·.2)
    let base := s!"{k.eraseMacroScopes}_"
    let kName := if taken.contains base then s!"{base}{taken.size}_" else base
    let a' ← exprToSym a
    let b'? ← b?.mapM exprToSym
    withLocalDecl k bi ty fun x => do
      modify fun st => { st with bound := st.bound.push (x, kName) }
      let body' ← exprToSym (b.instantiate1 x)
      modify fun st => { st with bound := st.bound.pop }
      match b'? with
      | none => return .rangeOp isSum kName a' body'
      | some hi => return .interval isSum kName a' (if exclusive then .sub hi (.num 1 1) else hi) body'
  | ``DFunLike.coe, #[_, _, _, _, F, arg] =>
    if F.isAppOf `Matrix.of then
      let some rows := vecList arg | return ← symAtom e
      let some rows := rows.mapM vecList | return ← symAtom e
      return .matrix (← rows.mapM (·.mapM exprToSym))
    if F.isAppOf `Polynomial.C then return ← exprToSym arg
    symAtom e
  | `Matrix.det, _ => return .method "det" (← exprToSym (lastArg e)) []
  | `Matrix.trace, _ => return .method "trace" (← exprToSym (lastArg e)) []
  | `Matrix.transpose, _ => return .method "transpose" (← exprToSym (lastArg e)) []
  | `Polynomial.X, _ => return .bvar "X"
  | `Polynomial.eval, #[_, _, x, p] => return .method "subs" (← exprToSym p) [.bvar s!"X={(← exprToSym x).toSage}"]
  | `Polynomial.coeff, #[_, _, p, n] => return .method "coefficient" (← exprToSym p) [.bvar "X", ← exprToSym n]
  | `Polynomial.natDegree, #[_, _, p] | `Polynomial.degree, #[_, _, p] =>
    return .method "degree" (← exprToSym p) [.bvar "X"]
  | _, _ => symAtom e

/-- The zero of a term's type. -/
private def zeroOf (e : Expr) : MetaM Expr := do
  mkAppOptM ``OfNat.ofNat #[← inferType e, mkRawNatLit 0, none]

/-- The proposition a condition asks for: `e ≠ 0`, `0 ≤ e`, `0 < e` or `e ≤ bound`. -/
def Condition.prop (c : Condition) : MetaM Expr := do
  match c.kind, c.bound with
  | .ne, some b => mkAppM ``Ne #[c.term, b]
  | .ne, none => mkAppM ``Ne #[c.term, ← zeroOf c.term]
  | .nonneg, _ => mkAppM ``LE.le #[← zeroOf c.term, c.term]
  | .pos, _ => mkAppM ``LT.lt #[← zeroOf c.term, c.term]
  | .le, some b => mkAppM ``LE.le #[c.term, b]
  | .le, none => throwError "veriphy: an `le` condition needs a bound"

/-- Forms of a hypothesis stronger than the condition that still discharge it. -/
private def strongerForms (c : Condition) : MetaM (List Expr) := do
  match c.kind, c.bound with
  | .ne, b => do
    let z ← match b with
      | some b => pure b
      | none => zeroOf c.term
    pure [← mkAppM ``LT.lt #[z, c.term], ← mkAppM ``LT.lt #[c.term, z]]
  | .nonneg, _ => pure [← mkAppM ``LT.lt #[← zeroOf c.term, c.term]]
  | .le, some b => pure [← mkAppM ``LT.lt #[c.term, b]]
  | _, _ => pure []

/-- Do two conditions ask for the same thing? -/
def Condition.same (c d : Condition) : MetaM Bool := do
  unless c.kind == d.kind do return false
  unless ← withReducible (isDefEq c.term d.term) do return false
  match c.bound, d.bound with
  | some a, some b => withReducible (isDefEq a b)
  | none, none => return true
  | _, _ => return false

/-- The nameable hypothesis that states a condition (or a stronger form of it), if any. -/
def Condition.dischargedBy (c : Condition) (nameable : LocalDecl → Bool) : MetaM (Option Name) := do
  let wanted ← c.prop
  let stronger ← strongerForms c
  for decl in ← getLCtx do
    unless nameable decl do continue
    let ty ← instantiateMVars decl.type
    for target in wanted :: stronger do
      if ← withReducible (isDefEq ty target) then return some decl.userName
  return none

end Veriphy
