"""Fusion categories: fusion rules from Sage, F- and R-symbols checked against the `FusionData` asset by the kernel.

Data are multiplicity free, on labels `0 … n-1` (the unit first). F-symbols are given by their values where they differ
from 1 (every other admissible symbol is 1, inadmissible ones 0), R-symbols likewise. Exact values in `ℚ(√5)` or
`ℚ(ζ₁₆)` go to Lean as rational coefficients on the power basis of `ζ = √5` or `ζ₁₆`; `decide +kernel` checks
associativity, unit, duals, the pentagon and the hexagons on those coefficients, on admissible labels, and the asset's
theorems give the equations at every `ζ` with the same minimal relation, in any `ℚ`-algebra.
"""

import itertools
from collections.abc import Callable
from dataclasses import dataclass, field

from sage.all import QQ, CyclotomicField, FusionRing, PolynomialRing, QuadraticField, prod
from sage.structure.element import FieldElement
from sage.structure.parent import Parent

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic

SQRT5 = QuadraticField(5, 's')
ZETA16 = CyclotomicField(16, 'z')

Key = tuple[int, ...]
Triple = tuple[int, int, int]
# a gauge: the scalar on each admissible triple's splitting space
Gauge = dict[Triple, FieldElement]


@dataclass
class Fusion:
    """Multiplicity-free fusion data on labels `0 … n-1`, the unit first.

    Args:
        labels: Names of the simple objects.
        dual: The dual of each label.
        rules: `(a, b) → [c, …]`, the labels in `a ⊗ b`.
        f_values: `(a, b, c, d, e, f) → value` where `(F^{abc}_d)_{ef}` is not 1.
        r_values: `(a, b, c) → value` where `R^{ab}_c` is not 1.
        field: `'sqrt5'`, `'zeta16'` or `'rational'`: where the values live.
    """

    labels: list[str]
    dual: list[int]
    rules: dict[tuple[int, int], list[int]]
    f_values: dict[Key, FieldElement] = field(default_factory=dict)
    r_values: dict[Triple, FieldElement] = field(default_factory=dict)
    field: str = 'rational'

    @property
    def size(self) -> int:
        """Return the number of labels."""
        return len(self.labels)

    def n(self, a: int, b: int, c: int) -> int:
        """Return the multiplicity of `c` in `a ⊗ b`."""
        return 1 if c in self.rules.get((a, b), []) else 0

    def f(self, *labels: int) -> FieldElement:
        """Return `(F^{abc}_d)_{ef}` for the labels `a, b, c, d, e, f`, zero when inadmissible."""
        a, b, c, d, e, f = labels
        if not (self.n(a, b, e) and self.n(e, c, d) and self.n(b, c, f) and self.n(a, f, d)):
            return QQ(0)
        return self.f_values.get((a, b, c, d, e, f), QQ(1))

    def r(self, a: int, b: int, c: int) -> FieldElement:
        """Return `R^{ab}_c`, zero when inadmissible."""
        return self.r_values.get((a, b, c), QQ(1)) if self.n(a, b, c) else QQ(0)


def fusion_rules(cartan_type: str, level: int) -> Fusion:
    """Return the fusion rules of a quantum group at a root of unity, from Sage's `FusionRing`.

    Args:
        cartan_type: The type, as `'A1'` or `'G2'`.
        level: The level.

    Returns:
        The fusion data with rules and duals (F- and R-symbols to be supplied).

    Raises:
        CertificateError: If a fusion multiplicity exceeds 1: the asset covers multiplicity-free categories only.

    Examples:
        >>> ising = fusion_rules('A1', 2)
        >>> ising.labels, ising.rules[(1, 1)]
        (['A12(0)', 'A12(1)', 'A12(2)'], [0, 2])
    """
    ring = FusionRing(cartan_type, level)
    basis = list(ring.basis())
    index = {b: i for i, b in enumerate(basis)}
    rules = {}
    for (i, a), (j, b) in itertools.product(enumerate(basis), repeat=2):
        product = list(a * b)
        if any(coefficient > 1 for _, coefficient in product):
            message = (
                f'{a} ⊗ {b} has a fusion multiplicity above 1: {cartan_type} at level {level} is not multiplicity '
                'free, outside the FusionData asset (F-symbols would be matrices on multiplicity spaces)'
            )
            raise CertificateError(message)
        rules[(i, j)] = sorted(index[ring.monomial(key)] for key, _ in product)
    dual = [index[b.dual()] for b in basis]
    return Fusion([str(b) for b in basis], dual, rules)


def fibonacci() -> Fusion:
    """Return the Fibonacci category's fusion data, with F-symbols in a gauge over `ℚ(√5)`.

    The only nontrivial F-matrix is `F^{τττ}_τ`; its entries are solved from the pentagon equations with the gauge
    fixed by `(F^{τττ}_τ)_{1τ} = 1`.

    Returns:
        The data.

    Raises:
        CertificateError: If the pentagon equations have no solution in `ℚ(√5)` in this gauge.
    """
    data = Fusion(['1', 'τ'], [0, 1], {(0, 0): [0], (0, 1): [1], (1, 0): [1], (1, 1): [0, 1]}, field='sqrt5')
    ring = PolynomialRing(SQRT5, 'p, q, r')
    p, q, r = ring.gens()
    trial = Fusion(data.labels, data.dual, data.rules)
    trial.f_values = {(1, 1, 1, 1, 0, 0): p, (1, 1, 1, 1, 0, 1): 1, (1, 1, 1, 1, 1, 0): q, (1, 1, 1, 1, 1, 1): r}
    equations = [lhs - rhs for lhs, rhs in _pentagon_sides(trial)]
    solutions = ring.ideal(equations).variety()
    if not solutions:
        message = 'the Fibonacci pentagon equations have no solution in ℚ(√5) in this gauge'
        raise CertificateError(message)
    s = next(x for x in solutions if x[p] != 0)
    data.f_values = {
        (1, 1, 1, 1, 0, 0): s[p],
        (1, 1, 1, 1, 1, 0): s[q],
        (1, 1, 1, 1, 1, 1): s[r],
    }
    return data


def ising() -> Fusion:
    """Return the Ising category's fusion data, with F- and R-symbols over `ℚ(ζ₁₆)`.

    The labels and rules are SU(2) at level 2 (`1`, `σ`, `ψ`); `F^{σσσ}_σ = (1/√2) [[1, 1], [1, -1]]` and
    `F^{σψσ}_ψ = F^{ψσψ}_σ = -1`; `R^{σσ}_1 = ζ₁₆⁻¹`, `R^{σσ}_ψ = ζ₁₆³`, `R^{σψ}_σ = R^{ψσ}_σ = -i`, `R^{ψψ}_1 = -1`.
    (SU(2) at level 2 itself has the opposite sign of `F^{σσσ}_σ` and other R-symbols: a different braided category
    with the same fusion rules.)

    Returns:
        The data.

    Examples:
        >>> data = ising()
        >>> pentagon_violations(data), hexagon_violations(data)
        (0, 0)
    """
    rules = fusion_rules('A1', 2)
    z = ZETA16.gen()
    root2 = z**2 + z**-2  # √2 = ζ₈ + ζ₈⁻¹
    sigma, psi = 1, 2
    f_values: dict[Key, FieldElement] = {
        (sigma, sigma, sigma, sigma, 0, 0): 1 / root2,
        (sigma, sigma, sigma, sigma, 0, psi): 1 / root2,
        (sigma, sigma, sigma, sigma, psi, 0): 1 / root2,
        (sigma, sigma, sigma, sigma, psi, psi): -1 / root2,
        (sigma, psi, sigma, psi, sigma, sigma): ZETA16(-1),
        (psi, sigma, psi, sigma, sigma, sigma): ZETA16(-1),
    }
    r_values = {
        (sigma, sigma, 0): z**-1,
        (sigma, sigma, psi): z**3,
        (sigma, psi, sigma): z**-4,
        (psi, sigma, sigma): z**-4,
        (psi, psi, 0): ZETA16(-1),
    }
    return Fusion(['1', 'σ', 'ψ'], rules.dual, rules.rules, f_values, r_values, field='zeta16')


def _pentagon_sides(data: Fusion) -> list[tuple[FieldElement, FieldElement]]:
    """Return both sides of every pentagon equation."""
    sides = []
    labels = range(data.size)
    for a, b, c, d, e, f, g, k, ell in itertools.product(labels, repeat=9):
        lhs = data.f(f, c, d, e, g, ell) * data.f(a, b, ell, e, f, k)
        rhs = sum(data.f(a, b, c, g, f, h) * data.f(a, h, d, e, g, k) * data.f(b, c, d, k, h, ell) for h in labels)
        sides.append((lhs, rhs))
    return sides


def associativity_violations(data: Fusion) -> list[tuple[int, int, int, int]]:
    """Return the label tuples where the fusion rules fail associativity.

    Args:
        data: The fusion data.

    Returns:
        The failing `(a, b, c, d)`.
    """
    labels = range(data.size)
    return [
        (a, b, c, d)
        for a, b, c, d in itertools.product(labels, repeat=4)
        if sum(data.n(a, b, e) * data.n(e, c, d) for e in labels)
        != sum(data.n(b, c, f) * data.n(a, f, d) for f in labels)
    ]


def pentagon_violations(data: Fusion) -> int:
    """Return the number of pentagon equations the F-symbols fail.

    Args:
        data: The fusion data.

    Returns:
        The count.
    """
    return sum(1 for lhs, rhs in _pentagon_sides(data) if lhs != rhs)


def hexagon_violations(data: Fusion) -> int:
    """Return the number of hexagon equations (both kinds) the R- and F-symbols fail.

    Args:
        data: The fusion data.

    Returns:
        The count.
    """
    labels = range(data.size)

    def inv(x: FieldElement) -> FieldElement:
        return QQ(0) if x == 0 else QQ(1) / x

    failures = 0
    for a, b, c, d, e, g in itertools.product(labels, repeat=6):
        one = data.r(c, a, e) * data.f(a, c, b, d, e, g) * data.r(c, b, g)
        one_rhs = sum(data.f(c, a, b, d, e, f) * data.r(c, f, d) * data.f(a, b, c, d, f, g) for f in labels)
        two = inv(data.r(a, c, e)) * data.f(a, c, b, d, e, g) * inv(data.r(b, c, g))
        two_rhs = sum(data.f(c, a, b, d, e, f) * inv(data.r(f, c, d)) * data.f(a, b, c, d, f, g) for f in labels)
        failures += (one != one_rhs) + (two != two_rhs)
    return failures


def _rational(q: FieldElement | int) -> str:
    """Return a rational as Lean text."""
    q = QQ(q)
    return str(q) if q.denominator() == 1 else f'({q.numerator()} / {q.denominator()})'


def coefficients(x: FieldElement | int, which: str) -> list[FieldElement]:
    """Return a value's rational coefficients on the power basis `1, ζ, …` of its field, trailing zeros dropped.

    Args:
        x: An element of `ℚ`, `ℚ(√5)` (`ζ = √5`) or `ℚ(ζ₁₆)`.
        which: `'rational'`, `'sqrt5'` or `'zeta16'`.

    Returns:
        The coefficients; empty for zero.

    Examples:
        >>> coefficients(SQRT5.gen() / 2 - 1, 'sqrt5')
        [-1, 1/2]
        >>> coefficients(ZETA16.gen() ** 3, 'zeta16')
        [0, 0, 0, 1]
    """
    if which == 'rational':
        values = [QQ(x)]
    elif which == 'sqrt5':
        values = list(SQRT5(x))
    else:
        values = list(ZETA16(x).polynomial().padded_list(8)) if ZETA16(x) != 0 else []
    while values and values[-1] == 0:
        values.pop()
    return values


def _coefficients_lean(x: FieldElement | int, which: str) -> str:
    """Return a value's coefficient list as Lean text."""
    return '[' + ', '.join(_rational(q) for q in coefficients(x, which)) + ']'


def _lookup(values: dict[Key, FieldElement] | Gauge, which: str, n: int) -> str:
    """Return a Lean association list from label tuples to coefficient lists."""
    entries = ', '.join(
        '((' + ', '.join(f'({i} : Fin {n})' for i in key) + f'), {_coefficients_lean(v, which)})'
        for key, v in values.items()
    )
    return f'[{entries}]'


FIELDS = {'rational': (1, 1, ''), 'sqrt5': (2, 5, '√5'), 'zeta16': (8, -1, 'ζ₁₆')}


def fusion_data_term(data: Fusion) -> str:
    """Return the data as a Lean `FusionData.RepData n` term, values as coefficient lists.

    Args:
        data: The fusion data.

    Returns:
        The term.
    """
    n = data.size
    dual = '![' + ', '.join(str(d) for d in data.dual) + ']'
    rules = (
        '!['
        + ', '.join(
            '![' + ', '.join('![' + ', '.join(str(data.n(a, b, c)) for c in range(n)) + ']' for b in range(n)) + ']'
            for a in range(n)
        )
        + ']'
    )
    admissible_f = 'N a b e ≠ 0 ∧ N e c d ≠ 0 ∧ N b c f ≠ 0 ∧ N a f d ≠ 0'
    labels6 = ' × '.join([f'Fin {n}'] * 6)
    f_term = (
        f'fun a b c d e f => (({_lookup(data.f_values, data.field, n)} : List (({labels6}) × List ℚ)).lookup '
        f'(a, b, c, d, e, f)).getD (if {admissible_f} then [1] else [])'
    )

    def braiding(values: Gauge) -> str:
        listed = _lookup(values, data.field, n)
        return (
            f'fun a b c => (({listed} : List ((Fin {n} × Fin {n} × Fin {n}) × List ℚ)).lookup (a, b, c)).getD '
            '(if N a b c ≠ 0 then [1] else [])'
        )

    r_term = braiding(data.r_values)
    rinv_term = braiding({key: 1 / value for key, value in data.r_values.items()})
    return (
        f'(let N : Fin {n} → Fin {n} → Fin {n} → ℕ := {rules}; '
        f'(⟨0, {dual}, N, {f_term}, {r_term}, {rinv_term}⟩ : FusionData.RepData {n}))'
    )


ROOTS = {
    'rational': ('(1 : ℚ)', 'simp'),
    'sqrt5': ('Real.sqrt 5', 'rw [Real.sq_sqrt (by norm_num)]; simp'),
    'zeta16': (
        'Complex.exp (2 * Real.pi * Complex.I / 16)',
        (
            'rw [← Complex.exp_nat_mul, show ((8 : ℕ) : ℂ) * (2 * Real.pi * Complex.I / 16) = Real.pi * Complex.I by\n'
            '    push_cast; ring, Complex.exp_pi_mul_I]\n'
            '  simp'
        ),
    ),
}


def root_fact(which: str) -> Lean:
    """Return the fact `hζ : ζ ^ m = r` for the field's standard root: `1`, `√5` in ℝ or `exp (2πi/16)` in ℂ.

    Args:
        which: `'rational'`, `'sqrt5'` or `'zeta16'`.

    Returns:
        The fact.

    Examples:
        >>> print(root_fact('sqrt5'))
        have hζ : Real.sqrt 5 ^ 2 = algebraMap ℚ _ (5) := by
          rw [Real.sq_sqrt (by norm_num)]; simp
    """
    m, r, _ = FIELDS[which]
    zeta, proof = ROOTS[which]
    return tactic(f'have hζ : {zeta} ^ {m} = algebraMap ℚ _ ({r}) := by\n  {proof}')


def _failure(data: Fusion, *, braided: bool) -> str | None:
    """Return what fails among associativity, the pentagon and (when braided) the hexagons in Sage, if anything."""
    if associativity_violations(data):
        return f'the fusion rules are not associative at {associativity_violations(data)[0]}'
    failures = pentagon_violations(data)
    if failures:
        return f'{failures} pentagon equations fail'
    if braided and hexagon_violations(data):
        return f'{hexagon_violations(data)} hexagon equations fail'
    return None


def fusion_proof(data: Fusion, *, braided: bool, root: bool = True) -> Lean:
    """Return a proof of a goal `FusionData.IsFusion (RepData.toData E ζ)` (or `IsBraidedFusion`) for explicit `E`.

    Sage checks the data first, naming what fails; the kernel then checks the goal's own `E` (a definition or the
    literal of `fusion_data_term`), so the data must be Sage's in the goal's gauge (see `gauge_mismatch`).

    Args:
        data: The fusion data the goal states.
        braided: Whether the goal is `IsBraidedFusion`.
        root: Whether `ζ` is the field's standard root (`root_fact`); otherwise a hypothesis `hζ : ζ ^ m = …` must be
            in the context.

    Returns:
        The tactic.

    Raises:
        CertificateError: If associativity, the pentagon or (when braided) the hexagons fail.
    """
    failure = _failure(data, braided=braided)
    if failure is not None:
        raise CertificateError(failure)
    m, r, _ = FIELDS[data.field]
    check = 'isBraidedFusion' if braided else 'isFusion'
    lines = [str(root_fact(data.field))] if root else []
    lines.append(
        f'exact FusionData.RepData.{check} (m := {m}) (r := {r}) hζ '
        '(by set_option maxRecDepth 100000 in decide +kernel)',
    )
    return tactic('\n'.join(lines))


def gauge_proof(reference: Fusion, target: Fusion, u: Gauge, *, root: bool = True) -> Lean:
    """Return a proof of a goal `FusionData.GaugeRelated (E.toData ζ) (E'.toData ζ) (eval U) (eval Uinv)`.

    The goal's gauge functions are `fun a b c => FusionData.Coeffs.eval ζ (U a b c)` with `U` the lookup that
    `gauge_term(u, data)` prints; Sage checks that `u` relates the data, the kernel checks the goal's.

    Args:
        reference: The data in Sage's gauge.
        target: The data in the goal's gauge.
        u: The gauge (from `find_gauge`).
        root: Whether `ζ` is the field's standard root; otherwise a hypothesis `hζ` must be in the context.

    Returns:
        The tactic.

    Raises:
        CertificateError: If `u` does not relate the data.
    """
    failure = _gauge_failure(reference, target, u)
    if failure is not None:
        raise CertificateError(failure)
    m, r, _ = FIELDS[reference.field]
    lines = [str(root_fact(reference.field))] if root else []
    lines.append(
        f'exact FusionData.RepData.gaugeRelated (m := {m}) (r := {r}) hζ '
        '(by set_option maxRecDepth 100000 in decide +kernel)',
    )
    return tactic('\n'.join(lines))


def gauge_term(u: Gauge, data: Fusion, *, inverse: bool = False) -> str:
    """Return a gauge (or its inverse) as a Lean `Fin n → Fin n → Fin n → List ℚ`, 1 where unlisted.

    Args:
        u: The gauge.
        data: The data it acts on (for the labels and the field).
        inverse: Whether to return the inverse gauge.

    Returns:
        The term.

    Examples:
        >>> term = gauge_term({(1, 1, 1): 2}, fibonacci(), inverse=True)
        >>> '(((1 : Fin 2), (1 : Fin 2), (1 : Fin 2)), [(1 / 2)])' in term, term.endswith('.getD [1]')
        (True, True)
    """
    n = data.size
    values = {key: (1 / _field(data)(v) if inverse else v) for key, v in u.items()}
    listed = _lookup(values, data.field, n)
    return f'fun a b c => (({listed} : List ((Fin {n} × Fin {n} × Fin {n}) × List ℚ)).lookup (a, b, c)).getD [1]'


def _gauge_failure(reference: Fusion, target: Fusion, u: Gauge) -> str | None:
    """Return why the gauge does not take the reference data to the target's in Sage, if it does not."""
    moved = gauge_transform(reference, u)
    if any(moved.f(*key) != target.f(*key) for key in itertools.product(range(reference.size), repeat=6)):
        return 'the gauge does not take the reference F-symbols to the target ones'
    if any(moved.r(*key) != target.r(*key) for key in _admissible_triples(reference)):
        return 'the gauge does not take the reference R-symbols to the target ones'
    return None


def fusion_facts(data: Fusion, *, braided: bool, symbols: bool = True) -> Lean:
    """Return the fact that the data form a fusion category (and a braided one), checked in Sage, then by the kernel.

    The kernel checks the equations once on coefficient lists, on admissible labels; the asset's theorems give them
    in every `ℚ`-algebra at every `ζ` with `ζ ^ m = r` (`ζ² = 5` for `ℚ(√5)`, `ζ⁸ = -1` for `ℚ(ζ₁₆)`), so the fact
    applies over `ℝ` or `ℂ` and at every Galois conjugate.

    Args:
        data: The fusion data.
        braided: Whether to state the hexagons too.
        symbols: Whether to state the pentagon (`False` for fusion rules alone, with no F-symbols).

    Returns:
        The fact `hfusion`: `∀ K ζ, ζ ^ m = r → FusionData.IsFusion (E.toData ζ)` (or `IsBraidedFusion`), or the fusion
        ring axioms of the rules alone.

    Raises:
        CertificateError: If associativity, the pentagon or (when braided) the hexagons fail in Sage.
    """
    failure = _failure(data, braided=braided) if symbols else None
    if failure is not None:
        raise CertificateError(failure)
    if associativity_violations(data):
        message = f'the fusion rules are not associative at {associativity_violations(data)[0]}'
        raise CertificateError(message)
    term = fusion_data_term(data)
    if not symbols:
        return tactic(f'have hfusion : FusionData.RepData.IsFusionRing {term} := by\n  decide +kernel')
    m, r, _ = FIELDS[data.field]
    bundle = 'IsBraidedFusion' if braided else 'IsFusion'
    check = 'isBraidedFusion' if braided else 'isFusion'
    # the kernel decides the pruned equations on coefficients; the asset's theorems give the full ones at every ζ
    return tactic(
        f'have hfusion : ∀ {{K : Type}} [CommRing K] [Algebra ℚ K] (ζ : K), ζ ^ {m} = algebraMap ℚ K ({r}) →\n'
        f'    FusionData.{bundle} (FusionData.RepData.toData {term} ζ) :=\n'
        f'  fun _ hζ => FusionData.RepData.{check} (m := {m}) (r := {r}) hζ\n'
        '    (by set_option maxRecDepth 100000 in decide +kernel)',
    )


def _field(data: Fusion) -> Parent:
    """Return the Sage field the data's values live in."""
    return {'rational': QQ, 'sqrt5': SQRT5, 'zeta16': ZETA16}[data.field]


def _admissible_triples(data: Fusion) -> list[Triple]:
    """Return the triples `(a, b, c)` with `c` in `a ⊗ b`."""
    return [(a, b, c) for a, b, c in itertools.product(range(data.size), repeat=3) if data.n(a, b, c)]


def gauge_transform(data: Fusion, u: Gauge) -> Fusion:
    """Return the data in another gauge.

    `(F'^{abc}_d)_{ef} = u^{ab}_e u^{ec}_d / (u^{bc}_f u^{af}_d) (F^{abc}_d)_{ef}` and
    `R'^{ab}_c = u^{ba}_c / u^{ab}_c R^{ab}_c`; unlisted `u` are 1.

    Args:
        data: The fusion data.
        u: The gauge, on admissible triples.

    Returns:
        The transformed data, which satisfies the same pentagon and hexagon equations.

    Examples:
        >>> fib = fibonacci()
        >>> other = gauge_transform(fib, {(1, 1, 1): 2})
        >>> other.f(1, 1, 1, 1, 1, 0) == 4 * fib.f(1, 1, 1, 1, 1, 0), pentagon_violations(other)
        (True, 0)
    """
    field = _field(data)

    def g(a: int, b: int, c: int) -> FieldElement:
        return field(u.get((a, b, c), 1))

    f_values = {}
    for key in itertools.product(range(data.size), repeat=6):
        a, b, c, d, e, f = key
        value = data.f(*key)
        if value == 0:
            continue
        new = g(a, b, e) * g(e, c, d) / (g(b, c, f) * g(a, f, d)) * value
        if new != 1:
            f_values[key] = new
    r_values = {}
    for a, b, c in _admissible_triples(data):
        new = g(b, a, c) / g(a, b, c) * data.r(a, b, c)
        if new != 1:
            r_values[(a, b, c)] = new
    return Fusion(data.labels, data.dual, data.rules, f_values, r_values, data.field)


def find_gauge(reference: Fusion, target: Fusion) -> Gauge | None:
    """Return a gauge taking the reference data to the target's, or `None` when they are not gauge equivalent.

    The unknowns `u^{ab}_c` (one per admissible triple, nonzero) satisfy polynomial equations; gauge freedom left over
    (gauges fixing the data) is spent by setting unknowns to 1 while the system stays consistent, and the remaining
    finite system is solved in the data's field.

    Args:
        reference: The data in Sage's gauge.
        target: The data in the goal's gauge, same labels and rules.

    Returns:
        The gauge, on the admissible triples where it is not 1.

    Raises:
        CertificateError: If the fusion rules differ.

    Examples:
        >>> fib = fibonacci()
        >>> u = find_gauge(fib, gauge_transform(fib, {(1, 1, 1): 2}))
        >>> gauge_transform(fib, u).f_values == gauge_transform(fib, {(1, 1, 1): 2}).f_values
        True
    """
    if reference.rules != target.rules:
        message = 'the fusion rules differ: no gauge relates the data'
        raise CertificateError(message)
    triples = _admissible_triples(reference)
    ring = PolynomialRing(_field(reference), [f'u{i}' for i in range(len(triples))] + ['t'])
    *us, t = ring.gens()
    var = dict(zip(triples, us, strict=True))
    equations = _gauge_equations(reference, target, var)
    if equations is None:
        return None
    ideal = ring.ideal([t * prod(us) - 1, *equations])
    if ideal.dimension() < 0:
        return None
    for u in us:
        if ideal.dimension() == 0:
            break
        # spend gauge freedom that fixes the data
        fixed = ideal + ring.ideal([u - 1])
        if fixed.dimension() >= 0:
            ideal = fixed
    solutions = ideal.variety()
    if not solutions:
        return None
    solution = solutions[0]
    return {key: solution[v] for key, v in var.items() if solution[v] != 1}


def _gauge_equations(reference: Fusion, target: Fusion, var: dict[Triple, FieldElement]) -> list[FieldElement] | None:
    """Return the polynomial equations on the gauge unknowns, or `None` if the target is nonzero where inadmissible."""
    equations = []
    for key in itertools.product(range(reference.size), repeat=6):
        a, b, c, d, e, f = key
        if reference.f(*key) == 0 and target.f(*key) == 0:
            continue
        if not (reference.n(a, b, e) and reference.n(e, c, d) and reference.n(b, c, f) and reference.n(a, f, d)):
            return None
        lhs = target.f(*key) * var[(b, c, f)] * var[(a, f, d)]
        equations.append(lhs - var[(a, b, e)] * var[(e, c, d)] * reference.f(*key))
    for (a, b, c), u in var.items():
        equations.append(target.r(a, b, c) * u - var[(b, a, c)] * reference.r(a, b, c))
    return equations


def gauge_mismatch(reference: Fusion, target: Fusion) -> str:
    """Return a report on how the target's F- and R-symbols differ from the reference's, and the gauge relating them.

    Args:
        reference: The data in Sage's gauge.
        target: The data in the goal's gauge.

    Returns:
        The report: the differing symbols, then the gauge (or that none exists in the field: then the target is a
        different category, or needs a field extension).

    Examples:
        >>> fib = fibonacci()
        >>> print(gauge_mismatch(fib, gauge_transform(fib, {(1, 1, 1): 2})).splitlines()[-1])
        gauge: u[(1, 1, 1)] = 2
    """
    lines = []
    for key in itertools.product(range(reference.size), repeat=6):
        if reference.f(*key) != target.f(*key):
            lines.append(f'F{key}: reference {reference.f(*key)}, target {target.f(*key)}')
    for key in _admissible_triples(reference):
        if reference.r(*key) != target.r(*key):
            lines.append(f'R{key}: reference {reference.r(*key)}, target {target.r(*key)}')
    if not lines:
        return 'the data agree: no gauge transformation needed'
    u = find_gauge(reference, target)
    if u is None:
        lines.append('no gauge in the field relates them: a different category, or a gauge over a field extension')
    else:
        lines.append('gauge: ' + ', '.join(f'u[{key}] = {value}' for key, value in sorted(u.items())))
    return '\n'.join(lines)


def gauge_facts(reference: Fusion, target: Fusion, u: Gauge) -> Lean:
    """Return the fact that the target is the reference in the gauge `u`, checked in Sage, then by the kernel.

    Args:
        reference: The data in Sage's gauge.
        target: The data in the goal's gauge.
        u: The gauge (from `find_gauge`).

    Returns:
        The fact `hgauge : ∀ K ζ, ζ ^ m = r → FusionData.GaugeRelated (E.toData ζ) (E'.toData ζ) u uinv`.

    Raises:
        CertificateError: If `u` does not relate the data.
    """
    failure = _gauge_failure(reference, target, u)
    if failure is not None:
        raise CertificateError(failure)
    m, r, _ = FIELDS[reference.field]
    gauge = gauge_term(u, reference)
    inverse = gauge_term(u, reference, inverse=True)
    return tactic(
        f'have hgauge : ∀ {{K : Type}} [CommRing K] [Algebra ℚ K] (ζ : K), ζ ^ {m} = algebraMap ℚ K ({r}) →\n'
        f'    FusionData.GaugeRelated (FusionData.RepData.toData {fusion_data_term(reference)} ζ)\n'
        f'      (FusionData.RepData.toData {fusion_data_term(target)} ζ)\n'
        f'      (fun a b c => FusionData.Coeffs.eval ζ (({gauge}) a b c))\n'
        f'      (fun a b c => FusionData.Coeffs.eval ζ (({inverse}) a b c)) :=\n'
        f'  fun _ hζ => FusionData.RepData.gaugeRelated (m := {m}) (r := {r}) hζ\n'
        '    (by set_option maxRecDepth 100000 in decide +kernel)',
    )


Builder = Callable[[], Fusion]
KNOWN: dict[str, Builder] = {'fibonacci': fibonacci, 'ising': ising}
