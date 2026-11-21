"""The `reproduction` pack's composites: `r.run` reproduces an analysis, `r.robustness` runs its variations.

`r.run` checks the data's digest, then runs the analysis in the pinned R image; `r.robustness` runs it again under
each declared variation.
"""

import hashlib
import tempfile
from collections.abc import Callable
from pathlib import Path

from veriphy.primitives import composite

Call = Callable[[str, dict[str, object]], dict[str, object]]
RUNNER = Path(__file__).resolve().parent / 'runner.R'
# |estimate / se| above it: significant at the 5% level, two-sided
SIGNIFICANT = 1.96
ANALYSIS = {
    'script': {'type': 'string', 'description': 'the analysis script, defining run(data, inputs)'},
    'data': {'type': 'string', 'description': 'the data, as CSV'},
    'sha256': {'type': 'string', 'description': "the data's SHA-256, as the claim names it"},
    'seed': {'type': 'integer'},
}


def _digest_problem(inputs: dict[str, object]) -> dict[str, object] | None:
    """Return a refusal naming both digests when the data is not the data the claim names, else `None`."""
    found = hashlib.sha256(Path(str(inputs['data'])).read_bytes()).hexdigest()
    if found == inputs['sha256']:
        return None
    message = f"the data {inputs['data']} has SHA-256 {found}, and the claim names {inputs['sha256']}: R was not run"
    return {'status': 'refused', 'error': message, 'found': found, 'expected': inputs['sha256']}


def _estimate(inputs: dict[str, object], call: Call, variation: str, directory: Path) -> dict[str, object]:
    """Run the analysis once, the variation passed to it as a file, and return its estimate and standard error."""
    path = directory / f'variation-{len(list(directory.iterdir()))}.txt'
    path.write_text(variation)
    arguments: dict[str, object] = {key: inputs[key] for key in ('script', 'data') if key in inputs}
    return call('r.exec', {**arguments, 'runner': str(RUNNER), 'variation': str(path), 'seed': inputs.get('seed', 0)})


@composite(
    'r.run',
    ('r.exec',),
    decides='r.exec',
    input_schema={'type': 'object', 'required': ['script', 'data', 'sha256'], 'properties': ANALYSIS},
    output_schema={'type': 'object', 'required': ['status']},
    pack='reproduction',
)
def run(inputs: dict[str, object], call: Call) -> dict[str, object]:
    """Reproduce an analysis: refuse data whose digest differs from the claim's, then run it in the pinned image.

    Args:
        inputs: The script, the data, its digest and the seed.
        call: Calls a part.

    Returns:
        The estimate and its standard error, or the refusal.
    """
    refused = _digest_problem(inputs)
    if refused is not None:
        return refused
    with tempfile.TemporaryDirectory(prefix='veriphy-r-') as tmp:
        result = _estimate(inputs, call, '', Path(tmp))
    return {'status': 'reported', 'estimate': result['estimate'], 'se': result['se']}


@composite(
    'r.robustness',
    ('r.exec',),
    decides='r.exec',
    input_schema={
        'type': 'object',
        'required': ['script', 'data', 'sha256', 'variations'],
        'properties': {**ANALYSIS, 'variations': {'type': 'array', 'items': {'type': 'string'}}},
    },
    output_schema={'type': 'object', 'required': ['status']},
    pack='reproduction',
)
def robustness(inputs: dict[str, object], call: Call) -> dict[str, object]:
    """Run each declared variation, and call the estimate robust when its sign and significance hold under all.

    Args:
        inputs: The script, the data, its digest, the seed and the variations.
        call: Calls a part.

    Returns:
        `robust`, or `fragile` naming the variations that break it, with every estimate.
    """
    refused = _digest_problem(inputs)
    if refused is not None:
        return refused
    variations = inputs['variations'] if isinstance(inputs['variations'], list) else []
    with tempfile.TemporaryDirectory(prefix='veriphy-r-') as tmp:
        base = _estimate(inputs, call, '', Path(tmp))
        runs = {str(v): _estimate(inputs, call, str(v), Path(tmp)) for v in variations}
    sign = float(str(base['estimate'])) > 0

    def holds(result: dict[str, object]) -> bool:
        """Return whether an estimate keeps the base's sign and stays significant."""
        estimate, se = float(str(result['estimate'])), float(str(result['se']))
        return (estimate > 0) == sign and abs(estimate / se) > SIGNIFICANT

    estimates = {v: {'estimate': r['estimate'], 'se': r['se'], 'holds': holds(r)} for v, r in runs.items()}
    breaking = [v for v, r in estimates.items() if not r['holds']]
    status = 'robust' if holds(base) and not breaking else 'fragile'
    return {'status': status, 'estimate': base['estimate'], 'variations': estimates, 'breaking': breaking}
