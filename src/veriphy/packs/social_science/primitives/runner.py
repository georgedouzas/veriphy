"""Run an analysis script on its data, in a fresh Python process, and write its estimate as JSON.

`python runner.py <script> <data> <seed> <out> <variation>`, or `--version` for Python's version. The script defines
`run(data, inputs)`, which receives the data as a list of rows (each a mapping from column to value, numbers as floats)
and `inputs['variation']`, and returns a mapping with `estimate` and `se`.
"""

import csv
import json
import random
import runpy
import sys
from pathlib import Path


def _value(text: str) -> object:
    """Return a cell as a float when it reads as one, else as text."""
    try:
        return float(text)
    except ValueError:
        return text


def main() -> None:
    """Run the script's `run(data, inputs)` and write its estimate and standard error to the output file."""
    if sys.argv[1:] == ['--version']:
        sys.stdout.write(f'Python {sys.version.split()[0]}\n')
        return
    script, data, seed, out, variation = sys.argv[1:6]
    random.seed(int(seed))
    with Path(data).open(newline='') as handle:
        rows = [{key: _value(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    run = runpy.run_path(script)['run']
    result = run(rows, {'variation': Path(variation).read_text()})
    estimate = {'status': 'reported', 'estimate': float(result['estimate']), 'se': float(result['se'])}
    Path(out).write_text(json.dumps(estimate))


if __name__ == '__main__':
    main()
