/-
Veriphy bridge client: talks JSON-RPC to the Sage daemon (the `veriphy` Python package,
started as `sage -python -m veriphy.sage_server`).

The daemon is an UNTRUSTED oracle. This module only transports data; soundness
lives entirely in Lean, which checks every proof a script emits.

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

/-- The daemon process, with its stdin taken for writing. Its stderr is discarded: a reader blocked on it
would keep this Lean process from exiting while the daemon lives, and the daemon lives until Lean exits. -/
abbrev DaemonChild := IO.Process.Child { stdin := .null, stdout := .piped, stderr := .null }

/-- A running daemon serving every request of this Lean process. -/
structure Session where
  exe : String
  args : Array String
  stdin : IO.FS.Handle
  child : DaemonChild
  nextId : Nat := 1

/-- The session, guarded by a mutex: Lean elaborates declarations in parallel, the daemon answers one at a time. -/
initialize session : Std.Mutex (Option Session) ← Std.Mutex.new none

/-- The per-request time limit in seconds: `$VERIPHY_SAGE_TIMEOUT`, else 150 (above the scripts' own 120). -/
def requestTimeout : IO Nat := do
  return ((← IO.getEnv "VERIPHY_SAGE_TIMEOUT").bind String.toNat?).getD 150

/-- Start the daemon. -/
private def start (cfg : Config) : IO Session := do
  let (exe, args) ← cfg.resolve
  unless ← executableExists exe do
    throw <| IO.userError s!"veriphy: could not start Sage: '{exe}' is not an executable on PATH — \
      install SageMath, or set VERIPHY_SAGE_CMD to the sage executable"
  let child ← IO.Process.spawn { cmd := exe, args, stdin := .piped, stdout := .piped, stderr := .null }
  let (stdin, child) ← child.takeStdin
  return { exe, args, stdin, child }

/-- Why a fresh daemon gave no answer: rerun its command with no input and read what it printed. -/
private def diagnose (s : Session) : IO IO.Error := do
  let out ← IO.Process.output { cmd := s.exe, args := s.args, stdin := .null }
  return startupFailure s.exe (out.stderr ++ out.stdout)

/-- How an exchange with the daemon ended. -/
inductive Reply | line (text : String) | eof | timeout

/-- Send one request line and wait for one response line, up to `seconds`. The read blocks this thread; a
watchdog polling every 100 ms kills the daemon at the limit, and ends as soon as the answer arrives. -/
private def exchange (s : Session) (req : Json) (seconds : Nat) : IO Reply := do
  try
    s.stdin.putStr (req.compress ++ "\n")
    s.stdin.flush
  catch _ => return .eof
  let answered ← IO.mkRef false
  let timedOut ← IO.mkRef false
  let deadline := (← IO.monoMsNow) + seconds * 1000
  let watchdog ← IO.asTask (prio := .dedicated) do
    repeat
      if ← answered.get then break
      if (← IO.monoMsNow) ≥ deadline then
        timedOut.set true
        s.child.kill
        break
      IO.sleep 100
  let line ← try s.child.stdout.getLine catch _ => pure ""
  answered.set true
  let _ ← IO.wait watchdog
  if ← timedOut.get then return .timeout
  return if line.isEmpty then .eof else .line line

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
      set (none : Option Session)
      throw <| IO.userError s!"veriphy: the Sage request '{method}' exceeded {seconds}s; the daemon \
        was restarted (raise the limit with VERIPHY_SAGE_TIMEOUT)"
    | .eof =>
      set (none : Option Session)
      if retry && !fresh then return none
      throw (← diagnose s)
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

def field {α : Type} (j : Json) (k : String) (f : Json → Except String α) : Except String α := do
  f (← j.getObjVal? k)

/-! ## Proof scripts -/

/-- Run a proof script against a serialized problem; returns the Lean tactic block it built, its output, and whether
the block declared that it leaves goals open for the next tactic. -/
def run (problem : Json) (script : String) (cfg : Config := {}) : IO (String × String × Bool) :=
  call "run" (Json.mkObj [("problem", problem), ("script", Json.str script)]) (cfg := cfg) fun r => do
    let leaves := (r.getObjValAs? Bool "leaves_goals").toOption.getD false
    return (← field r "lean" (·.getStr?), ← field r "stdout" (·.getStr?), leaves)

/-- Run a test script against a claim's serialized problem; returns its instances (as the daemon encodes them), its
output, the seed it used and Sage's version. -/
def test (problem : Json) (script : String) (cfg : Config := {}) : IO (Array Json × String × Nat × String) :=
  call "test" (Json.mkObj [("problem", problem), ("script", Json.str script)]) (cfg := cfg) fun r => do
    return (← field r "instances" (·.getArr?), ← field r "stdout" (·.getStr?), ← field r "seed" (·.getNat?),
      ← field r "sage_version" (·.getStr?))

end Veriphy.Bridge
