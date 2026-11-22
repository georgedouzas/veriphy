"""Run an analysis script on its data, in a fresh Python process, and write its estimate as JSON.

`python runner.py <script> <data> <seed> <out> <variation>`, or `--version` for Python's version. The script defines
`run(data, inputs)`, which receives the data as a pandas DataFrame read from the CSV, and `inputs['variation']`, the
model to fit instead of the published one (empty for the published one), and returns a mapping with `estimate` and
`se`. Python's and NumPy's random generators are seeded before the script runs.
"""

import json
import random
import runpy
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    """Run the script's `run(data, inputs)` and write its estimate and standard error to the output file."""
    if sys.argv[1:] == ['--version']:
        sys.stdout.write(f'Python {sys.version.split()[0]}\n')
        return
    script, data, seed, out, variation = sys.argv[1:6]
    random.seed(int(seed))
    np.random.seed(int(seed))
    run = runpy.run_path(script)['run']
    result = run(pd.read_csv(data), {'variation': Path(variation).read_text()})
    estimate = {'status': 'reported', 'estimate': float(result['estimate']), 'se': float(result['se'])}
    Path(out).write_text(json.dumps(estimate))


if __name__ == '__main__':
    main()
