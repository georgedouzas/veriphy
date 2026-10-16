/-
Verification levels: how a claim was checked through Veriphy.

* `certificate`: a recipe built the proof. Its replacement runs inside `veriphy_certified`, which leaves the marker
  `Veriphy.certified` (the identity on proofs) in the proof term, so the level survives the replacement.
* `kernel-test` and `oracle-test`: `sage_test` checked the claim at instances, by the kernel or by Sage alone. The
  replacement carries the attribute `veriphy_tested` with the level and the instance counts.
* `none`: a proof Veriphy did not build or test.

`veriphy_instance% c v₁ … vₙ` is the claim `c` at the values, built from `c`'s statement and never from its proof, so
a tested instance cannot depend on the claim it tests. `#veriphy_levels p₁ …` lists the declarations under the
prefixes with their levels.
-/
import Lean

namespace Veriphy

open Lean Elab Meta Term Tactic Command

/-- Marks a proof built by a Veriphy recipe: the identity on proofs, kept in the proof term. -/
theorem certified {p : Prop} (h : p) : p := h

/-- `veriphy_certified tac` runs `tac` (a tactic, or a parenthesized sequence) under the marker `Veriphy.certified`,
recording that a recipe built the proof. -/
syntax (name := veriphyCertified) "veriphy_certified " tactic : tactic

elab_rules : tactic
  | `(tactic| veriphy_certified $tac) => withMainContext do
    let g ← getMainGoal
    let ty ← g.getType
    let h ← mkFreshExprSyntheticOpaqueMVar ty (← g.getTag)
    g.assign (mkApp2 (mkConst ``Veriphy.certified) ty h)
    replaceMainGoal [h.mvarId!]
    evalTactic tac

/-- A claim's level and instance counts, recorded by `sage_test`. -/
structure Tested where
  /-- `kernel-test` or `oracle-test`. -/
  level : String
  /-- The kernel-checked instances. -/
  kernel : Nat
  /-- The instances Sage alone evaluated. -/
  oracle : Nat
  deriving Inhabited, Repr

/-- `veriphy_tested kernel_test k o` (or `oracle_test`): the claim was tested at `k` kernel instances and `o` oracle
instances. -/
syntax (name := veriphyTested) "veriphy_tested " ident num num : attr

initialize testedAttr : ParametricAttribute Tested ←
  registerParametricAttribute {
    name := `veriphyTested
    descr := "a claim tested by sage_test, with its level and instance counts"
    getParam := fun _ stx => do
      match stx with
      | `(attr| veriphy_tested $level:ident $kernel:num $oracle:num) =>
        let text := match level.getId.toString with
          | "kernel_test" => some "kernel-test"
          | "oracle_test" => some "oracle-test"
          | _ => none
        let some text := text | throwError "veriphy_tested: the level is kernel_test or oracle_test"
        return { level := text, kernel := kernel.getNat, oracle := oracle.getNat }
      | _ => throwError "veriphy_tested: expected `veriphy_tested <kernel_test|oracle_test> <kernel> <oracle>`" }

/-- The statement of a claim: a theorem's type, or the value of a definition of type `Prop`, with fresh universe
levels. -/
def claimStatement (name : Name) : MetaM Expr := do
  let info ← getConstInfo name
  let levels ← info.levelParams.mapM fun _ => mkFreshLevelMVar
  match info with
  | .thmInfo _ | .axiomInfo _ => return info.instantiateTypeLevelParams levels
  | .defnInfo d =>
    unless (← whnf (d.type.instantiateLevelParams d.levelParams levels)).isProp do
      throwError "veriphy: `{name}` is a definition of type {d.type}, not of type `Prop`"
    return d.value.instantiateLevelParams d.levelParams levels
  | _ => throwError "veriphy: `{name}` is neither a theorem nor a definition of type `Prop`"

/-- `veriphy_instance% c v₁ … vₙ`: the claim `c` with its first universal binders instantiated at the values. -/
syntax (name := veriphyInstance) "veriphy_instance% " ident (ppSpace colGt term:max)* : term

@[term_elab veriphyInstance] def elabInstance : TermElab := fun stx _ => do
  match stx with
  | `(veriphy_instance% $c:ident $vs*) =>
    let name ← realizeGlobalConstNoOverloadWithInfo c
    let mut ty ← claimStatement name
    for v in vs do
      let ty' ← if ty.isForall then pure ty else whnf ty
      let .forallE _ dom body _ := ty'
        | throwError "veriphy_instance%: `{name}` has fewer universal binders than values"
      let value ← elabTermEnsuringType v dom
      ty := body.instantiate1 value
    synthesizeSyntheticMVarsNoPostponing
    instantiateMVars ty
  | _ => throwUnsupportedSyntax

/-- The level of a declaration: `certificate`, `kernel-test`, `oracle-test` or `none`. -/
def levelOf (env : Environment) (name : Name) : String :=
  match testedAttr.getParam? env name with
  | some t => t.level
  | none =>
    match env.find? name with
    | some (.thmInfo t) => if t.value.getUsedConstants.contains ``Veriphy.certified then "certificate" else "none"
    | _ => "none"

/-- `#veriphy_levels p₁ …`: each theorem (and tested proposition) under the prefixes, with its level. -/
syntax (name := veriphyLevels) "#veriphy_levels" (ppSpace ident)+ : command

elab_rules : command
  | `(#veriphy_levels $prefixes*) => do
    let env ← getEnv
    let roots := prefixes.map (·.getId)
    let names := env.constants.fold (init := #[]) fun acc name info =>
      if !name.isInternal && roots.any (·.isPrefixOf name) &&
          (info matches .thmInfo _ || (testedAttr.getParam? env name).isSome) then
        acc.push name
      else acc
    let lines := (names.qsort (·.toString < ·.toString)).map fun n => s!"{n}: {levelOf env n}"
    logInfo (if lines.isEmpty then "no theorems under the prefixes" else "\n".intercalate lines.toList)

end Veriphy
