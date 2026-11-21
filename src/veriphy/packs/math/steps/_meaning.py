"""The `meaning` step: test whether a Lean statement says what it was meant to, at seeded values, as evidence."""

import json
from pathlib import Path

from veriphy.packs.lean.steps import lean_sources, resolve
from veriphy.steps import Argument, Outcome, Params, Prepared, Step, call_primitive

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
    """Test the statement at seeded values (`meaning`), and record the outcome with the agent's reading of it."""
    path = prepared.context if isinstance(prepared.context, Path) else Path()
    inputs: dict[str, object] = {
        'root': str(root),
        'file': str(path),
        'declaration': str(params['declaration']),
        'seed': prepared.seed or 0,
        'values': int(str(params.get('values') or MEANING_VALUES)),
    }
    if params.get('points') is not None:
        inputs['points'] = json.loads(str(params['points']))
    outcome = call_primitive(root, 'meaning', inputs, status='outcome')
    outputs = {'declaration': str(params['declaration']), 'informal': params.get('informal'), **outcome.outputs}
    outputs.pop('sage_version', None)
    outputs.pop('statement', None)
    return Outcome(outcome.status, outputs, outcome.tools)


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
