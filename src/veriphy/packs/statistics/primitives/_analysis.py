"""The `statistics` pack's composites: `analysis.run` reproduces an analysis, `analysis.robustness` its variations.

Both record the data's SHA-256, and refuse data whose digest differs from the one the claim names, when it names one.
`analysis.run` runs the authors' script once; `analysis.robustness` runs it again under each declared variation.
"""

import hashlib
import tempfile
from collections.abc import Callable
from pathlib import Path

from veriphy.primitives import composite

Call = Callable[[str, dict[str, object]], dict[str, object]]
# |estimate / se| above it: significant at the 5% level, two-sided
SIGNIFICANT = 1.96
ANALYSIS = {
    'script': {'type': 'string', 'description': 'the analysis script, defining run(data, inputs)'},
    'data': {'type': 'string', 'description': 'the data, as CSV'},
    'sha256': {'type': 'string', 'description': "the data's SHA-256, as the claim names it, to refuse other data"},
    'seed': {'type': 'integer'},
}


def _data_digest(inputs: dict[str, object]) -> tuple[str, dict[str, object] | None]:
    """Return the data's SHA-256, and a refusal naming both digests when the claim names another, else `None`."""
    found = hashlib.sha256(Path(str(inputs['data'])).read_bytes()).hexdigest()
    expected = inputs.get('sha256')
    if expected is None or found == expected:
        return found, None
    message = f"the data {inputs['data']} has SHA-256 {found}, and the claim names {expected}: the analysis was not run"
    return found, {'status': 'refused', 'error': message, 'sha256': found, 'expected': expected}


def _estimate(inputs: dict[str, object], call: Call, variation: str, directory: Path) -> dict[str, object]:
    """Run the analysis once, the variation passed to it as a file, and return its estimate and standard error."""
    path = directory / f'variation-{len(list(directory.iterdir()))}.txt'
    path.write_text(variation)
    arguments: dict[str, object] = {key: inputs[key] for key in ('script', 'data') if key in inputs}
    return call('analysis.exec', {**arguments, 'variation': str(path), 'seed': inputs.get('seed', 0)})


@composite(
    'analysis.run',
    ('analysis.exec',),
    decides='analysis.exec',
    input_schema={'type': 'object', 'required': ['script', 'data'], 'properties': ANALYSIS},
    output_schema={'type': 'object', 'required': ['status']},
    pack='statistics',
)
def run(inputs: dict[str, object], call: Call) -> dict[str, object]:
    """Reproduce an analysis, recording the data's digest and refusing data the claim doesn't name.

    Args:
        inputs: The script, the data, the digest the claim names if any, and the seed.
        call: Calls a part.

    Returns:
        The estimate and its standard error, or the refusal.
    """
    found, refused = _data_digest(inputs)
    if refused is not None:
        return refused
    with tempfile.TemporaryDirectory(prefix='veriphy-r-') as tmp:
        result = _estimate(inputs, call, '', Path(tmp))
    return {'status': 'reported', 'estimate': result['estimate'], 'se': result['se'], 'sha256': found}


@composite(
    'analysis.robustness',
    ('analysis.exec',),
    decides='analysis.exec',
    input_schema={
        'type': 'object',
        'required': ['script', 'data', 'variations'],
        'properties': {**ANALYSIS, 'variations': {'type': 'array', 'items': {'type': 'string'}}},
    },
    output_schema={'type': 'object', 'required': ['status']},
    pack='statistics',
)
def robustness(inputs: dict[str, object], call: Call) -> dict[str, object]:
    """Run each declared variation, and call the estimate robust when its sign and significance hold under all.

    Args:
        inputs: The script, the data, the digest the claim names if any, the seed and the variations.
        call: Calls a part.

    Returns:
        `robust`, or `fragile` naming the variations that break it, with every estimate.
    """
    found, refused = _data_digest(inputs)
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
    outputs = {'estimate': base['estimate'], 'variations': estimates, 'breaking': breaking, 'sha256': found}
    return {'status': status, **outputs}
