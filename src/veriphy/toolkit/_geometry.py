"""Coordinate geometry with SageManifolds: components computed in Sage, proved against the `CoordinateGeometry` asset.

A metric is given by its components, Sage expressions in coordinates `x0, x1, …`. SageManifolds computes Christoffel
symbols and curvature; Lean proves each requested component from the definitions in
`VeriphyAssets.CoordinateGeometry`: the inverse metric as a matrix identity (its determinant nonzero by hypotheses in
the context), the partial derivatives by `simp` with derivative lemmas, and `field_simp` and `ring` to close.
"""

from collections.abc import Sequence

from sage.all import SR, Manifold, matrix, var
from sage.matrix.matrix0 import Matrix

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic
from veriphy.toolkit._problem import read_problem
from veriphy.toolkit._symbolic_emit import symbolic

DERIVATIVE_SIMP = (
    'Fin.sum_univ_succ, Function.update_apply, deriv_fun_pow, deriv_fun_mul, deriv_fun_add, deriv_fun_sub, '
    'Real.deriv_sin, Real.deriv_cos, Real.deriv_exp'
)


def coordinates(n: int) -> list[object]:
    """Return the Sage coordinates `x0, …` of an `n`-dimensional chart.

    Args:
        n: The dimension.

    Returns:
        The symbols.
    """
    return [var(f'x{i}') for i in range(n)]


def _render(e: object, n: int) -> str:
    """Return an expression in the coordinates as Lean text in `x 0, x 1, …`."""
    problem = read_problem(
        {
            'vars': [f'x{i}' for i in range(n)],
            'atoms': [f'x {i}' for i in range(n)],
            'atom_types': ['ℝ'] * n,
            'goal': {'kind': 'false'},
        },
    )
    text = str(symbolic(SR(e), problem, lean_type='ℝ'))
    return text


def metric_term(g: Matrix) -> str:
    """Return a metric's components as a Lean `Fin n → Fin n → (Fin n → ℝ) → ℝ`.

    Args:
        g: The metric's matrix of expressions in the coordinates.

    Returns:
        The term.

    Examples:
        >>> from sage.all import sin
        >>> x0, x1 = coordinates(2)
        >>> term = metric_term(matrix(SR, [[1, 0], [0, sin(x0)**2]]))
        >>> 'fun x => ((Real.sin (x 0)) ^ 2 : ℝ)' in term, term.endswith(': Fin 2 → Fin 2 → (Fin 2 → ℝ) → ℝ)')
        (True, True)
    """
    n = g.nrows()
    rows = ', '.join('![' + ', '.join(f'fun x => {_render(e, n)}' for e in row) + ']' for row in g.rows())
    return f'(![{rows}] : Fin {n} → Fin {n} → (Fin {n} → ℝ) → ℝ)'


def christoffel_symbols(g: Matrix) -> dict[tuple[int, int, int], object]:
    """Return the nonzero Christoffel symbols `Γᵏᵢⱼ` of a metric, computed by SageManifolds.

    Args:
        g: The metric's matrix of expressions in the coordinates `x0, …`.

    Returns:
        The symbols by `(k, i, j)`, simplified.
    """
    n = g.nrows()
    manifold = Manifold(n, 'M', structure='pseudo-Riemannian', signature=None)
    chart = manifold.chart(' '.join(f'x{i}' for i in range(n)))
    metric = manifold.metric('g')
    for i in range(n):
        for j in range(n):
            metric[i, j] = SR(g[i, j])
    gamma = metric.christoffel_symbols(chart)
    symbols = {}
    for k in range(n):
        for i in range(n):
            for j in range(n):
                value = gamma[k, i, j].expr().simplify_full()
                if value != 0:
                    symbols[(k, i, j)] = value
    return symbols


def christoffel_proof(g: Matrix, *, metric: str, unfold: Sequence[str] = ()) -> Lean:
    """Return a proof of a goal `christoffel G k i j x = Γ` for an explicit metric `G` at a point.

    A constant metric's symbols vanish: the derivatives of its components are zero. Otherwise the proof states the
    inverse metric, rewrites with it, expands the partial derivatives and closes by `field_simp` and `ring`; the
    hypotheses that the inverse needs (a component nonzero) must be in the context.

    Args:
        g: The metric's matrix of expressions in the coordinates.
        metric: The Lean term of the metric as the goal writes it (a definition name or `metric_term(g)`).
        unfold: Definitions to unfold (the metric's name).

    Returns:
        The tactic.

    Raises:
        CertificateError: If the metric is degenerate.
    """
    n = g.nrows()
    if all(SR(e).is_constant() for e in g.list()):
        names = ', '.join(['CoordinateGeometry.christoffel', 'CoordinateGeometry.pd', *unfold])
        return tactic(f'simp [{names}]')
    if g.det().simplify_full() == 0:
        message = 'the metric is degenerate (its determinant vanishes)'
        raise CertificateError(message)
    inverse = matrix(SR, g).inverse().simplify_full()
    inverse_text = '!![' + '; '.join(', '.join(_render(e, n) for e in row) for row in inverse.rows()) + ']'
    names = ', '.join([*unfold, 'CoordinateGeometry.metricAt', 'Matrix.mul_apply', 'Fin.sum_univ_succ'])
    lines = [
        f'have hinv : CoordinateGeometry.invMetric {metric} x = {inverse_text} := by',
        '  refine Matrix.inv_eq_right_inv ?_',
        f'  ext a b\n  fin_cases a <;> fin_cases b <;> simp [{names}] <;> field_simp',
        'rw [CoordinateGeometry.christoffel, hinv]',
        f'simp (disch := fun_prop) [CoordinateGeometry.pd, {", ".join([*unfold, DERIVATIVE_SIMP])}]',
        'all_goals first | ring1 | (field_simp; ring1) | (field_simp; done)',
    ]
    return tactic('\n'.join(lines))


def killing_proof(*, unfold: Sequence[str] = ()) -> Lean:
    """Return a proof of `CoordinateGeometry.IsKilling G X` for an explicit metric and vector field.

    Every component of the Lie derivative is expanded (`simp` with derivative lemmas) and closed by `ring`.

    Args:
        unfold: Definitions to unfold (the metric's and the field's names).

    Returns:
        The tactic.
    """
    names = ', '.join(['CoordinateGeometry.lieMetric', 'CoordinateGeometry.pd', *unfold, DERIVATIVE_SIMP])
    return tactic(
        'intro a b x\n'
        'fin_cases a <;> fin_cases b <;>\n'
        f'  simp (disch := fun_prop) [{names}]\n'
        'all_goals first | ring1 | (field_simp; ring1)',
    )


def primitive(omega: Sequence[object]) -> object:
    """Return a function `f` with `df = ω` for a closed 1-form on ℝⁿ, by integrating along the coordinate axes.

    Args:
        omega: The components `ω₀, ω₁, …`, expressions in the coordinates `x0, …`.

    Returns:
        The primitive.

    Raises:
        CertificateError: If the form is not closed (`∂ᵢ ωⱼ ≠ ∂ⱼ ωᵢ`, naming the pair).

    Examples:
        >>> x0, x1, x2 = coordinates(3)
        >>> primitive([2 * x0 * x1, x0**2, 2 * x2])
        x0^2*x1 + x2^2
    """
    xs = coordinates(len(omega))
    for i in range(len(omega)):
        for j in range(i + 1, len(omega)):
            if (SR(omega[j]).diff(xs[i]) - SR(omega[i]).diff(xs[j])).simplify_full() != 0:
                message = f'the form is not closed: ∂{i} ω{j} ≠ ∂{j} ω{i}'
                raise CertificateError(message)
    f = SR(0)
    for i, x in enumerate(xs):
        remainder = (SR(omega[i]) - f.diff(x)).simplify_full()
        f += remainder.integral(x)
    return f.simplify_full()


def exact_form_proof(f: object, n: int) -> Lean:
    """Return a proof of `∀ i x, extDeriv F ![i] x = ω i x` for the 0-form `F` of a primitive `f`.

    The goal's `F` is `fun _ x => f x` and its `ω` the component functions; each component's partial derivative is
    expanded by `simp` and closed by `ring`.

    Args:
        f: The primitive (only its existence matters to the proof; Sage checks it).
        n: The dimension.

    Returns:
        The tactic.
    """
    del f
    names = ', '.join(['CoordinateGeometry.extDeriv', 'CoordinateGeometry.pd', DERIVATIVE_SIMP])
    return tactic(
        'intro i x\n'
        f'fin_cases i <;> simp (disch := fun_prop) [{names}]\n'
        'all_goals first | ring1 | (field_simp; ring1)',
    )


def field_invariant(f: Matrix, eta: Matrix) -> object:
    """Return `F_{μν} F^{μν}` for a field strength with lower indices and a constant metric.

    Args:
        f: The matrix `F_{μν}`.
        eta: The metric (its own inverse up to the sign conventions of a diagonal `±1` metric is not assumed).

    Returns:
        The contraction, expanded.

    Examples:
        >>> from sage.all import diagonal_matrix
        >>> e1, b3 = var('E1 B3')
        >>> f = matrix(SR, [[0, -e1, 0, 0], [e1, 0, -b3, 0], [0, b3, 0, 0], [0, 0, 0, 0]])
        >>> field_invariant(f, diagonal_matrix(SR, [1, -1, -1, -1]))
        2*B3^2 - 2*E1^2
    """
    inverse = eta.inverse()
    upper = inverse * f * inverse.transpose()
    return sum(f[m, n] * upper[m, n] for m in range(f.nrows()) for n in range(f.ncols())).expand()


def contraction_proof(names: Sequence[str]) -> Lean:
    """Return the proof of a contraction of explicit component arrays: expand the sums and close by `ring`.

    Args:
        names: The `let`-bound arrays of the goal to introduce and unfold.

    Returns:
        The tactic.
    """
    return tactic(f'intro {" ".join(names)}\nsimp [{", ".join([*names, "Fin.sum_univ_succ"])}]\nring')
