"""The `math` pack's composites: `meaning` (Lean serializes, Sage samples), `certify` (Sage searches, Lean decides)."""

from collections.abc import Callable
from pathlib import Path

from veriphy.primitives import composite

Call = Callable[[str, dict[str, object]], dict[str, object]]
CLAIM = {
    'root': {'type': 'string'},
    'file': {'type': 'string'},
    'source': {'type': 'string'},
    'declaration': {'type': 'string'},
}
FAILED = {'status': {'const': 'failed'}, 'error': {'type': 'string'}}


def _claim(inputs: dict[str, object]) -> dict[str, object]:
    """Return the part of an input that names a claim: its workspace, its file or source, and its declaration."""
    return {key: inputs[key] for key in ('root', 'file', 'source', 'declaration') if key in inputs}


@composite(
    'meaning',
    ('lean.serialize', 'sage.sample'),
    input_schema={
        'type': 'object',
        'required': ['root', 'declaration'],
        'properties': {**CLAIM, 'seed': {'type': 'integer'}, 'values': {'type': 'integer'}, 'points': {}},
        'anyOf': [{'required': ['file']}, {'required': ['source']}],
    },
    output_schema={
        'type': 'object',
        'required': ['outcome'],
        'properties': {'outcome': {'enum': ['agrees', 'counterexample', 'undecided', 'failed']}},
    },
    pack='math',
)
def meaning(inputs: dict[str, object], call: Call) -> dict[str, object]:
    """Test whether a claim's statement says what it was meant to: Lean serializes it, Sage samples it.

    Args:
        inputs: The claim, and the seed, the count of values and the given points.
        call: Calls a part.

    Returns:
        Sage's outcome, with the declaration and its statement.
    """
    claim = call('lean.serialize', _claim(inputs))
    if claim.get('status') == 'failed':
        return {'outcome': 'failed', 'error': claim.get('error', '')}
    sample: dict[str, object] = {key: inputs[key] for key in ('seed', 'values', 'points') if key in inputs}
    result = call('sage.sample', {'problem': claim['problem'], **sample})
    result.pop('tools', None)
    return {**result, 'declaration': claim['declaration'], 'statement': claim['statement']}


def _check_source(text: str, claim: dict[str, object], tactic: str) -> str:
    """Return the file with an `example` that proves the claim by the candidate tactic block, after its intros."""
    declaration = str(claim['declaration'])
    problem = claim.get('problem')
    names = problem.get('intros', []) if isinstance(problem, dict) else []
    target = f'type_of% @{declaration}' if claim.get('kind') == 'theorem' else declaration
    lines = [f'example : {target} := by']
    if claim.get('kind') != 'theorem':
        lines.append(f'  unfold {declaration}')
    if names:
        lines.append('  intro ' + ' '.join(str(n) for n in names))
    lines += ['  ' + line for line in tactic.splitlines()]
    return text.rstrip() + '\n\n' + '\n'.join(lines) + '\n'


@composite(
    'certify',
    ('lean.serialize', 'sage.search', 'lean.check'),
    decides='lean.check',
    input_schema={
        'type': 'object',
        'required': ['root', 'declaration', 'script'],
        'properties': {**CLAIM, 'script': {'type': 'string'}},
        'anyOf': [{'required': ['file']}, {'required': ['source']}],
    },
    output_schema={
        'type': 'object',
        'required': ['status'],
        'properties': {'status': {'enum': ['certified', 'refused', 'failed']}, 'lean': {'type': 'string'}},
    },
    pack='math',
)
def certify(inputs: dict[str, object], call: Call) -> dict[str, object]:
    """Certify a claim: Sage's script finds a candidate proof, and Lean's check of it decides.

    Args:
        inputs: The claim and the script.
        call: Calls a part.

    Returns:
        `certified` with the proof when Lean accepts it on the standard axioms, else `refused` with Lean's errors.
    """
    claim = call('lean.serialize', _claim(inputs))
    if claim.get('status') == 'failed':
        return {'status': 'failed', 'error': claim.get('error', '')}
    candidate = call('sage.search', {'problem': claim['problem'], 'script': inputs['script']})
    text = str(inputs['source']) if 'source' in inputs else Path(str(inputs['file'])).read_text()
    lean = str(candidate['lean'])
    checked = call('lean.check', {'root': inputs['root'], 'source': _check_source(text, claim, lean)})
    if checked.get('status') != 'accepted':
        return {
            'status': 'refused',
            'lean': lean,
            'errors': checked.get('errors', []),
            'error': checked.get('error', ''),
        }
    return {'status': 'certified', 'lean': lean, 'axioms': checked.get('axioms', {})}
