"""Refit a published regression with linearmodels: ordinary least squares, instrumental variables, or a panel model.

The model is a formula in linearmodels' syntax. `y ~ 1 + x` is fitted by OLS, `y ~ 1 + x + [w ~ z]` by two-stage
least squares with `w` instrumented by `z`, and, given the entity and time columns, `y ~ x + EntityEffects` by
`PanelOLS`, with entity or time effects as the formula names them.
"""

import pandas as pd

COVARIANCES = ('unadjusted', 'robust', 'clustered')


def regression(inputs: dict[str, object]) -> dict[str, object]:
    """Refit a regression and return one coefficient's estimate and standard error.

    Args:
        inputs: `data`, a CSV file, `formula`, `coefficient`, the regressor to report, and optionally `entity` and
            `time`, the panel's columns, and `covariance`: `unadjusted` (by default), `robust`, or `clustered` (by
            entity).

    Returns:
        The estimate, its standard error and the number of observations, and the estimator that fitted them.
    """
    import linearmodels  # noqa: PLC0415 - the pack's optional library, imported only when the check runs
    from linearmodels.iv import IV2SLS  # noqa: PLC0415
    from linearmodels.panel import PanelOLS  # noqa: PLC0415

    data = pd.read_csv(str(inputs['data']))
    formula, name = str(inputs['formula']), str(inputs['coefficient'])
    covariance = str(inputs.get('covariance') or 'unadjusted')
    if covariance not in COVARIANCES:
        return {'status': 'failed', 'error': f"the covariance '{covariance}' is not one of {', '.join(COVARIANCES)}"}
    entity, time = str(inputs.get('entity') or ''), str(inputs.get('time') or '')
    missing = [c for c in (entity, time) if c and c not in data.columns]
    if missing:
        return {'status': 'failed', 'error': f"the data has no column '{missing[0]}': it has {', '.join(data.columns)}"}
    if entity and time:
        estimator = 'PanelOLS'
        clustered = {'cov_type': 'clustered', 'cluster_entity': True} if covariance == 'clustered' else {}
        model = PanelOLS.from_formula(formula, data.set_index([entity, time]))
        fitted = model.fit(**(clustered or {'cov_type': covariance}))
    elif covariance == 'clustered':
        return {'status': 'failed', 'error': 'clustered errors are by entity: name the entity and time columns'}
    else:
        estimator = 'IV2SLS' if '[' in formula else 'OLS'
        fitted = IV2SLS.from_formula(formula, data).fit(cov_type=covariance)
    if name not in fitted.params.index:
        error = f"the model has no coefficient '{name}': it has {', '.join(fitted.params.index)}"
        return {'status': 'failed', 'error': error}
    tools = [{'name': 'linearmodels', 'version': linearmodels.__version__, 'pin': 'version'}]
    return {
        'status': 'reported',
        'estimate': float(fitted.params[name]),
        'se': float(fitted.std_errors[name]),
        'n': int(fitted.nobs),
        'estimator': estimator,
        'tools': tools,
    }
