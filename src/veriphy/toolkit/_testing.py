"""Test instances for `sage_test`: values chosen by a script, checked by the kernel or evaluated by Sage.

When no recipe can build a certificate for a claim `∀ x, P x`, `sage_test` tests it: the script chooses instances, a
kernel instance carries a proof of `P v` that Lean checks by computation alone, and an oracle instance carries Sage's
exact (or interval, at least 53 bits) evaluation of `P v`. Floating-point comparisons are refused, since they prove
nothing about the exact statement.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from sage.all import CDF, QQ, RDF, RR, ZZ, RealIntervalField, identity_matrix, matrix, zero_matrix
from sage.matrix.matrix0 import Matrix
from sage.rings.real_mpfi import RealIntervalFieldElement
from sage.structure.element import RingElement

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean

# the least precision an interval evaluation may use
MIN_PRECISION = 53
RELATIONS = ('==', '<', '<=', '>', '>=')


@dataclass(frozen=True)
class Instance:
    """One instance of a tested claim.

    Args:
        values: The Lean text of each binder's value, in the binders' order.
        proof: For a kernel instance, the tactic block proving the instantiated claim.
        verdict: For an oracle instance, whether Sage's evaluation satisfies the claim.
        evaluation: For an oracle instance, the values compared, as text (with the precision of an interval).
        edge: Whether the instance is an edge case (zero, one, the identity, a singular matrix, a degenerate size).
    """

    values: tuple[str, ...]
    proof: str | None = None
    verdict: bool | None = None
    evaluation: str = ''
    edge: bool = False

    @property
    def kind(self) -> str:
        """Return `kernel` or `oracle`."""
        return 'kernel' if self.proof is not None else 'oracle'

    def to_json(self) -> dict[str, object]:
        """Return the instance as the daemon sends it to Lean."""
        data: dict[str, object] = {'values': list(self.values), 'kind': self.kind, 'edge': self.edge}
        if self.proof is not None:
            data['proof'] = self.proof
        else:
            data['verdict'] = self.verdict
            data['evaluation'] = self.evaluation
        return data


def kernel_instance(*values: object, proof: Lean | str, edge: bool = False) -> Instance:
    """Return an instance the kernel checks: the claim at the values, with a proof by computation.

    Args:
        *values: The binders' values, as Lean text (or Sage values rendered with `str`).
        proof: The tactic block proving the instantiated claim.
        edge: Whether the instance is an edge case.

    Returns:
        The instance.

    Examples:
        >>> kernel_instance('0', proof='norm_num', edge=True).to_json()
        {'values': ['0'], 'kind': 'kernel', 'edge': True, 'proof': 'norm_num'}
    """
    text = proof.text if isinstance(proof, Lean) else proof
    return Instance(tuple(str(v) for v in values), proof=text, edge=edge)


def _floating(x: object) -> bool:
    """Return whether a value is a floating-point number (or a matrix or vector of them)."""
    if isinstance(x, float | complex):
        return True
    parent = getattr(x, 'parent', None)
    if parent is None:
        return False
    p = parent()
    base = getattr(p, 'base_ring', None)
    rings = {RDF, CDF, RR}
    if p in rings or (base is not None and base() in rings):
        return True
    name = type(p).__name__
    return 'RealField' in name and 'Interval' not in name


def _interval_precision(x: object) -> int | None:
    """Return the precision of an interval value, `None` for an exact one."""
    if isinstance(x, RealIntervalFieldElement):
        return int(x.prec())
    return None


def oracle_instance(
    *values: object,
    lhs: RingElement,
    rhs: RingElement,
    relation: str = "==",
    edge: bool = False,
) -> Instance:
    """Return an instance Sage evaluates: the claim's two sides at the values, compared exactly or by intervals.

    Exact values (rationals, number fields, exact symbolic expressions, matrices over them) are compared exactly.
    Intervals (`RealIntervalField`, at least 53 bits) satisfy `==` when they overlap and an inequality when it holds
    for every point. Floating-point values are refused.

    Args:
        *values: The binders' values, as Lean text.
        lhs: Sage's value of the claim's left side.
        rhs: Sage's value of the right side.
        relation: One of `==`, `<`, `<=`, `>`, `>=`.
        edge: Whether the instance is an edge case.

    Returns:
        The instance.

    Raises:
        CertificateError: For floating-point values, a precision below 53 bits, or an unknown relation.

    Examples:
        >>> oracle_instance('2', lhs=QQ(4), rhs=QQ(2) ** 2).verdict
        True
        >>> try:
        ...     oracle_instance('2', lhs=RDF(4), rhs=RDF(4))
        ... except CertificateError as exc:
        ...     print(exc)
        the instance at ['2']: floating-point values cannot decide it; use exact or interval ones
    """
    if relation not in RELATIONS:
        message = f'unknown relation {relation!r}; use one of {list(RELATIONS)}'
        raise CertificateError(message)
    if _floating(lhs) or _floating(rhs):
        shown = [str(v) for v in values]
        message = f'the instance at {shown}: floating-point values cannot decide it; use exact or interval ones'
        raise CertificateError(message)
    precisions = [q for q in (_interval_precision(lhs), _interval_precision(rhs)) if q is not None]
    if any(q < MIN_PRECISION for q in precisions):
        message = f'interval evaluations need at least {MIN_PRECISION} bits, got {min(precisions)}'
        raise CertificateError(message)
    if precisions:
        field = RealIntervalField(min(precisions))
        a, b = field(lhs), field(rhs)
        verdict = {
            '==': a.overlaps(b),
            '<': bool(a < b),
            '<=': bool(a <= b),
            '>': bool(a > b),
            '>=': bool(a >= b),
        }[relation]
        evaluation = f'{a.str(style="brackets")} {relation} {b.str(style="brackets")} at {min(precisions)} bits'
    else:
        difference = lhs - rhs
        if relation == '==':
            verdict = bool(difference == 0)
        else:
            verdict = {'<': bool(lhs < rhs), '<=': bool(lhs <= rhs), '>': bool(lhs > rhs), '>=': bool(lhs >= rhs)}[
                relation
            ]
        evaluation = f'{lhs} {relation} {rhs} (exact)'
    return Instance(tuple(str(v) for v in values), verdict=verdict, evaluation=evaluation, edge=edge)


class Sampler:
    """Seeded random values for test instances, with the edge cases of the common binder types.

    Args:
        seed: The seed; the test record keeps it, so a run is reproducible.

    Examples:
        >>> s = Sampler(7)
        >>> s.rational() == Sampler(7).rational()
        True
    """

    def __init__(self, seed: int = 0) -> None:
        self.seed = int(seed)
        self._random = np.random.default_rng(self.seed)

    def integer(self, low: int = -5, high: int = 5) -> object:
        """Return an integer in `[low, high]`."""
        return ZZ(int(self._random.integers(low, high + 1)))

    def rational(self, height: int = 5) -> object:
        """Return a rational with numerator and denominator bounded by `height`."""
        return QQ(int(self._random.integers(-height, height + 1))) / int(self._random.integers(1, height + 1))

    def matrix(self, rows: int, cols: int | None = None, height: int = 5) -> Matrix:
        """Return a rational matrix with small entries."""
        cols = rows if cols is None else cols
        return matrix(QQ, rows, cols, [self.rational(height) for _ in range(rows * cols)])

    @staticmethod
    def edge_matrices(rows: int, cols: int | None = None) -> list[Matrix]:
        """Return the edge cases of a matrix type: zero, a rank-one matrix, and the identity when square."""
        cols = rows if cols is None else cols
        cases = [zero_matrix(QQ, rows, cols)]
        if rows and cols:
            cases.append(matrix(QQ, rows, cols, lambda i, j: (i + 1) * (j + 1)))
        if rows == cols:
            cases.append(identity_matrix(QQ, rows))
        return cases


def lean_rational_matrix(m: Matrix) -> str:
    """Return a rational matrix as a typed Lean literal, `(0 : Matrix (Fin 0) (Fin 0) ℚ)` for an empty one.

    Args:
        m: The matrix.

    Returns:
        The Lean text.

    Examples:
        >>> lean_rational_matrix(matrix(QQ, [[1, 2]]))
        '(!![1, 2] : Matrix (Fin 1) (Fin 2) ℚ)'
    """
    kind = f'Matrix (Fin {m.nrows()}) (Fin {m.ncols()}) ℚ'
    if m.nrows() == 0 or m.ncols() == 0:
        return f'(0 : {kind})'
    rows = '; '.join(', '.join(_q(x) for x in row) for row in m.rows())
    return f'(!![{rows}] : {kind})'


def _q(x: object) -> str:
    """Return a rational as Lean text."""
    q = QQ(x)
    return str(q) if q.denominator() == 1 else f'({q.numerator()} / {q.denominator()})'


def check_instances(instances: Sequence[object], binders: int) -> list[Instance]:
    """Return a script's instances, checked to give a value to every binder.

    Args:
        instances: What the script assigned to `instances`.
        binders: The number of universal binders of the claim.

    Returns:
        The instances.

    Raises:
        CertificateError: If an instance is not an `Instance` or has the wrong number of values.
    """
    checked = []
    for k, instance in enumerate(instances):
        if not isinstance(instance, Instance):
            message = f'instance {k} is not built with kernel_instance or oracle_instance'
            raise CertificateError(message)
        if len(instance.values) != binders:
            message = f'instance {k} gives {len(instance.values)} values for {binders} binders'
            raise CertificateError(message)
        checked.append(instance)
    return checked


SCALARS = ('ℕ', 'ℤ', 'ℚ', 'ℝ')
MATRIX = re.compile(r'^Matrix \(Fin (\w+)\) \(Fin (\w+)\) (ℚ|ℝ)$')


def _scalar_cases(kind: str, sampler: Sampler) -> list[tuple[str, bool]]:
    """Return values of a scalar type, edge cases first."""
    if kind == 'ℕ':
        return [('0', True), ('1', True), (str(sampler.integer(2, 4)), False)]
    if kind == 'ℤ':
        return [('0', True), ('1', True), (str(sampler.integer(-5, -1)), False)]
    return [('0', True), ('1', True), (_q(sampler.rational()), False)]


def default_cases(
    universal: Sequence[tuple[str, str]],
    sampler: Sampler,
    count: int = 4,
) -> list[tuple[list[str], bool]]:
    """Return instances for a claim's binders: edge cases (zero, one, a degenerate size, a singular matrix) and samples.

    Binders are scalars (`ℕ`, `ℤ`, `ℚ`, `ℝ`) or matrices `Matrix (Fin a) (Fin b) K` whose sizes are numerals or earlier
    `ℕ` binders. Each instance is a list of Lean texts with whether it is an edge case.

    Args:
        universal: The claim's binders (`universal` in a test script).
        sampler: The seeded sampler.
        count: How many instances to return, at most.

    Returns:
        The instances.

    Raises:
        CertificateError: If a binder has another type; list the instances by hand then.

    Examples:
        >>> cases = default_cases([('n', 'ℕ'), ('A', 'Matrix (Fin n) (Fin n) ℚ')], Sampler(0))
        >>> cases[0]
        (['0', '(0 : Matrix (Fin 0) (Fin 0) ℚ)'], True)
        >>> len(cases), any(edge for _, edge in cases)
        (4, True)
    """
    partial: list[tuple[list[str], dict[str, int], bool]] = [([], {}, False)]
    for name, kind in universal:
        extended = []
        for values, sizes, edge in partial:
            if kind in SCALARS:
                for text, is_edge in _scalar_cases(kind, sampler):
                    new_sizes = {**sizes, name: int(text)} if kind == 'ℕ' else sizes
                    extended.append(([*values, text], new_sizes, edge or is_edge))
                continue
            match = MATRIX.match(kind)
            if match is None:
                message = f"no default instances for the binder {name} : {kind}; list CASES by hand"
                raise CertificateError(message)
            rows, cols = (int(d) if d.isdigit() else sizes.get(d) for d in match.groups()[:2])
            if rows is None or cols is None:
                message = f'the size of {name} : {kind} is not a numeral or an earlier ℕ binder'
                raise CertificateError(message)
            for m in [*Sampler.edge_matrices(rows, cols), sampler.matrix(rows, cols)]:
                singular = rows != cols or rows == 0 or m.det() == 0
                extended.append(([*values, lean_rational_matrix(m)], sizes, edge or singular))
        partial = extended
    cases = [(values, edge) for values, _, edge in partial]
    edges = [c for c in cases if c[1]]
    others = [c for c in cases if not c[1]]
    return (edges[:1] + others + edges[1:])[:count]
