/-
Veriphy bridge client: talks JSON-RPC to the Sage daemon (the `veriphy` Python package,
started as `sage -python -m veriphy.sage_server`).

The daemon is an UNTRUSTED oracle. This module only transports data; soundness
lives entirely in the certificate checkers (`Veriphy/Tactic/*`), which must close
every goal through the kernel (`ring`, `positivity`, `norm_num`, ...).

Every method is one `call`: a JSON request plus a decoder for its result. Tactics
reach the daemon through `Veriphy.Kit.call` (which refuses during replay), not
through this module directly.
-/
import Lean.Data.Json
import Std.Sync.Mutex

namespace Veriphy.Bridge

open Lean (Json)

structure Config where
  /-- The Sage executable; `$VERIPHY_SAGE_CMD` overrides it. -/
  sageCmd : String := "sage"
  /-- The daemon module, installed into Sage with `sage -pip install veriphy`. -/
  module : String := "veriphy.sage_server"
  deriving Repr

/-- The command line that starts the daemon: `<sage> -python -m veriphy.sage_server`, with
`$VERIPHY_SAGE_CMD` replacing `<sage>`, or `<sage> -python <script>` when `$VERIPHY_SAGE_SERVER`
names a development copy of the daemon. -/
def Config.resolve (cfg : Config) : IO (String × Array String) := do
  let exe := (← IO.getEnv "VERIPHY_SAGE_CMD").getD cfg.sageCmd
  match ← IO.getEnv "VERIPHY_SAGE_SERVER" with
  | some path =>
    unless ← System.FilePath.pathExists path do
      throw <| IO.userError s!"veriphy: VERIPHY_SAGE_SERVER points at '{path}', which does not \
        exist — fix the path, or unset VERIPHY_SAGE_SERVER to use the installed daemon \
        (`sage -pip install veriphy`)"
    return (exe, #["-python", path])
  | none => return (exe, #["-python", "-m", cfg.module])

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

/-- Why the daemon gave no answer, from its stderr: a missing package names the install command. -/
private def startupFailure (exe : String) (stderr : String) : IO.Error :=
  let err := (stderr.take 2000).trim
  if (stderr.splitOn "No module named 'veriphy'").length > 1 then
    IO.userError s!"veriphy: the daemon module is not installed in Sage ('{exe}'); run \
      `sage -pip install veriphy`"
  else
    IO.userError s!"veriphy: the Sage daemon exited before answering ('{exe}'):\n{err}"

/-- Is `exe` runnable: an existing path, or a name found on `$PATH`? -/
private def executableExists (exe : String) : IO Bool := do
  if exe.contains '/' then return ← System.FilePath.pathExists exe
  let dirs := ((← IO.getEnv "PATH").getD "").splitOn ":"
  dirs.anyM fun dir => System.FilePath.pathExists (System.FilePath.mk dir / exe)

/-- The daemon process, with its stdin taken for writing. -/
abbrev DaemonChild := IO.Process.Child { stdin := .null, stdout := .piped, stderr := .piped }

/-- A running daemon serving every request of this Lean process. -/
structure Session where
  exe : String
  stdin : IO.FS.Handle
  child : DaemonChild
  /-- The last few kilobytes the daemon wrote to stderr (drained in the background, so it never blocks). -/
  stderrTail : IO.Ref String
  nextId : Nat := 1

/-- The session, guarded by a mutex: Lean elaborates declarations in parallel, the daemon answers one at a time. -/
initialize session : Std.Mutex (Option Session) ← Std.Mutex.new none

/-- The per-request time limit in seconds: `$VERIPHY_SAGE_TIMEOUT`, else 150 (above the scripts' own 120). -/
def requestTimeout : IO Nat := do
  return ((← IO.getEnv "VERIPHY_SAGE_TIMEOUT").bind String.toNat?).getD 150

/-- Start the daemon and drain its stderr in the background. -/
private def start (cfg : Config) : IO Session := do
  let (exe, args) ← cfg.resolve
  unless ← executableExists exe do
    throw <| IO.userError s!"veriphy: could not start Sage: '{exe}' is not an executable on PATH — \
      install SageMath, or set VERIPHY_SAGE_CMD to the sage executable"
  let child ← IO.Process.spawn { cmd := exe, args, stdin := .piped, stdout := .piped, stderr := .piped }
  let (stdin, child) ← child.takeStdin
  let tail ← IO.mkRef ""
  let _ ← IO.asTask (prio := .dedicated) do
    repeat
      let line ← child.stderr.getLine
      if line.isEmpty then break
      tail.modify fun t => let all := t ++ line; (all.drop (all.length - 4000)).toString
  return { exe, stdin, child, stderrTail := tail }

/-- How an exchange with the daemon ended. -/
inductive Reply | line (text : String) | eof | timeout

/-- Send one request line and wait for one response line, up to `seconds`. -/
private def exchange (s : Session) (req : Json) (seconds : Nat) : IO Reply := do
  try
    s.stdin.putStr (req.compress ++ "\n")
    s.stdin.flush
  catch _ => return .eof
  let reader ← IO.asTask (prio := .dedicated) do
    let line ← s.child.stdout.getLine
    return if line.isEmpty then Reply.eof else Reply.line line
  let timer ← IO.asTask (prio := .dedicated) do
    IO.sleep (seconds * 1000).toUInt32
    return Reply.timeout
  match ← IO.waitAny [reader, timer] with
  | .ok reply => return reply
  | .error _ => return .eof

/-- Send one request to the daemon session and return its result. The session starts on first use, is
restarted once if it died, and is killed when a request exceeds the time limit. -/
def request (cfg : Config := {}) (method : String) (params : Json := Json.null) : IO Json := do
  let seconds ← requestTimeout
  -- one attempt: `none` means an already-running daemon had died, so the caller retries once on a fresh one
  let attempt (retry : Bool) : Std.AtomicT (Option Session) IO (Option String) := do
    let (s, fresh) ← match ← get with
      | some s => pure (s, false)
      | none => pure (← start cfg, true)
    let req := Json.mkObj [("id", Json.num s.nextId), ("method", Json.str method), ("params", params)]
    match ← exchange s req seconds with
    | .line text =>
      set (some { s with nextId := s.nextId + 1 })
      return some text
    | .timeout =>
      s.child.kill
      set (none : Option Session)
      throw <| IO.userError s!"veriphy: the Sage request '{method}' exceeded {seconds}s; the daemon \
        was restarted (raise the limit with VERIPHY_SAGE_TIMEOUT)"
    | .eof =>
      set (none : Option Session)
      if retry && !fresh then return none
      IO.sleep 200
      throw (startupFailure s.exe (← s.stderrTail.get))
  let answer ← session.atomically (m := IO) do
    match ← attempt true with
    | some text => pure text
    | none => match ← attempt false with
      | some text => pure text
      | none => throw <| IO.userError "veriphy: the Sage daemon died twice in a row"
  let .ok json := Json.parse answer
    | throw <| IO.userError s!"veriphy: the Sage daemon answered with something other than JSON:\n{answer}"
  match json.getObjVal? "error" with
  | .ok (Json.str e) => throw <| IO.userError s!"sage daemon error: {e}"
  | _ => IO.ofExcept (json.getObjVal? "result")

/-- One request, decoded: the shared path of every daemon method. -/
def call {α : Type} (method : String) (params : Json) (decode : Json → Except String α)
    (cfg : Config := {}) : IO α := do
  let result ← request cfg method params
  match decode result with
  | .ok a => pure a
  | .error e => throw <| IO.userError s!"veriphy: malformed '{method}' response from the daemon: {e}"

/-! ## Decoders -/

def strs (l : List String) : Json := Json.arr (l.toArray.map Json.str)

def field {α : Type} (j : Json) (k : String) (f : Json → Except String α) : Except String α := do
  f (← j.getObjVal? k)

def listOf {α : Type} (f : Json → Except String α) (j : Json) : Except String (List α) := do
  (← j.getArr?).toList.mapM f

def parseTerm (j : Json) : Except String Term := do
  return { coeff := ← field j "coeff" (·.getStr?), exps := ← field j "exps" (listOf (·.getNat?)) }

def parsePoly : Json → Except String (List Term) := listOf parseTerm

/-! ## Certificate methods -/

/-- Ask the daemon to factor `poly` (Sage/Python syntax) over `ℚ[vars]`. -/
def factor (poly : String) (vars : List String) (cfg : Config := {}) : IO FactorCert :=
  call "factor" (Json.mkObj [("poly", Json.str poly), ("vars", strs vars)]) (cfg := cfg) fun r => do
    let factors ← field r "factors" <| listOf fun j => do
      return ({ terms := ← field j "terms" parsePoly, mult := ← field j "mult" (·.getNat?) } : Factor)
    return { unit := ← field r "unit" (·.getStr?), factors }

/-- One square `coeff * q^2` of a sum-of-squares certificate. -/
structure Square where
  coeff : String
  terms : List Term
  deriving Repr, Inhabited

def parseSquare (j : Json) : Except String Square := do
  return { coeff := ← field j "coeff" (·.getStr?), terms := ← field j "terms" parsePoly }

/-- SOS certificate for `0 ≤ poly`: `poly = Σ coeffᵢ * qᵢ²`, all `coeffᵢ ≥ 0`. -/
def sos (poly : String) (vars : List String) (cfg : Config := {}) (hints : List String := []) :
    IO (List Square) :=
  call "sos" (Json.mkObj [("poly", Json.str poly), ("vars", strs vars), ("hints", strs hints)])
    (cfg := cfg) (field · "squares" (listOf parseSquare))

/-- Rational roots of a univariate polynomial over ℚ (as rational strings). -/
def roots (poly : String) (varName : String) (cfg : Config := {}) : IO (List String) :=
  call "roots" (Json.mkObj [("poly", Json.str poly), ("var", Json.str varName)]) (cfg := cfg)
    (field · "roots" (listOf (·.getStr?)))

/-- Ideal-membership certificate: cofactors `cᵢ` with `target = Σ cᵢ * hypᵢ`.
Fails (daemon error) when `target` is not in the ideal of the hypotheses. -/
def lincomb (target : String) (hyps : List String) (vars : List String)
    (cfg : Config := {}) : IO (List (List Term)) :=
  call "lincomb" (Json.mkObj [("target", Json.str target), ("hyps", strs hyps), ("vars", strs vars)])
    (cfg := cfg) (field · "cofactors" (listOf parsePoly))

/-- Closed form of `∑_{k=0}^{n-1} f(k)` as a polynomial in `n` (term list). -/
def sumClosedForm (summand : String) (cfg : Config := {}) : IO (List Term) :=
  call "sum" (Json.mkObj [("summand", Json.str summand)]) (cfg := cfg) (field · "closed_form" parsePoly)

/-- Linear Farkas certificate: multipliers `mᵢ` (rational strings), the constant `κ = Σ mᵢ pᵢ`, and
whether a strict hypothesis carries positive weight. -/
structure FarkasCert where
  multipliers : List String
  kappa : String
  strict : Bool
  deriving Repr, Inhabited

def farkas (polys rels vars : List String) (cfg : Config := {}) : IO FarkasCert :=
  call "farkas" (Json.mkObj [("polys", strs polys), ("rels", strs rels), ("vars", strs vars)])
    (cfg := cfg) fun r => do
      return { multipliers := ← field r "multipliers" (listOf (·.getStr?)),
               kappa := ← field r "kappa" (·.getStr?), strict := ← field r "strict" (·.getBool?) }

/-- Rational witness for a system of equations, linear inequalities and disequalities. -/
def exists_ (vars eqs les lts nes : List String) (cfg : Config := {}) : IO (List String) :=
  call "exists" (Json.mkObj
      [("vars", strs vars), ("eqs", strs eqs), ("les", strs les), ("lts", strs lts), ("nes", strs nes)])
    (cfg := cfg) (field · "point" (listOf (·.getStr?)))

/-! ## Agent certificates -/

/-- One named weight or cofactor (a polynomial) on a hypothesis. -/
structure Weighted where
  name : String
  poly : List Term
  deriving Repr, Inhabited

/-- A validated `certify` result; which fields are set depends on the family. -/
structure AgentCert where
  /-- identity: cofactors; inequality: hypothesis weights. -/
  weights : List Weighted := []
  /-- inequality: `coeff * q²` terms. -/
  squares : List Square := []
  /-- inequality refuting `False`: the constant `κ` and whether a strict hypothesis is used. -/
  kappa : Option String := none
  strict : Bool := false
  /-- witness: one rational per binder. -/
  point : List String := []
  deriving Repr, Inhabited

/-- Run an agent-written Sage `script` against a serialized problem and return its certificate,
validated against `family`'s schema (`identity`, `inequality`, `witness`). -/
def certify (problem : Json) (family script : String) (cfg : Config := {}) : IO AgentCert :=
  call "certify" (Json.mkObj
      [("problem", problem), ("family", Json.str family), ("script", Json.str script)]) (cfg := cfg)
    fun r => do
      let weighted (k : String) : Except String (List Weighted) :=
        match r.getObjVal? k with
        | .ok j => listOf (fun j => do
            return { name := ← field j "name" (·.getStr?), poly := ← field j "poly" parsePoly }) j
        | .error _ => pure []
      let opt {α} (k : String) (f : Json → Except String α) : Except String (Option α) :=
        match r.getObjVal? k with | .ok j => some <$> f j | .error _ => pure none
      return { weights := (← weighted "cofactors") ++ (← weighted "weights"),
               squares := (← opt "squares" (listOf parseSquare)).getD [],
               kappa := ← opt "kappa" (·.getStr?),
               strict := (← opt "strict" (·.getBool?)).getD false,
               point := (← opt "point" (listOf (·.getStr?))).getD [] }

/-! ## Proof scripts -/

/-- Run a proof script against a serialized problem; returns the Lean tactic block it built and its output. -/
def run (problem : Json) (script : String) (cfg : Config := {}) : IO (String × String) :=
  call "run" (Json.mkObj [("problem", problem), ("script", Json.str script)]) (cfg := cfg) fun r => do
    return (← field r "lean" (·.getStr?), ← field r "stdout" (·.getStr?))

end Veriphy.Bridge
