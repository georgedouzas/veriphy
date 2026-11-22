"""Recompute the reliability of a scale from its items: Cronbach's alpha, with pingouin."""

import pandas as pd
import pingouin as pg


def cronbach_alpha(inputs: dict[str, object]) -> dict[str, object]:
    """Return Cronbach's alpha of the items of a scale, read from a CSV file, with its 95% confidence interval.

    Args:
        inputs: `data`, the CSV file, and `items`, the columns of the scale.

    Returns:
        The alpha, its confidence interval, and how many respondents answered every item.
    """
    data = pd.read_csv(str(inputs['data']))
    items = [str(item) for item in inputs['items']] if isinstance(inputs['items'], list) else []
    missing = [item for item in items if item not in data.columns]
    if missing:
        return {'status': 'failed', 'error': f"the data has no column {', '.join(missing)}"}
    answered = data[items].dropna()
    alpha, interval = pg.cronbach_alpha(data=answered)
    return {'status': 'reported', 'alpha': float(alpha), 'interval': [float(v) for v in interval], 'n': len(answered)}
