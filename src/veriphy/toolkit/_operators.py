"""Differential operators and matrix operators: commutators computed in Sage, identities proved in Lean.

A differential operator is built from multiplications by polynomials in the coordinates and partial derivatives, and
acts on a test function `ψ`. Sage applies both sides of a claimed identity to a symbolic `ψ` and compares them; Lean
proves the identity at a point by expanding the derivatives of products (`simp` with the derivative lemmas, the
differentiability side conditions discharged by `fun_prop`), using the symmetry of second derivatives in several
variables, and closing by `ring`. One variable uses `deriv`; several use `fderiv ℝ f y (Pi.single j 1)`.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from sage.all import QQ, SR, PolynomialRing, QuadraticField, diff, function, matrix, var, vector
from sage.matrix.matrix0 import Matrix
from sage.symbolic.expression import Expression

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic

# operators in several variables need the symmetry of second derivatives, which mathlib gives for C² functions
SECOND_ORDER = 2


@dataclass(frozen=True)
class Operator:
    """A linear differential operator, with its action on Sage expressions and on Lean function texts.

    Args:
        act: The action on a Sage expression in the coordinates.
        lean: The action on the Lean text of a function, returning the Lean text of a function.
        order: The highest derivative order it applies.
    """

    act: Callable[[Expression], Expression]
    lean: Callable[[str], str]
    order: int

    def __mul__(self, other: 'Operator') -> 'Operator':
        """Return the composition `self ∘ other`."""
        return Operator(lambda f: self.act(other.act(f)), lambda t: self.lean(other.lean(t)), self.order + other.order)

    def __add__(self, other: 'Operator') -> 'Operator':
        """Return the sum."""
        return Operator(
            lambda f: self.act(f) + other.act(f),
            lambda t: f'fun y => {_paren(self.lean(t))} y + {_paren(other.lean(t))} y',
            max(self.order, other.order),
        )

    def __sub__(self, other: 'Operator') -> 'Operator':
        """Return the difference."""
        return Operator(
            lambda f: self.act(f) - other.act(f),
            lambda t: f'fun y => {_paren(self.lean(t))} y - {_paren(other.lean(t))} y',
            max(self.order, other.order),
        )


def _paren(text: str) -> str:
    """Parenthesize a function text unless it is a single name."""
    return text if text.replace('_', '').replace('.', '').isalnum() else f'({text})'


@dataclass(frozen=True)
class Coordinates:
    """The coordinates operators act in: `n` Sage variables, rendered in Lean as `y` (one) or `y i` (several).

    Args:
        n: The number of coordinates.
    """

    n: int

    @property
    def symbols(self) -> list[Expression]:
        """Return the Sage coordinates `x0, x1, …`."""
        return [var(f'x{i}') for i in range(self.n)]

    def render(self, e: object) -> str:
        """Return a polynomial in the coordinates as Lean text in the bound variable `y`.

        Args:
            e: A polynomial with rational coefficients in the coordinates.

        Returns:
            The text.
        """
        ring = PolynomialRing(QQ, self.n, [f'x{i}' for i in range(self.n)])
        p = ring(SR(e))
        terms = []
        for coefficient, monomial in zip(p.coefficients(), p.monomials(), strict=True):
            factors = []
            for i, k in enumerate(monomial.exponents()[0]):
                if k:
                    base = 'y' if self.n == 1 else f'y {i}'
                    factors.append(base if k == 1 else f'({base}) ^ {k}' if self.n > 1 else f'y ^ {k}')
            q = QQ(coefficient)
            scalar = str(q) if q.denominator() == 1 else f'({q.numerator()} / {q.denominator()})'
            leading = [] if factors and q == 1 else [f'({scalar})']
            terms.append(' * '.join([*leading, *factors]))
        return ' + '.join(terms) if terms else '0'

    def multiplication(self, e: object) -> Operator:
        """Return the operator of multiplication by a polynomial in the coordinates.

        Args:
            e: The polynomial (a Sage expression in `x0, x1, …`).

        Returns:
            The operator.
        """
        text = self.render(e)
        return Operator(lambda f: SR(e) * f, lambda t: f'fun y => ({text}) * {_paren(t)} y', 0)

    def partial(self, i: int) -> Operator:
        """Return the partial derivative along the coordinate `i` (`deriv` in one variable).

        Args:
            i: The coordinate.

        Returns:
            The operator.
        """
        x = self.symbols[i]
        if self.n == 1:
            return Operator(lambda f: diff(f, x), lambda t: f'deriv {_paren(t)}', 1)
        return Operator(lambda f: diff(f, x), lambda t: f'fun y => fderiv ℝ {_paren(t)} y (Pi.single {i} 1)', 1)

    def scalar(self, c: object) -> Operator:
        """Return multiplication by a rational constant.

        Args:
            c: The constant.

        Returns:
            The operator.
        """
        return self.multiplication(QQ(c))


def commutator(a: Operator, b: Operator) -> Operator:
    """Return `[a, b] = a b - b a`.

    Args:
        a: An operator.
        b: Another.

    Returns:
        The commutator.
    """
    return a * b - b * a


def _differentiability(coordinates: Coordinates, order: int, psi: str, smooth: str, point: str) -> list[str]:
    """Return the facts `fun_prop` needs about `ψ` and its derivatives, from `smooth : ContDiff ℝ order ψ`."""
    if coordinates.n == 1:
        facts = []
        text = psi
        for m in range(order):
            facts.append(
                f'have hd{m} : Differentiable ℝ ({text}) := '
                f'({smooth}.iterate_deriv\' {order - m} {m}).differentiable (by norm_num)',
            )
            text = f'deriv ({text})'
        return facts
    if order > SECOND_ORDER:
        message = 'operators in several variables are supported up to second order'
        raise CertificateError(message)
    facts = [f'have hd0 : Differentiable ℝ {psi} := {smooth}.differentiable (by norm_num)']
    if order == SECOND_ORDER:
        facts += [
            (
                f'have hd1 : Differentiable ℝ (fderiv ℝ {psi}) := '
                f'({smooth}.fderiv_right (m := 1) (by norm_num)).differentiable (by norm_num)'
            ),
            f'have hsymm := ({smooth}.contDiffAt (x := {point})).isSymmSndFDerivAt (by simp)',
        ]
    return facts


def operator_identity(
    lhs: Operator,
    rhs: Operator,
    coordinates: Coordinates,
    *,
    psi: str = 'ψ',
    smooth: str = 'hψ',
    point: str = 'x',
    name: str = 'hop',
) -> Lean:
    """Return a fact `(lhs ψ) x = (rhs ψ) x`, checked first in Sage on a symbolic `ψ`, then proved in Lean.

    Args:
        lhs: The left operator.
        rhs: The right operator.
        coordinates: The coordinates.
        psi: The Lean name of the test function.
        smooth: The Lean name of the hypothesis `ContDiff ℝ k ψ`, with `k` the identity's order.
        point: The Lean name of the point.
        name: The fact's name.

    Returns:
        The tactic.

    Raises:
        CertificateError: If the identity fails in Sage (the difference is shown).

    Examples:
        >>> c = Coordinates(1)
        >>> d, x = c.partial(0), c.multiplication(c.symbols[0])
        >>> print(operator_identity(commutator(d, x), c.scalar(1), c).text.splitlines()[0])
        have hd0 : Differentiable ℝ (ψ) := (hψ.iterate_deriv' 1 0).differentiable (by norm_num)
    """
    xs = coordinates.symbols
    test = function('psi_')(*xs)
    difference = (lhs.act(test) - rhs.act(test)).expand()
    if difference != 0:
        message = f'the identity fails in Sage: the two sides differ by {difference}'
        raise CertificateError(message)
    order = max(lhs.order, rhs.order)
    facts = _differentiability(coordinates, order, psi, smooth, point)
    statement = f'({lhs.lean(psi)}) {point} = ({rhs.lean(psi)}) {point}'
    if coordinates.n == 1:
        proof = ['simp (disch := fun_prop) [deriv_fun_mul, deriv_fun_sub, deriv_fun_add]', 'all_goals ring']
    else:
        proof = [
            (
                f'have hproj : ∀ (i : Fin {coordinates.n}) (v : Fin {coordinates.n} → ℝ), '
                f'fderiv ℝ (fun y : Fin {coordinates.n} → ℝ => y i) {point} v = v i := '
                f'fun i v => by rw [(hasFDerivAt_apply i {point}).fderiv]; rfl'
            ),
            (
                'simp (disch := fun_prop) [fderiv_fun_sub, fderiv_fun_add, fderiv_fun_mul, fderiv_clm_apply, hproj, '
                'Pi.single_apply]'
            ),
        ]
        if order == SECOND_ORDER:
            pairs = [(i, j) for i in range(coordinates.n) for j in range(i + 1, coordinates.n)]
            rewrites = ', '.join(f'hsymm (Pi.single {i} 1) (Pi.single {j} 1)' for i, j in pairs)
            proof.append(f'try simp only [{rewrites}]')
        proof.append('all_goals ring')
    body = '\n'.join(f'  {line}' for line in proof)
    return tactic('\n'.join([*facts, f'have {name} : {statement} := by', body]))


ENTRYWISE = (
    'ext i j\n'
    'fin_cases i <;> fin_cases j <;> simp [Matrix.mul_apply, Fin.sum_univ_succ, Matrix.smul_apply, Matrix.sub_apply, '
    'Matrix.add_apply]\n'
    'all_goals first | ring1 | (ring_nf; simp [Complex.I_sq, Complex.I_mul_I]; ring_nf; done) | '
    '(ring_nf; simp [Complex.I_sq, Complex.I_mul_I]; done) | (norm_num; done)'
)


def _complex(c: object) -> str:
    """Return a Gaussian rational `a + b i` as Lean text over ℂ."""
    value = QuadraticField(-1, 'i')(c)
    a, b = QQ(value[0]), QQ(value[1])

    def rat(q: object) -> str:
        q = QQ(q)
        return str(q) if q.denominator() == 1 else f'({q.numerator()} / {q.denominator()})'

    if b == 0:
        return rat(a)
    imaginary = 'Complex.I' if b == 1 else f'{rat(b)} * Complex.I'
    return f'({imaginary})' if a == 0 else f'({rat(a)} + {imaginary})'


def complex_matrix_term(m: Matrix) -> str:
    """Return a matrix over ℚ(i) as a Lean `!![…]` literal over ℂ.

    Args:
        m: The matrix, with entries in `QuadraticField(-1)` (or rationals).

    Returns:
        The literal.

    Examples:
        >>> i = QuadraticField(-1, 'i').gen()
        >>> complex_matrix_term(matrix([[0, -i], [i, 0]]))
        '(!![0, (-1 * Complex.I); (Complex.I), 0] : Matrix (Fin 2) (Fin 2) ℂ)'
    """
    rows = '; '.join(', '.join(_complex(x) for x in row) for row in m.rows())
    return f'(!![{rows}] : Matrix (Fin {m.nrows()}) (Fin {m.ncols()}) ℂ)'


def operator_relations(
    matrices: Sequence[Matrix],
    names: Sequence[str],
    pairs: Sequence[tuple[int, int]] | None = None,
) -> Lean:
    """Return facts `Xᵢ * Xⱼ - Xⱼ * Xᵢ = Σ cₖ • Xₖ` for matrices over ℚ(i), proved entrywise over ℂ.

    Args:
        matrices: The matrices (Pauli, spin, gamma matrices), with entries in ℚ(i).
        names: Their Lean names (definitions over ℂ, unfolded by the proof).
        pairs: The pairs to state; every `i < j` when `None`.

    Returns:
        The facts `hcomm_i_j`.

    Raises:
        CertificateError: If a commutator is not in the span of the matrices.
    """
    field = QuadraticField(-1, 'i')
    rows = matrix(field, [m.list() for m in matrices])
    chosen = pairs if pairs is not None else [(i, j) for i in range(len(matrices)) for j in range(i + 1, len(matrices))]
    lines = []
    for i, j in chosen:
        bracket = matrices[i] * matrices[j] - matrices[j] * matrices[i]
        try:
            coefficients = rows.solve_left(vector(field, bracket.list()))
        except ValueError:
            message = f'[{names[i]}, {names[j]}] is not in the span of the matrices'
            raise CertificateError(message) from None
        terms = [f'{_complex(c)} • {names[k]}' for k, c in enumerate(coefficients) if c != 0]
        rhs = ' + '.join(terms) if terms else '0'
        proof = '\n'.join(f'  {line}' for line in [f'unfold {" ".join(dict.fromkeys(names))}', *ENTRYWISE.splitlines()])
        lines.append(f'have hcomm_{i}_{j} : {names[i]} * {names[j]} - {names[j]} * {names[i]} = {rhs} := by\n{proof}')
    return tactic('\n'.join(lines))


def ladder_matrices(levels: int) -> tuple[Matrix, Matrix]:
    """Return the annihilation and creation operators truncated to `levels` states, over Sage's symbolic ring.

    `a |n⟩ = √n |n - 1⟩`; on the truncated space `[a, a†] = 1 - levels · |levels - 1⟩⟨levels - 1|`.

    Args:
        levels: The number of states.

    Returns:
        `a` and `a†`.

    Examples:
        >>> a, ad = ladder_matrices(3)
        >>> (a * ad - ad * a).diagonal()
        [1, 1, -2]
    """
    a = matrix(SR, levels, levels)
    for n in range(1, levels):
        a[n - 1, n] = SR(n).sqrt()
    return a, a.transpose()


def real_matrix_term(m: Matrix) -> str:
    """Return a matrix with entries `q √k` as a Lean literal over ℝ.

    Args:
        m: The matrix (rationals times square roots of integers).

    Returns:
        The literal.
    """

    def entry(x: object) -> str:
        e = SR(x)
        if e in QQ:
            q = QQ(e)
            return str(q) if q.denominator() == 1 else f'({q.numerator()} / {q.denominator()})'
        squared = QQ(e**2)
        if squared.denominator() == 1 and e > 0:
            return f'Real.sqrt {squared}'
        message = f'cannot render {e} as a rational or a square root'
        raise CertificateError(message)

    rows = '; '.join(', '.join(entry(x) for x in row) for row in m.rows())
    return f'(!![{rows}] : Matrix (Fin {m.nrows()}) (Fin {m.ncols()}) ℝ)'


def matrix_identity_proof() -> Lean:
    """Return the entrywise proof of an identity between explicit matrices over ℝ or ℂ (`√k`, `Complex.I` entries).

    Returns:
        The tactic.
    """
    return tactic(ENTRYWISE)


def ladder_operators(xi: object = None, hbar: object = None) -> tuple[dict[str, object], dict[str, object]]:
    """Return the lowering and raising operators as combinations of one coordinate's position and momentum.

    `a = (x/ξ + i ξ p/ℏ)/√2` and `a† = (x/ξ - i ξ p/ℏ)/√2`, Physlib's convention for the harmonic oscillator.

    Args:
        xi: The length scale `ξ`; the symbol `xi` when `None`.
        hbar: The reduced Planck constant; the symbol `hbar` when `None`.

    Returns:
        The coefficients of `'x'` and `'p'` in `a` and in `a†`.

    Examples:
        >>> lowering, raising = ladder_operators()
        >>> lowering['p']
        1/2*I*sqrt(2)*xi/hbar
    """
    xi = var('xi') if xi is None else xi
    hbar = var('hbar') if hbar is None else hbar
    scale = 1 / SR(2).sqrt()
    lowering = {'x': (scale / xi).simplify_full(), 'p': (scale * SR.I() * xi / hbar).simplify_full()}
    raising = {'x': lowering['x'], 'p': -lowering['p']}
    return lowering, raising


def canonical_commutator(left: dict[str, object], right: dict[str, object], hbar: object = None) -> object:
    """Return `[A, B]` as a multiple of the identity, for combinations of one coordinate's `x` and `p`.

    With `[x, x] = [p, p] = 0` and `[x, p] = iℏ`, `[αₓ x + αₚ p, βₓ x + βₚ p] = iℏ (αₓ βₚ - αₚ βₓ)`.

    Args:
        left: The coefficients of `'x'` and `'p'` in `A` (missing ones zero).
        right: Those of `B`.
        hbar: The reduced Planck constant; the symbol `hbar` when `None`.

    Returns:
        The scalar, simplified.

    Examples:
        >>> lowering, raising = ladder_operators()
        >>> canonical_commutator(lowering, raising)
        1
        >>> canonical_commutator(lowering, {'x': 1})
        1/2*sqrt(2)*xi
    """
    hbar = var('hbar') if hbar is None else hbar
    alpha_x, alpha_p = SR(left.get('x', 0)), SR(left.get('p', 0))
    beta_x, beta_p = SR(right.get('x', 0)), SR(right.get('p', 0))
    return (SR.I() * hbar * (alpha_x * beta_p - alpha_p * beta_x)).simplify_full()
