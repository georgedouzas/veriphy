"""Does education raise social trust? An ordinary least squares regression on the survey, written in plain Python.

`run(data, inputs)` regresses the outcome on the regressors of a formula and returns the coefficient of the first
regressor, with its standard error: `trust_index ~ education_years` as published, another formula as a variation.
"""

import math


def _solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Solve a small linear system by Gauss-Jordan elimination with partial pivoting."""
    size = len(vector)
    rows = [[*matrix[i], vector[i]] for i in range(size)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda r: abs(rows[r][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]
        for r in range(size):
            if r != col:
                factor = rows[r][col] / rows[col][col]
                rows[r] = [a - factor * b for a, b in zip(rows[r], rows[col], strict=True)]
    return [rows[i][size] / rows[i][i] for i in range(size)]


def run(data: list[dict[str, object]], inputs: dict[str, str]) -> dict[str, float]:
    """Regress the outcome on the formula's regressors, and return the first regressor's coefficient.

    Args:
        data: The rows of the survey.
        inputs: `variation`, a formula such as `trust_index ~ education_years + income`, empty as published.

    Returns:
        The coefficient of the first regressor, and its standard error.
    """
    formula = inputs.get('variation', '').strip() or 'trust_index ~ education_years'
    outcome, right = (side.strip() for side in formula.split('~'))
    regressors = [name.strip() for name in right.split('+')]
    x = [[1.0, *(float(str(row[name])) for name in regressors)] for row in data]
    y = [float(str(row[outcome])) for row in data]
    k, n = len(x[0]), len(y)
    xtx = [[sum(r[i] * r[j] for r in x) for j in range(k)] for i in range(k)]
    beta = _solve(xtx, [sum(r[i] * v for r, v in zip(x, y, strict=True)) for i in range(k)])
    residuals = [v - sum(b * c for b, c in zip(beta, r, strict=True)) for r, v in zip(x, y, strict=True)]
    variance = sum(e * e for e in residuals) / (n - k)
    unit = [1.0 if i == 1 else 0.0 for i in range(k)]
    return {'estimate': beta[1], 'se': math.sqrt(variance * _solve(xtx, unit)[1])}
