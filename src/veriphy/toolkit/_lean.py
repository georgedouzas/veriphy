"""Represent Lean text and render Sage values as Lean terms over a problem's atoms."""

import dataclasses
import re
from dataclasses import dataclass

from sage.all import QQ
from sage.rings.polynomial.multi_polynomial import MPolynomial

from veriphy.core import VeriphyError
from veriphy.toolkit._problem import Problem

KINDS = ('term', 'tactic')
ATOMIC = re.compile(r"[^\W\d][\w'.₀-₉]*")


@dataclass(frozen=True)
class Lean:
    """Hold a piece of Lean source text and its syntactic category.

    Args:
        text: The Lean source.
        kind: `term` or `tactic`.
        leaves_goals: Whether the tactic deliberately leaves goals open for the next tactic (a rewrite step).

    Examples:
        >>> Lean('ring1', 'tactic')
        Lean(text='ring1', kind='tactic', leaves_goals=False)
    """

    text: str
    kind: str
    leaves_goals: bool = False

    def __post_init__(self) -> None:
        """Reject an unknown syntactic category."""
        if self.kind not in KINDS:
            message = f'Lean text kind must be one of {list(KINDS)}, got {self.kind!r}'
            raise VeriphyError(message)

    def __str__(self) -> str:
        """Return the Lean source."""
        return self.text


def term(text: str) -> Lean:
    """Wrap Lean source as a term.

    Args:
        text: The Lean source of a term.

    Returns:
        The term.

    Examples:
        >>> str(term('h1'))
        'h1'
    """
    return Lean(text, 'term')


def tactic(text: str) -> Lean:
    """Wrap Lean source as a tactic.

    Args:
        text: The Lean source of a tactic or tactic block.

    Returns:
        The tactic.

    Examples:
        >>> tactic('norm_num').kind
        'tactic'
    """
    return Lean(text, 'tactic')


def leaving_goals(block: Lean) -> Lean:
    """Mark a tactic as leaving goals open on purpose, for the user's next tactic.

    `sage_run` refuses a block that leaves goals unless it is marked; a marked block's open goals stay.

    Args:
        block: The tactic.

    Returns:
        The same tactic, marked.

    Examples:
        >>> leaving_goals(tactic('rw [h]')).leaves_goals
        True
    """
    return dataclasses.replace(block, leaves_goals=True)


def parenthesize(text: str) -> str:
    """Return Lean text wrapped in parentheses unless it is a single identifier or numeral.

    Args:
        text: The Lean source.

    Returns:
        The text, safe to use as an operand.

    Examples:
        >>> parenthesize('f a'), parenthesize('v₁'), parenthesize('↑n')
        ('(f a)', 'v₁', '(↑n)')
    """
    if ATOMIC.fullmatch(text) or text.isdigit():
        return text
    return f'({text})'


def rational(q: object) -> Lean:
    """Render an exact rational as a Lean numeral term.

    Args:
        q: Anything Sage converts exactly to a rational.

    Returns:
        `n`, `-n`, `n / d` or `-(n / d)`.

    Examples:
        >>> [str(rational(x)) for x in (3, -3, QQ(3) / 2, QQ(-3) / 2)]
        ['3', '-3', '3 / 2', '-(3 / 2)']
    """
    value = QQ(q)
    numerator, denominator = abs(value.numerator()), value.denominator()
    base = str(numerator) if denominator == 1 else f'{numerator} / {denominator}'
    if value >= 0:
        return term(base)
    return term(f'-{base}' if denominator == 1 else f'-({base})')


def _render_monomial(exponents: tuple[int, ...], names: list[str], problem: Problem) -> str:
    """Return a monomial as a product of powers of atoms, empty for the constant monomial."""
    factors = []
    for name, e in zip(names, exponents, strict=True):
        if e == 0:
            continue
        atom = parenthesize(problem.atoms.get(name, name))
        factors.append(atom if e == 1 else f'{atom} ^ {e}')
    return ' * '.join(factors)


def polynomial(p: object, problem: Problem) -> Lean:
    """Render a polynomial of the problem's ring as a Lean term over the atoms' text.

    Args:
        p: A polynomial in `problem.ring`, or anything the ring converts.
        problem: The problem whose atoms name the variables.

    Returns:
        The term, `0` for the zero polynomial.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0', 'x1'], 'atoms': ['f a', 'b'], 'goal': {'kind': 'false'}})
        >>> str(polynomial('2*x0^2 - x0*x1/3', prob))
        '2 * (f a) ^ 2 - 1 / 3 * (f a) * b'
    """
    poly: MPolynomial = problem.ring(p)
    if poly == 0:
        return term('0')
    names = [str(g) for g in problem.ring.gens()]
    text = ''
    for exponents, coeff in sorted(poly.dict().items(), reverse=True):
        mono = _render_monomial(tuple(exponents), names, problem)
        value = QQ(coeff)
        magnitude = str(rational(abs(value)))
        body = mono if mono and abs(value) == 1 else ' * '.join(part for part in (magnitude, mono) if part)
        if not text:
            text = f'-{body}' if value < 0 else body
        else:
            text += f" {'-' if value < 0 else '+'} {body}"
    return term(text)
