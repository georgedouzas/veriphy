"""Recompute survival statistics with lifelines: a Cox model's hazard ratio, and a Kaplan-Meier median survival.

The data is a CSV file with a row per subject: the time to the event or to censoring, and whether the event happened.
"""

import math

import pandas as pd


def _covariates(inputs: dict[str, object]) -> list[str]:
    """Return the model's covariates, as the step gives them."""
    given = inputs.get('covariates')
    return [str(c) for c in given] if isinstance(given, list) else []


def _read(inputs: dict[str, object]) -> pd.DataFrame | str:
    """Return the data, or why it can't be used, with the subjects of the group the claim is about."""
    data = pd.read_csv(str(inputs['data']))
    needed = [str(inputs['duration']), str(inputs['event']), *_covariates(inputs)]
    missing = [c for c in needed if c not in data.columns]
    if missing:
        return f"the data has no column '{missing[0]}': it has {', '.join(data.columns)}"
    group = str(inputs.get('group') or '')
    if group:
        column, _, value = group.partition('=')
        if column not in data.columns:
            return f"the data has no column '{column}': it has {', '.join(data.columns)}"
        data = data[data[column].astype(str) == value.strip()]
        if data.empty:
            return f"no subject has {column} = {value.strip()}"
    return data


def _tools() -> list[dict[str, str]]:
    """Return lifelines' version, as a record names it."""
    import lifelines  # noqa: PLC0415 - the pack's optional library, imported only when the check runs

    return [{'name': 'lifelines', 'version': lifelines.__version__, 'pin': 'version'}]


def hazard_ratio(inputs: dict[str, object]) -> dict[str, object]:
    """Fit a Cox proportional hazards model and return a covariate's hazard ratio with its 95% interval.

    Args:
        inputs: `data`, `duration` and `event`, their columns, `covariates`, the model's columns, and `covariate`,
            the one to report (the first by default).

    Returns:
        The hazard ratio, its 95% confidence interval, and the subjects and events counted.
    """
    from lifelines import CoxPHFitter  # noqa: PLC0415 - the pack's optional library, imported when the check runs

    data = _read(inputs)
    if isinstance(data, str):
        return {'status': 'failed', 'error': data}
    duration, event = str(inputs['duration']), str(inputs['event'])
    covariates = _covariates(inputs)
    covariate = str(inputs.get('covariate') or (covariates[0] if covariates else ''))
    if covariate not in covariates:
        return {'status': 'failed', 'error': f"the covariate '{covariate}' is not among the model's covariates"}
    fitted = CoxPHFitter().fit(data[[duration, event, *covariates]], duration_col=duration, event_col=event)
    low, high = (math.exp(float(v)) for v in fitted.confidence_intervals_.loc[covariate])
    return {
        'status': 'reported',
        'hazard_ratio': float(fitted.hazard_ratios_[covariate]),
        'ci': [low, high],
        'subjects': len(data),
        'events': int(data[event].sum()),
        'tools': _tools(),
    }


def median_survival(inputs: dict[str, object]) -> dict[str, object]:
    """Fit a Kaplan-Meier estimate and return its median survival time.

    Args:
        inputs: `data`, `duration` and `event`, their columns, and optionally `group`, as `arm=treatment`, the subjects
            the claim is about.

    Returns:
        The median survival time, and the subjects and events counted; `failed` when fewer than half had the event.
    """
    from lifelines import KaplanMeierFitter  # noqa: PLC0415 - the pack's optional library, imported when it runs

    data = _read(inputs)
    if isinstance(data, str):
        return {'status': 'failed', 'error': data}
    duration, event = str(inputs['duration']), str(inputs['event'])
    median = float(KaplanMeierFitter().fit(data[duration], data[event]).median_survival_time_)
    if math.isinf(median):
        return {'status': 'failed', 'error': 'fewer than half the subjects had the event: the median is not reached'}
    return {
        'status': 'reported',
        'median': median,
        'subjects': len(data),
        'events': int(data[event].sum()),
        'tools': _tools(),
    }
