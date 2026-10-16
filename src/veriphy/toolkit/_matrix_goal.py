"""Matrix goals read from the goal itself: identities, determinants and traces, also modulo side relations.

Sage evaluates `lhs - rhs` from the goal's own matrices. Lean proves a matrix or vector identity entry by entry, and a
determinant or trace by expanding it (Laplace expansion along the first row for any size, the trace as a sum). Entries
that involve `cosh` and `sinh`, `cos` and `sin`, or square roots are equal only modulo identities such as
`cosh² - sinh² = 1`: Sage reduces each entry modulo the named relation lemmas and closes it by `linear_combination` of
the lemmas, with the cofactors of a Gröbner lift.
"""

import operator
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from sage.all import QQ, SR, PolynomialRing, cos, cosh, function, sin, sinh, sqrt
from sage.matrix.matrix0 import Matrix
from sage.symbolic.expression import Expression
from sage.symbolic.operators import add_vararg, mul_vararg

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic
from veriphy.toolkit._problem import Hyp, Problem, parse_symbolic
from veriphy.toolkit._symbolic_emit import symbolic

ENTRY_SIMP = ('Matrix.mul_apply', 'Matrix.transpose_apply', 'Matrix.one_apply', 'Fin.sum_univ_succ')
VECTOR_SIMP = ('Matrix.mulVec', 'Matrix.vecMul', 'dotProduct', 'Fin.sum_univ_succ')
SCALAR_SIMP = (
    'Matrix.det_succ_row_zero',
    'Matrix.trace',
    'Fin.sum_univ_succ',
    'Fin.succAbove_of_castSucc_lt',
    'Fin.succAbove_of_le_castSucc',
    'Matrix.mul_apply',
    'Matrix.transpose_apply',
)


REAL = {'sqrt': sqrt, 'cosh': cosh, 'sinh': sinh, 'cos': cos, 'sin': sin}
# the same functions as opaque symbols: Sage keeps `sqrt(2)^2` and `cosh(u)^2 - sinh(u)^2` as written, like `ring1`
OPAQUE = {name: function(name) for name in REAL}


@dataclass(frozen=True)
class Relation:
    """A side relation `lhs = rhs`, as a Lean lemma applied at an argument.

    Args:
        kernels: The functions whose arguments instantiate it (`cosh`, `sqrt`).
        difference: `lhs - rhs` at an argument, in Sage, given the functions by name.
        lean: The Lean proof of `lhs = rhs` at an argument, given the argument's text.
    """

    kernels: tuple[str, ...]
    difference: Callable[[Expression, Mapping[str, Callable[[Expression], Expression]]], Expression]
    lean: Callable[[str], str]


SIDE_RELATIONS: dict[str, Relation] = {
    'Real.cosh_sq_sub_sinh_sq': Relation(
        ('cosh', 'sinh'),
        lambda t, f: f['cosh'](t) ** 2 - f['sinh'](t) ** 2 - 1,
        lambda t: f'Real.cosh_sq_sub_sinh_sq {t}',
    ),
    'Real.cos_sq_add_sin_sq': Relation(
        ('cos', 'sin'),
        lambda t, f: f['cos'](t) ** 2 + f['sin'](t) ** 2 - 1,
        lambda t: f'Real.cos_sq_add_sin_sq {t}',
    ),
    'Real.sin_sq_add_cos_sq': Relation(
        ('sin', 'cos'),
        lambda t, f: f['sin'](t) ** 2 + f['cos'](t) ** 2 - 1,
        lambda t: f'Real.sin_sq_add_cos_sq {t}',
    ),
    'Real.sq_sqrt': Relation(
        ('sqrt',),
        lambda a, f: f['sqrt'](a) ** 2 - a,
        lambda a: f'Real.sq_sqrt (show (0 : ℝ) ≤ {a} by positivity)',
    ),
}


def _real(e: Expression) -> Expression:
    """Return an expression with its opaque functions replaced by Sage's own."""
    for name, f in OPAQUE.items():
        e = e.substitute_function(f, REAL[name])
    return e


def _kernel_name(e: Expression) -> str | None:
    """Return the name of an opaque function application, `None` for anything else."""
    op = e.operator()
    name = op.name() if op is not None and hasattr(op, 'name') else None
    return name if name in OPAQUE else None


def _kernels(e: Expression, found: set[Expression]) -> None:
    """Collect the non-polynomial subterms of `e`: function applications and fractional powers."""
    if e.is_symbol() or (e.is_numeric() and e in QQ):
        return
    op = e.operator()
    if op in (add_vararg, mul_vararg):
        for a in e.operands():
            _kernels(a, found)
        return
    if op == operator.pow and e.operands()[1] in QQ and QQ(e.operands()[1]).denominator() == 1:
        _kernels(e.operands()[0], found)
        return
    found.add(e)


def _argument(e: Expression) -> Expression:
    """Return the argument of a kernel: the radicand of a square root, the operand of a function."""
    return e.operands()[0]


def _instances(kernels: set[Expression], names: Sequence[str]) -> list[tuple[str, Expression]]:
    """Return every relation instance the goal needs: each named relation at each argument of its kernels."""
    instances = []
    for name in names:
        if name not in SIDE_RELATIONS:
            message = f'unknown side relation {name!r}; the known ones are {sorted(SIDE_RELATIONS)}'
            raise CertificateError(message)
        relation = SIDE_RELATIONS[name]
        arguments = {_argument(k) for k in kernels if _kernel_name(k) in relation.kernels}
        instances += [(name, t) for t in sorted(arguments, key=str)]
    return instances


def _entries(e: Expression | Matrix) -> list[Expression]:
    """Return the entries of a matrix difference, or the scalar difference as one entry."""
    return [SR(x) for x in e.list()] if hasattr(e, 'nrows') else [SR(e)]


def _combinations(entries: Sequence[Expression], relations: Sequence[str], problem: Problem) -> list[str] | None:
    """Return the `linear_combination` arguments closing each entry modulo the relations; `None` if they are all 0."""
    # zero as polynomials in the goal's atoms and function values, which is what `ring1` proves
    if all(x.expand().is_trivial_zero() for x in entries):
        return None
    if not relations:
        if all(bool(_real(x).simplify_full() == 0) for x in entries):
            message = (
                'the entries vanish only by identities of their functions; name the identities in RELATIONS, '
                f'among {sorted(SIDE_RELATIONS)}'
            )
            raise CertificateError(message)
        return []
    kernels: set[Expression] = set()
    for x in entries:
        _kernels(x.expand(), kernels)
    instances = _instances(kernels, relations)
    for name, t in instances:
        _kernels(SIDE_RELATIONS[name].difference(t, OPAQUE).expand(), kernels)
    ordered = sorted(kernels, key=str)
    generators = [SR.var(f'g{i}_') for i in range(len(ordered))]
    substitution = dict(zip(ordered, generators, strict=True))
    variables = sorted(
        {str(v) for x in entries for v in x.subs(substitution).variables()} | {str(g) for g in generators},
    )
    ring = PolynomialRing(QQ, len(variables), variables)
    back = {ring(str(g)): k for k, g in substitution.items()}
    differences = [SIDE_RELATIONS[name].difference(t, OPAQUE).expand().subs(substitution) for name, t in instances]
    ideal = ring.ideal([ring(str(d)) for d in differences])
    texts = []
    for x in entries:
        p = ring(str(x.expand().subs(substitution)))
        if p == 0:
            continue
        if p not in ideal:
            message = f'an entry is not zero modulo the relations {list(relations)}: {_real(x).simplify_full()}'
            raise CertificateError(message)
        combination = _combination(p.lift(ideal), instances, back, problem)
        texts += [combination, f'-({combination})']
    return list(dict.fromkeys(texts))


def _combination(
    cofactors: Sequence[object],
    instances: Sequence[tuple[str, Expression]],
    back: Mapping[object, Expression],
    problem: Problem,
) -> str:
    """Return the `linear_combination` argument `Σ cᵢ hᵢ` for an entry's cofactors over the relation instances."""
    terms = []
    for c, (name, t) in zip(cofactors, instances, strict=True):
        if c == 0:
            continue
        coefficient = _real(SR(str(c)).subs({SR(str(g)): k for g, k in back.items()}))
        lemma = SIDE_RELATIONS[name].lean(str(symbolic(_real(t), problem, lean_type='ℝ')))
        terms.append(f'({symbolic(coefficient, problem, lean_type="ℝ")}) * ({lemma})')
    return ' + '.join(terms)


def _closer(combinations: Sequence[str]) -> str:
    """Return the line closing every remaining entry goal."""
    alternatives = ['ring1', '(norm_num; done)', *(f'linear_combination {c}' for c in combinations)]
    return 'all_goals first | ' + ' | '.join(alternatives)


def matrix_from_goal_proof(
    goal: Hyp | None,
    problem: Problem,
    simp: Sequence[str] = (),
    relations: Sequence[str] = (),
) -> Lean:
    """Return a proof of a matrix identity, determinant or trace read from the goal, modulo side relations.

    Args:
        goal: The goal (`goal` in a script), with `expr` its `lhs - rhs`.
        problem: The problem.
        simp: Extra simp lemmas, for example the definitions of named matrices.
        relations: Side-relation lemmas, among `Real.cosh_sq_sub_sinh_sq`, `Real.cos_sq_add_sin_sq`,
            `Real.sin_sq_add_cos_sq` and `Real.sq_sqrt`.

    Returns:
        The tactic.

    Raises:
        CertificateError: If the goal has no symbolic form, or the identity is false (modulo the relations).
    """
    if goal is None or goal.expr is None:
        message = 'the goal has no symbolic form; transcribe the matrices with the matrix_identity recipe'
        raise CertificateError(message)
    e = goal.expr
    if not all(bool(SR(x).simplify_full() == 0) for x in _entries(e)):
        message = f'the identity is false: lhs - rhs = {e.simplify_full() if hasattr(e, "simplify_full") else e}'
        raise CertificateError(message)
    opaque = parse_symbolic(goal.source, problem.symbols, functions=OPAQUE) if goal.source else None
    entries = _entries(opaque if opaque is not None else e)
    combinations = _combinations(entries, relations, problem)
    closer = _closer(combinations or [])
    if not hasattr(e, 'nrows'):
        names = ', '.join([*SCALAR_SIMP, *simp])
        return tactic(f'simp +decide [{names}]\n{closer}')
    matrix_names = ', '.join([*ENTRY_SIMP, *simp])
    vector_names = ', '.join([*VECTOR_SIMP, *simp])
    return tactic(
        'first\n'
        f'| ext i j\n  fin_cases i <;> fin_cases j <;> simp [{matrix_names}]\n  {closer}\n'
        f'| ext i\n  fin_cases i <;> simp [{vector_names}]\n  {closer}',
    )
