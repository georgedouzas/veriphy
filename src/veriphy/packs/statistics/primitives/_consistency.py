"""Check that reported statistics are consistent with each other.

`p_value` recomputes the p-value of a reported test statistic with SciPy's distributions, as statcheck does: a t, F,
χ², z or correlation test, at the statistic as reported and at the ends of its rounding, and says whether the reported
p-value lies among them. `grim` applies the GRIM test: whether a mean reported for integer data is possible for its
sample size.
"""

import math

from scipy import stats

TESTS = ('t', 'F', 'chi2', 'z', 'r')


def p_of(test: str, statistic: float, df: tuple[float, ...], tails: int = 2) -> float:
    """Return the p-value of a test statistic.

    Args:
        test: `t`, `F`, `chi2`, `z` or `r`.
        statistic: The statistic.
        df: Its degrees of freedom: one for t, χ² and r, two for F, none for z.
        tails: 2 for a two-sided t, z or r test, 1 for a one-sided one; F and χ² tests are upper-tailed.

    Returns:
        The p-value.

    Examples:
        >>> round(p_of('t', 2.2, (28,)), 4), round(p_of('z', 1.96, ()), 4), round(p_of('chi2', 3.84, (1,)), 3)
        (0.0362, 0.05, 0.05)
    """
    if test == 'F':
        return float(stats.f.sf(statistic, *df))
    if test == 'chi2':
        return float(stats.chi2.sf(statistic, *df))
    if test == 'z':
        return float(stats.norm.sf(abs(statistic)) * tails)
    if test == 'r':
        (n,) = df
        statistic = statistic * math.sqrt(n / (1 - statistic**2))
    return float(stats.t.sf(abs(statistic), *df) * tails)


def _half_unit(text: str) -> float:
    """Return half a unit in the last digit a number was reported with."""
    decimals = len(text.split('.', 1)[1]) if '.' in text else 0
    return 0.5 * 10.0**-decimals


def p_value(inputs: dict[str, object]) -> dict[str, object]:
    """Recompute a reported p-value from its test statistic, allowing for the rounding of both.

    Args:
        inputs: `test` (t, F, chi2, z or r), `statistic` and `df` as reported text (`df` as `d1,d2` for F),
            `claimed`, the reported p-value as text (`<.001` for a bound), and `tails`, 2 by default.

    Returns:
        `agrees` when the reported p-value is within the range the statistic's rounding allows, `differs` otherwise,
        with the recomputed p-value and the range.
    """
    test = str(inputs['test'])
    if test not in TESTS:
        return {'status': 'failed', 'error': f"the test '{test}' is not one of {', '.join(TESTS)}"}
    text = str(inputs['statistic'])
    statistic = float(text)
    df = tuple(float(d) for d in str(inputs.get('df') or '').split(',') if d.strip())
    tails = int(str(inputs.get('tails', 2)))
    half = _half_unit(text)
    ends = [p_of(test, value, df, tails) for value in (statistic - half, statistic + half)]
    low, high = min(ends), max(ends)
    reported = str(inputs['claimed'])
    claimed_text = reported.lstrip('<=').strip()
    claimed = float(claimed_text)
    tolerance = _half_unit(claimed_text)
    agrees = low < claimed if reported.startswith('<') else low - tolerance <= claimed <= high + tolerance
    recomputed = p_of(test, statistic, df, tails)
    return {
        'status': 'agrees' if agrees else 'differs',
        'p': recomputed,
        'range': [low, high],
        'compared': {'field': 'p', 'found': round(recomputed, 6), 'claimed': claimed, 'tolerance': tolerance},
    }


def grim(inputs: dict[str, object]) -> dict[str, object]:
    """Apply the GRIM test: whether a mean, reported for integer data, is possible for its sample size.

    Args:
        inputs: `mean`, as reported text, `n`, the sample size, and `items`, the number of integer items averaged
            per respondent, 1 by default.

    Returns:
        `agrees` when some integer total gives the reported mean, `differs` otherwise, with the nearest possible means.

    Examples:
        >>> grim({'mean': '5.19', 'n': 28})['status'], grim({'mean': '5.18', 'n': 28})['status']
        ('differs', 'agrees')
    """
    text = str(inputs['mean'])
    decimals = len(text.split('.', 1)[1]) if '.' in text else 0
    mean, count = float(text), int(str(inputs['n'])) * int(str(inputs.get('items', 1)))
    totals = (round(mean * count) - 1, round(mean * count), round(mean * count) + 1)
    means = [round(total / count, decimals) for total in totals]
    possible = any(math.isclose(m, mean, abs_tol=1e-12) for m in means)
    return {
        'status': 'agrees' if possible else 'differs',
        'nearest': sorted(set(means)),
        'compared': {'field': 'mean', 'found': sorted(set(means)), 'claimed': mean, 'tolerance': 0},
    }
