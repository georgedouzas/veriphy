"""The Lean steps, `check` and `level`, and how a Lean step runs Lean on a generated file of the workspace."""

import json
from pathlib import Path

from veriphy.core import ToolError, canonical_json, content_digest, find_tool, project_dir, run_process
from veriphy.core._version import __version__
from veriphy.steps import Argument, Outcome, Params, Prepared, Step

TIMEOUT_S = 1800
AXIOMS_MARKER = 'veriphy-axioms '
# prepended to the copy `check` runs; the appended script needs it, and line numbers are shifted back
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


def _lake() -> str:
    """Return the path of `lake`, or fail naming what is missing."""
    return find_tool('lake', 'install Lean with elan (https://leanprover-community.github.io/get_started.html)')


def lean_sources(root: Path) -> str:
    """Return the content a Lean step's digest covers: every Lean file of the workspace, the toolchain and manifest.

    Hidden directories, which hold `.lake/` and Veriphy's own records, are skipped.

    Args:
        root: The workspace root.

    Returns:
        Canonical JSON naming each file with the digest of its content.
    """
    files = {
        str(path.relative_to(root)): content_digest(path.read_bytes())
        for path in sorted(root.rglob('*.lean'))
        if not any(part.startswith('.') for part in path.relative_to(root).parts)
    }
    for name in ('lean-toolchain', 'lake-manifest.json'):
        if (root / name).is_file():
            files[name] = content_digest((root / name).read_bytes())
    return canonical_json(files)


def toolchain(root: Path) -> str:
    """Return the workspace's Lean toolchain, as `lean-toolchain` names it."""
    path = root / 'lean-toolchain'
    return path.read_text().strip() if path.is_file() else 'unknown'


def _messages(stdout: str) -> list[dict[str, object]]:
    """Return the messages `lean --json` printed, one JSON object per line."""
    messages = []
    for line in stdout.splitlines():
        if line.startswith('{'):
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                messages.append(value)
    return messages


def run_lean(root: Path, source: str, name: str) -> tuple[int, str, list[dict[str, object]]]:
    """Run `lake env lean --json` on a generated file under `.veriphy/runs/tmp/`, and delete the file after.

    Returns the exit status, the error output and the messages.
    """
    directory = project_dir(root) / 'runs' / 'tmp'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{name}.lean'
    path.write_text(source)
    try:
        code, stdout, stderr = run_process([_lake(), 'env', 'lean', '--json', str(path)], root, TIMEOUT_S)
    finally:
        path.unlink(missing_ok=True)
    return code, stderr or stdout, _messages(stdout)


def message_text(message: dict[str, object]) -> str:
    """Return a message's text."""
    return str(message.get('data', ''))


def message_line(message: dict[str, object], shift: int) -> int:
    """Return a message's line in the original file."""
    pos = message.get('pos')
    line = pos.get('line', 0) if isinstance(pos, dict) else 0
    return int(line) - shift


def _prepare_check(root: Path, params: Params) -> Prepared:
    """Read the file and the workspace's Lean sources."""
    path = resolve(root, params['file'])
    return Prepared(
        {'file': path.read_bytes(), 'workspace': lean_sources(root)},
        {'file': str(path)},
        context=path,
    )


def _check(root: Path, _params: Params, prepared: Prepared) -> Outcome:
    """Have Lean check the file, and report its errors and the axioms of each declaration."""
    path = prepared.context if isinstance(prepared.context, Path) else Path()
    shift = PRELUDE.count('\n')
    text = path.read_text()
    last = len(text.splitlines())
    source = PRELUDE + text + AXIOMS_SCRIPT
    tools = {'lean': toolchain(root), 'veriphy': __version__}
    try:
        code, error, messages = run_lean(root, source, f'check-{content_digest(source)[:12]}')
    except ToolError as exc:
        return Outcome('failed', {'error': str(exc)}, tools)
    if not messages and code != 0:
        return Outcome('failed', {'error': error.strip()[-4000:]}, tools)
    axioms: dict[str, object] = {}
    errors = []
    for message in messages:
        text = message_text(message)
        if text.startswith(AXIOMS_MARKER):
            axioms = json.loads(text.removeprefix(AXIOMS_MARKER))
        elif message.get('severity') == 'error':
            errors.append({'line': message_line(message, shift), 'message': text})
    if any(int(str(e['line'])) > last for e in errors):
        script = [str(e['message']) for e in errors if int(str(e['line'])) > last]
        return Outcome('failed', {'error': 'the axioms report did not run: ' + '\n'.join(script)}, tools)
    warnings = sum(1 for m in messages if m.get('severity') == 'warning')
    outputs = {'errors': errors, 'warnings': warnings, 'axioms': axioms}
    return Outcome('refused' if errors else 'accepted', outputs, tools)


def _prepare_level(root: Path, params: Params) -> Prepared:
    """Read the module, the prefixes and the workspace's Lean sources."""
    module = str(params['module'])
    raw = params.get('prefixes')
    prefixes = [str(p) for p in raw] if isinstance(raw, list | tuple) and raw else [module]
    contents = {'workspace': lean_sources(root), 'module': module, 'prefixes': canonical_json(prefixes)}
    return Prepared(contents, {'module': module, 'prefixes': prefixes}, context=prefixes)


def _level(root: Path, params: Params, prepared: Prepared) -> Outcome:
    """Build the module, then report the level `#veriphy level` gives every declaration under the prefixes."""
    module = str(params['module'])
    prefixes = prepared.context if isinstance(prepared.context, list) else [module]
    tools = {'lean': toolchain(root), 'veriphy': __version__}
    try:
        built, out, err = run_process([_lake(), 'build', module], root, TIMEOUT_S)
        if built != 0:
            return Outcome('refused', {'error': (out + err).strip()[-4000:]}, tools)
        source = f'import {module}\nimport Veriphy.Tactic.Operation\n#veriphy level {" ".join(prefixes)}\n'
        code, error, messages = run_lean(root, source, f'level-{content_digest(source)[:12]}')
    except ToolError as exc:
        return Outcome('failed', {'error': str(exc)}, tools)
    errors = [message_text(m) for m in messages if m.get('severity') == 'error']
    if errors or (not messages and code != 0):
        return Outcome('failed', {'error': '\n'.join(errors) or error.strip()[-4000:]}, tools)
    levels: dict[str, object] = {}
    for message in messages:
        for line in message_text(message).splitlines():
            name, sep, level = line.rpartition(': ')
            if sep:
                levels[name] = level
    return Outcome('reported', {'levels': levels}, tools)


CHECK = Step(
    'check',
    'check',
    _prepare_check,
    _check,
    help='Lean checks a file, with each axiom set',
    arguments=(Argument('file'),),
)
LEVEL = Step(
    'level',
    'derived',
    _prepare_level,
    _level,
    help='the levels of a module, from #veriphy level',
    arguments=(
        Argument('module'),
        Argument('prefixes', 'a name prefix (default: the module)', option=True, flag='--prefix', many=True),
    ),
)


def resolve(root: Path, file: object) -> Path:
    """Return a file parameter as a path, relative ones taken from the workspace root."""
    path = Path(str(file))
    return path if path.is_absolute() else root / path
