"""Bind a serialized Lean problem to Sage objects."""

from dataclasses import dataclass, field
from typing import NamedTuple

from sage.all import QQ, PolynomialRing
from sage.rings.polynomial.multi_polynomial import MPolynomial
from sage.rings.polynomial.multi_polynomial_ring_base import MPolynomialRing_base

from veriphy.core import RELATIONS, CertificateError, ParamError

GOAL_KINDS = ('rel', 'false', 'exists', 'other')


def create_ring(names: list[str]) -> MPolynomialRing_base:
    """Create the multivariate polynomial ring QQ[names], multivariate even for one name.

    Args:
        names: The variable names, valid identifiers.

    Returns:
        The polynomial ring.

    Examples:
        >>> create_ring(['x0', 'x1']).gens()
        (x0, x1)
    """
    return PolynomialRing(QQ, len(names), names)


def parse_polynomial(ring: MPolynomialRing_base, s: object, *, param: str) -> MPolynomial:
    """Parse a polynomial string in `ring`.

    Args:
        ring: The polynomial ring.
        s: The polynomial, written in Sage syntax.
        param: The request parameter the string came from, named in errors.

    Returns:
        The polynomial.

    Raises:
        ParamError: If `s` is not a string or not a polynomial in `ring`.

    Examples:
        >>> parse_polynomial(create_ring(['x0']), 'x0^2 - 1/2', param='poly')
        x0^2 - 1/2
    """
    if not isinstance(s, str):
        raise ParamError(param=param, reason='must be a polynomial string')
    try:
        return ring(s)
    except (TypeError, ValueError, SyntaxError, NameError) as exc:
        gens = ', '.join(map(str, ring.gens()))
        raise ParamError(param=param, reason=f'not a polynomial in QQ[{gens}]: {s!r} ({exc})') from exc


class Hyp(NamedTuple):
    """Hold one hypothesis or goal of a problem, as scripts see it.

    Args:
        name: The Lean hypothesis name, or `None` for the goal and existential body.
        poly: The polynomial `p` of the constraint `p rel 0`, or `None` when it has no polynomial form.
        rel: The relation tag, one of `eq`, `le`, `lt`, `ne`, or `None` without a polynomial form.
        text: The Lean text of the proposition.
    """

    name: str | None
    poly: MPolynomial | None
    rel: str | None
    text: str = ''


@dataclass
class Problem:
    """Hold a serialized Lean problem bound to Sage objects.

    Args:
        ring: The polynomial ring over the problem's atoms.
        hyps: The hypotheses.
        goal_kind: One of `rel`, `false`, `exists` and `other`.
        goal: The goal of a `rel` or `other` goal, with its Lean text.
        binders: The generators bound by an `exists` goal.
        body: The constraints of an `exists` goal.
        atoms: The Lean text of each variable, by variable name.
    """

    ring: MPolynomialRing_base
    hyps: list[Hyp]
    goal_kind: str
    goal: Hyp | None = None
    binders: list[MPolynomial] = field(default_factory=list)
    body: list[Hyp] = field(default_factory=list)
    atoms: dict[str, str] = field(default_factory=dict)

    def find_hyp(self, name: str, allowed: tuple[str, ...], family: str) -> Hyp:
        """Find the hypothesis named `name`, checking its relation is usable by `family`.

        Args:
            name: The hypothesis name.
            allowed: The relation tags `family` accepts.
            family: The proof shape asking, named in errors.

        Returns:
            The hypothesis.

        Raises:
            CertificateError: If no hypothesis has that name, or its relation is not in `allowed`.
        """
        by_name = {h.name: h for h in self.hyps}
        if name not in by_name:
            message = f"certificate names unknown hypothesis '{name}' (known: {sorted(map(str, by_name))})"
            raise CertificateError(message)
        hyp = by_name[name]
        if hyp.rel not in allowed:
            message = f"hypothesis '{name}' has relation '{hyp.rel}', not usable by {family}"
            raise CertificateError(message)
        return hyp

    def to_namespace(self) -> dict[str, object]:
        """Return the names a script sees.

        Returns:
            `problem`, `R`, the generators by name, `hyps`, `goal`, `goal_kind`, `binders`, `body`, `atoms` and
            `Hyp`.
        """
        names: dict[str, object] = {
            'problem': self,
            'R': self.ring,
            'Hyp': Hyp,
            'hyps': self.hyps,
            'goal': self.goal,
            'goal_kind': self.goal_kind,
            'binders': self.binders,
            'body': self.body,
            'atoms': self.atoms,
        }
        names.update({str(g): g for g in self.ring.gens()})
        return names


def _read_constraint(item: object, where: str, ring: MPolynomialRing_base) -> Hyp:
    """Return one serialized hypothesis or goal as a `Hyp`, with or without a polynomial form."""
    if not isinstance(item, dict):
        raise ParamError(param='problem', reason=f'{where}: must be an object')
    text = str(item.get('text', ''))
    if item.get('poly') is None:
        return Hyp(item.get('name'), None, None, text)
    rel = item.get('rel')
    if rel not in RELATIONS:
        raise ParamError(param='problem', reason=f'{where}: bad relation {rel!r}')
    return Hyp(item.get('name'), parse_polynomial(ring, item.get('poly'), param='problem'), str(rel), text)


def _read_constraints(items: object, where: str, ring: MPolynomialRing_base) -> list[Hyp]:
    """Return a serialized list of constraints as `Hyp`s, empty for anything that is not a list."""
    return [_read_constraint(h, f'{where} {i}', ring) for i, h in enumerate(items if isinstance(items, list) else [])]


def _read_names(problem: dict[str, object]) -> list[str]:
    """Return the problem's variable names, or a single placeholder name for a problem without atoms."""
    names = problem.get('vars') or []
    if not isinstance(names, list) or not all(isinstance(n, str) and n.isidentifier() for n in names):
        raise ParamError(param='problem', reason="'vars' must be a list of identifiers")
    return names or ['x0']


def read_problem(problem: object) -> Problem:
    """Bind a serialized Lean problem to Sage objects.

    Args:
        problem: The problem as `Veriphy.Problem.toJson` serializes it.

    Returns:
        The bound problem.

    Raises:
        ParamError: If the serialization is malformed.

    Examples:
        >>> bound = read_problem({'vars': ['x0'], 'atoms': ['x'],
        ...     'hyps': [{'name': 'h', 'poly': 'x0 - 1', 'rel': 'le', 'text': 'x ≤ 1'},
        ...              {'name': 'hs', 'text': 'Real.sin x ≤ 1'}],
        ...     'goal': {'kind': 'other', 'text': 'Real.cos x ≤ 1'}})
        >>> [(h.name, h.poly, h.rel) for h in bound.hyps]
        [('h', x0 - 1, 'le'), ('hs', None, None)]
        >>> bound.goal.text
        'Real.cos x ≤ 1'
    """
    if not isinstance(problem, dict):
        raise ParamError(param='problem', reason='must be an object')
    names = _read_names(problem)
    ring = create_ring(names)
    goal = problem.get('goal') or {'kind': 'false'}
    goal = goal if isinstance(goal, dict) else {}
    kind = str(goal.get('kind'))
    if kind not in GOAL_KINDS:
        raise ParamError(param='problem', reason=f'unknown goal kind {kind!r}')
    atoms = problem.get('atoms', [])
    bound = Problem(
        ring=ring,
        hyps=_read_constraints(problem.get('hyps', []), 'constraint', ring),
        goal_kind=kind,
        atoms={n: str(a) for n, a in zip(names, atoms if isinstance(atoms, list) else [], strict=False)},
    )
    if kind in ('rel', 'other'):
        bound.goal = _read_constraint({**goal, 'name': None}, 'goal', ring)
    elif kind == 'exists':
        bound.binders = list(ring.gens()[: int(str(goal.get('binders', 0)))])
        bound.body = _read_constraints(goal.get('body', []), 'body', ring)
    return bound
