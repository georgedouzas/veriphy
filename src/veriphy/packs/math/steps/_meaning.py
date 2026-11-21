"""The `meaning` step: test whether a Lean statement says what it was meant to, at seeded values, as evidence."""

import json
from pathlib import Path

from veriphy.core import ToolError, content_digest
from veriphy.core._version import __version__
from veriphy.packs.lean.steps import lean_sources, message_line, message_text, resolve, run_lean, toolchain
from veriphy.steps import Argument, Outcome, Params, Prepared, Step

MEANING_MARKER = 'veriphy-meaning '
MEANING_VALUES = 10


def _prepare_meaning(root: Path, params: Params) -> Prepared:
    """Read the file, the declaration, the seed, the count or the points, the agent's reading and the Lean sources."""
    path = resolve(root, params['file'])
    declaration = str(params['declaration'])
    values = int(str(params.get('values') or MEANING_VALUES))
    points = params.get('points')
    informal = params.get('informal')
    if points is not None:
        json.loads(str(points))
    contents: dict[str, str | bytes] = {
        'file': path.read_bytes(),
        'workspace': lean_sources(root),
        'declaration': declaration,
        'values': str(values),
        'points': '' if points is None else str(points),
        'informal': '' if informal is None else str(informal),
    }
    sources: dict[str, object] = {'file': str(path), 'declaration': declaration}
    return Prepared(contents, sources, seed=int(str(params.get('seed') or 0)), context=path)


def _meaning(root: Path, params: Params, prepared: Prepared) -> Outcome:
    """Run `#veriphy_meaning` after the file, and record its outcome with the agent's reading of the statement."""
    path = prepared.context if isinstance(prepared.context, Path) else Path()
    declaration = str(params['declaration'])
    seed = prepared.seed or 0
    command = f'#veriphy_meaning {declaration} seed {seed} values {int(str(params.get("values") or MEANING_VALUES))}'
    if params.get('points') is not None:
        command += f' points {json.dumps(str(params["points"]))}'
    text = path.read_text()
    last = len(text.splitlines())
    source = f'import Veriphy.Tactic.Meaning\n{text}\n\nset_option veriphy.meaning.json true in\n{command}\n'
    tools = {'lean': toolchain(root), 'veriphy': __version__}
    try:
        _, error, messages = run_lean(root, source, f'meaning-{content_digest(source)[:12]}')
    except ToolError as exc:
        return Outcome('failed', {'error': str(exc)}, tools)
    errors = [
        {'line': message_line(m, 1), 'message': message_text(m)} for m in messages if m.get('severity') == 'error'
    ]
    found = [
        message_text(m).removeprefix(MEANING_MARKER) for m in messages if message_text(m).startswith(MEANING_MARKER)
    ]
    if errors or not found:
        where = (
            'the file does not elaborate' if any(int(str(e['line'])) <= last for e in errors) else 'the check failed'
        )
        detail = '\n'.join(str(e['message']) for e in errors) or error.strip()[-4000:]
        return Outcome('failed', {'error': f'{where}: {detail}'}, tools)
    result: dict[str, object] = json.loads(found[0])
    tools['sage'] = str(result.pop('sage_version', 'unknown'))
    informal = params.get('informal')
    outputs: dict[str, object] = {'declaration': declaration, 'informal': informal, **result}
    return Outcome(str(result.get('outcome', 'failed')), outputs, tools)


MEANING = Step(
    'meaning',
    'evidence',
    _prepare_meaning,
    _meaning,
    help='a statement tested at seeded values',
    arguments=(
        Argument('file', 'the Lean file that states the declaration'),
        Argument('declaration'),
        Argument('seed', option=True, type=int, default=0),
        Argument('values', 'how many values must agree (default 10)', option=True, type=int),
        Argument('points', 'values to evaluate at, as JSON: [{"x": "pi"}]', option=True),
        Argument('informal', "the agent's reading of the statement, kept in the record", option=True),
    ),
)
