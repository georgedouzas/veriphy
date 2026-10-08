/-
Veriphy bridge client: talks JSON-RPC to the Sage daemon (`sage_bridge/server.py`).

The daemon is an UNTRUSTED oracle. This module only transports data; soundness
lives entirely in the certificate checkers (`Veriphy/Tactic/*`), which must close
every goal through the kernel (`ring`, `positivity`, `norm_num`, ...).

STATUS: written against Lean v4.25.0 but not yet compiled (`lake build` pending
toolchain install). Expect minor API fixes on first build.
-/
import Lean.Data.Json

namespace Veriphy.Bridge

open Lean (Json)

structure Config where
  sageCmd : String := "sage"
  serverPath : String := "sage_bridge/server.py"
  deriving Repr

/-- A polynomial as a certificate-friendly term list: each term is a rational
coefficient (as a string, e.g. `"-3/2"`) and one exponent per variable. -/
structure Term where
  coeff : String
  exps : List Nat
  deriving Repr, Inhabited

/-- One irreducible factor with multiplicity. -/
structure Factor where
  terms : List Term
  mult : Nat
  deriving Repr, Inhabited

/-- A factorization certificate: `unit * ∏ factorᵢ ^ multᵢ`. -/
structure FactorCert where
  unit : String
  factors : List Factor
  deriving Repr, Inhabited

/-- Send one request to a freshly spawned daemon and read one response line.
A persistent daemon (kept warm across tactic calls) should replace this once
the tactics stabilize; the protocol is already line-oriented to allow it. -/
def request (cfg : Config := {}) (method : String) (params : Json := Json.null) :
    IO Json := do
  let child ← IO.Process.spawn {
    cmd := cfg.sageCmd
    args := #["-python", cfg.serverPath]
    stdin := .piped, stdout := .piped, stderr := .piped
  }
  let req := Json.mkObj
    [("id", Json.num 1), ("method", Json.str method), ("params", params)]
  let (stdin, child) ← child.takeStdin
  stdin.putStr (req.compress ++ "\n")
  stdin.flush
  let line ← child.stdout.getLine
  let json ← IO.ofExcept (Json.parse line)
  match json.getObjVal? "error" with
  | .ok (Json.str e) => throw <| IO.userError s!"sage daemon error: {e}"
  | _ => IO.ofExcept (json.getObjVal? "result")

private def parseTerm (j : Json) : Except String Term := do
  let coeff ← (← j.getObjVal? "coeff").getStr?
  let exps ← (← j.getObjVal? "exps").getArr?
  let exps ← exps.toList.mapM fun e => e.getNat?
  return { coeff, exps }

private def parseFactor (j : Json) : Except String Factor := do
  let terms ← (← j.getObjVal? "terms").getArr?
  let terms ← terms.toList.mapM parseTerm
  let mult ← (← j.getObjVal? "mult").getNat?
  return { terms, mult }

/-- Ask the daemon to factor `poly` (Sage/Python syntax) over `ℚ[vars]`. -/
def factor (poly : String) (vars : List String) (cfg : Config := {}) :
    IO FactorCert := do
  let params := Json.mkObj
    [ ("poly", Json.str poly)
    , ("vars", Json.arr (vars.toArray.map Json.str)) ]
  let result ← request cfg "factor" params
  IO.ofExcept do
    let unit ← (← result.getObjVal? "unit").getStr?
    let factors ← (← result.getObjVal? "factors").getArr?
    let factors ← factors.toList.mapM parseFactor
    return ({ unit, factors } : FactorCert)

end Veriphy.Bridge
