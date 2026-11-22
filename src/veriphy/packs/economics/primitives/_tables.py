"""Recompute a statistic of a table's column with pandas: its mean, median or sum, or its growth over the rows."""

import pandas as pd

STATISTICS = ('mean', 'median', 'sum', 'growth', 'cagr')


def statistic(inputs: dict[str, object]) -> dict[str, object]:
    """Return a statistic of a column of a CSV file, in its rows' order.

    `growth` is the growth from the first row to the last, as a fraction; `cagr` is the compound annual growth rate
    over `periods` periods (the rows less one by default).

    Args:
        inputs: `data`, the CSV file, `column`, `statistic`, and `periods` for `cagr`.

    Returns:
        The value, and the number of rows it read.
    """
    data = pd.read_csv(str(inputs['data']))
    column, name = str(inputs['column']), str(inputs['statistic'])
    if column not in data.columns:
        return {'status': 'failed', 'error': f"the data has no column '{column}': it has {', '.join(data.columns)}"}
    if name not in STATISTICS:
        return {'status': 'failed', 'error': f"the statistic '{name}' is not one of {', '.join(STATISTICS)}"}
    values = data[column].dropna().astype(float)
    first, last = float(values.iloc[0]), float(values.iloc[-1])
    periods = int(str(inputs.get('periods') or len(values) - 1))
    found = {
        'mean': lambda: float(values.mean()),
        'median': lambda: float(values.median()),
        'sum': lambda: float(values.sum()),
        'growth': lambda: last / first - 1,
        'cagr': lambda: (last / first) ** (1 / periods) - 1,
    }[name]()
    return {'status': 'reported', 'value': found, 'rows': len(values)}
