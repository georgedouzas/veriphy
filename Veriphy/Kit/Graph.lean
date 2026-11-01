/-
`#veriphy_graph p₁ … pₙ`: the project's formalized claims for Veriphy's research claim graph. Each theorem and each
definition of type `Prop` under the prefixes is a claim, with the level `#veriphy_levels` reports and its statement;
each other definition is a definition; each declaration `uses` every other exported declaration its type or value
mentions. The export is N-Triples under `.veriphy/graph/lean/`, which `python -m veriphy.graph` reads with
provenance `lean`. With `veriphy.graph.write` off, the command prints the triples instead of writing them.
-/
import Veriphy.Kit.Levels
import Veriphy.Kit.Project

namespace Veriphy.Graph

open Lean Elab Command Meta

register_option veriphy.graph.write : Bool := {
  defValue := true
  descr := "write #veriphy_graph exports under .veriphy/graph/lean/ (off: print the triples)"
}

/-- A term of Veriphy's vocabulary, in N-Triples spelling. -/
def vocab (name : String) : String := s!"<urn:veriphy:vocabulary#{name}>"

/-- `rdf:type`, in N-Triples spelling. -/
def rdfType : String := "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"

/-- An upper-case two-digit hexadecimal byte. -/
private def hexByte (b : UInt8) : String :=
  let digit (n : Nat) : Char := (Nat.digitChar n).toUpper
  String.ofList [digit (b.toNat / 16), digit (b.toNat % 16)]

/-- Percent-encode a name, keeping ASCII letters, digits and `._-'~` (as Python's `quote` with `safe="._-'"`). -/
def encodeName (s : String) : String :=
  s.foldl (init := "") fun acc c =>
    if (c.isAlphanum && c.toNat < 128) || "._-'~".contains c then acc.push c
    else (String.singleton c).toUTF8.foldl (init := acc) fun a b => a ++ "%" ++ hexByte b

/-- The IRI of an exported declaration, in N-Triples spelling. -/
def leanIri (name : Name) : String := s!"<urn:veriphy:lean:{encodeName name.toString}>"

/-- A string literal in N-Triples spelling. -/
def literal (s : String) : String :=
  let body := s.foldl (init := "") fun acc c =>
    match c with
    | '"' => acc ++ "\\\""
    | '\\' => acc ++ "\\\\"
    | '\n' => acc ++ "\\n"
    | '\r' => acc ++ "\\r"
    | '\t' => acc ++ "\\t"
    | c => acc.push c
  "\"" ++ body ++ "\""

/-- Whether a constant is something the export describes: a theorem or a definition that is not generated. -/
private def exported (env : Environment) (name : Name) (info : ConstantInfo) : Bool :=
  !name.isInternalDetail && !isAuxRecursor env name && !isNoConfusion env name && !Meta.isMatcherCore env name &&
    (info matches .thmInfo _ || info matches .defnInfo _)

/-- Whether an exported constant is a claim: a theorem, or a definition whose type is `Prop`. -/
def isClaim (info : ConstantInfo) : Bool :=
  match info with
  | .thmInfo _ => true
  | .defnInfo d => d.type.isProp
  | _ => false

/-- The text of a claim's statement: a theorem's type, or a proposition's value. -/
private def statement (info : ConstantInfo) : MetaM String := do
  let e := match info with
    | .defnInfo d => if d.type.isProp then d.value else d.type
    | i => i.type
  return (← ppExpr e).pretty 100000

/-- The constants a declaration's type and value mention. -/
private def mentions (info : ConstantInfo) : Array Name :=
  let value := match info with
    | .thmInfo t => t.value.getUsedConstants
    | .defnInfo d => d.value.getUsedConstants
    | _ => #[]
  info.type.getUsedConstants ++ value

/-- The export's triples and its counts of claims, definitions and dependencies. -/
structure Export where
  lines : Array String := #[]
  claims : Nat := 0
  definitions : Nat := 0
  uses : Nat := 0

/-- The export of the declarations under the prefixes, or an error naming a prefix with no declaration. -/
def build (prefixes : Array Name) : MetaM Export := do
  let env ← getEnv
  let names := env.constants.fold (init := #[]) fun acc name info =>
    if prefixes.any (·.isPrefixOf name) && exported env name info then acc.push name else acc
  for p in prefixes do
    unless names.any (p.isPrefixOf ·) do throwError "no declarations start with {p}"
  let sorted := names.qsort (·.toString < ·.toString)
  let set := Std.HashSet.ofArray sorted
  let mut out : Export := {}
  for name in sorted do
    let some info := env.find? name | continue
    let iri := leanIri name
    let claim := isClaim info
    out := { out with lines := out.lines ++ #[
      s!"{iri} {rdfType} {vocab (if claim then "Claim" else "Definition")} .",
      s!"{iri} {vocab "leanName"} {literal name.toString} .",
      s!"{iri} {vocab "statement"} {literal (← statement info)} ."] }
    if claim then
      out := { out with claims := out.claims + 1,
                        lines := out.lines.push s!"{iri} {vocab "hasLevel"} {vocab (levelOf env name)} ." }
    else
      out := { out with definitions := out.definitions + 1 }
    let used := (mentions info).foldl (init := #[]) fun acc n =>
      if n != name && set.contains n && !acc.contains n then acc.push n else acc
    for n in used.qsort (·.toString < ·.toString) do
      out := { out with uses := out.uses + 1, lines := out.lines.push s!"{iri} {vocab "uses"} {leanIri n} ." }
  return out

/-- `#veriphy_graph p₁ … pₙ ["file.nt"]` exports the formalized claims under the prefixes; see the module doc. -/
syntax (name := veriphyGraph) "#veriphy_graph" (ppSpace ident)+ (ppSpace str)? : command

elab_rules : command
  | `(#veriphy_graph $ps* $[$out]?) => do
    let prefixes := ps.map (·.getId)
    let result ← liftTermElabM (build prefixes)
    let text := "\n".intercalate result.lines.toList ++ "\n"
    let summary := s!"{result.claims} claims, {result.definitions} definitions, {result.uses} dependencies"
    unless veriphy.graph.write.get (← getOptions) do
      logInfo m!"{summary}\n{text}"
      return
    let file ← match out with
      | some s => pure (System.FilePath.mk s.getString)
      | none => do
        let stem := "_".intercalate (prefixes.toList.map toString)
        pure ((← projectDir) / "graph" / "lean" / s!"{stem}.nt")
    if let some dir := file.parent then IO.FS.createDirAll dir
    IO.FS.writeFile file text
    logInfo m!"{summary} written to {file}"

end Veriphy.Graph
