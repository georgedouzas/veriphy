"""Does education raise social trust? An ordinary least squares regression on the survey, with statsmodels.

`run(data, inputs)` fits the formula, `trust_index ~ education_years` as published or a declared variation, and returns
the coefficient of its first regressor with its standard error.
"""

import pandas as pd
import statsmodels.formula.api as smf


def run(data: pd.DataFrame, inputs: dict[str, str]) -> dict[str, float]:
    """Fit the published model, or a variation of it, and return the first regressor's coefficient.

    Args:
        data: The survey.
        inputs: `variation`, a formula such as `trust_index ~ education_years + income`, empty as published.

    Returns:
        The coefficient and its standard error.
    """
    formula = inputs.get('variation', '').strip() or 'trust_index ~ education_years'
    fit = smf.ols(formula, data=data).fit()
    regressor = formula.split('~')[1].split('+')[0].strip()
    return {'estimate': float(fit.params[regressor]), 'se': float(fit.bse[regressor])}
