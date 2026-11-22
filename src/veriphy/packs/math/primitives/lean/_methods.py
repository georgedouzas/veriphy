"""The `lean` pack's primitives as Python functions: `check` a file, `serialize` a claim, and `level` a module.

Each runs Lean once, as `lake env lean`, and keeps no process.
"""

import json
from pathlib import Path

from veriphy.core import ToolError, run_process
from veriphy.packs.math.primitives.lean._runner import TIMEOUT_S, lake, run_lean, toolchain

AXIOMS_MARKER = 'veriphy-axioms '
PROBLEM_MARKER = 'veriphy-problem '
# prepended to the source `check` runs; the appended script needs it, and line numbers are shifted back
PRELUDE = 'import Lean\n'
AXIOMS_SCRIPT = """

open Lean Elab Command in
#eval show CommandElabM Unit from do
  let env ← getEnv
  let names : Array Name := env.constants.foldStage2 (fun acc n info =>
    if !n.isInternal && (info matches .thmInfo _ || info matches .defnInfo _ || info matches .axiomInfo _) then
      acc.push n
    else acc) #[]
  let mut entries : List (String × Json) := []
  for n in names.qsort (·.toString < ·.toString) do
    let axioms ← collectAxioms n
    entries := entries ++ [(n.toString, Json.arr (axioms.map fun a => Json.str a.toString))]
  logInfo m!"veriphy-axioms {(Json.mkObj entries).compress}"
"""


def _tools(root: Path) -> list[dict[str, str]]:
    """Return the tools a Lean primitive ran: the workspace's Lean."""
    return [{'name': 'lean', 'version': toolchain(root), 'pin': 'version'}]


def _source(params: dict[str, object]) -> str:
    """Return the Lean text a request names: its `source`, or the content of its `file`."""
    if isinstance(params.get('source'), str):
        return str(params['source'])
    return Path(str(params['file'])).read_text()


def check(params: dict[str, object]) -> dict[str, object]:
    """Have Lean check a file, and report its errors, its warning count, and each declaration's axioms."""
    root = Path(str(params['root']))
    text = _source(params)
    shift = PRELUDE.count('\n')
    last = len(text.splitlines())
    try:
        code, error, messages = run_lean(root, PRELUDE + text + AXIOMS_SCRIPT)
    except ToolError as exc:
        return {'status': 'failed', 'error': str(exc)}
    if not messages and code != 0:
        return {'status': 'failed', 'error': error.strip()[-4000:]}
    axioms: dict[str, object] = {}
    errors: list[dict[str, object]] = []
    for message in messages:
        if message.text.startswith(AXIOMS_MARKER):
            axioms = json.loads(message.text.removeprefix(AXIOMS_MARKER))
        elif message.severity == 'error':
            errors.append({'line': message.line - shift, 'message': message.text})
    script = [str(e['message']) for e in errors if int(str(e['line'])) > last]
    if script:
        return {'status': 'failed', 'error': 'the axioms report did not run: ' + '\n'.join(script)}
    warnings = sum(1 for m in messages if m.severity == 'warning')
    status = 'refused' if errors else 'accepted'
    return {'status': status, 'errors': errors, 'warnings': warnings, 'axioms': axioms, 'tools': _tools(root)}


def serialize(params: dict[str, object]) -> dict[str, object]:
    """Return the problem of a claim of a file for the meaning check, with its statement."""
    root = Path(str(params['root']))
    declaration = str(params['declaration'])
    text = _source(params)
    last = len(text.splitlines())
    source = f'import Veriphy.Tactic.Meaning\n{text}\n\n#veriphy serialize {declaration}\n'
    try:
        _, error, messages = run_lean(root, source)
    except ToolError as exc:
        return {'status': 'failed', 'error': str(exc)}
    errors = [m for m in messages if m.severity == 'error']
    found = [m.text.removeprefix(PROBLEM_MARKER) for m in messages if m.text.startswith(PROBLEM_MARKER)]
    if errors or not found:
        where = 'the file does not elaborate' if any(m.line - 1 <= last for m in errors) else 'serializing failed'
        detail = '\n'.join(m.text for m in errors) or error.strip()[-4000:]
        return {'status': 'failed', 'error': f'{where}: {detail}'}
    return {'status': 'serialized', **json.loads(found[0]), 'tools': _tools(root)}


def level(params: dict[str, object]) -> dict[str, object]:
    """Build a module, then report the level `#veriphy levels` gives every declaration under the prefixes."""
    root = Path(str(params['root']))
    module = str(params['module'])
    raw = params.get('prefixes')
    prefixes = [str(p) for p in raw] if isinstance(raw, list) and raw else [module]
    try:
        built, out, err = run_process([lake(), 'build', module], root, TIMEOUT_S)
        if built != 0:
            return {'status': 'refused', 'error': (out + err).strip()[-4000:]}
        source = f'import {module}\nimport Veriphy.Tactic.Operation\n#veriphy levels {" ".join(prefixes)}\n'
        code, error, messages = run_lean(root, source)
    except ToolError as exc:
        return {'status': 'failed', 'error': str(exc)}
    errors = [m.text for m in messages if m.severity == 'error']
    if errors or (not messages and code != 0):
        return {'status': 'failed', 'error': '\n'.join(errors) or error.strip()[-4000:]}
    levels: dict[str, object] = {}
    for message in messages:
        for line in message.text.splitlines():
            name, sep, value = line.rpartition(': ')
            if sep:
                levels[name] = value
    return {'status': 'reported', 'levels': levels, 'tools': _tools(root)}
