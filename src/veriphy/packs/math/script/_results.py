"""What a script returns: `found(...)`, `refuted(...)` or `unknown(reason)`, which its verb turns into a status.

A script declares `SCRIPT = {'name': …, 'serves': …, 'inputs': {…}}` and defines `run(goal, inputs)`, where `goal` is
the goal proposition (as `problem.goal`) and `inputs` the values the caller gave; the whole `problem` and its parts
(`lhs`, `rhs`, `hyps`, …) are bound as before. For `certify`, `found` carries the proof (a Lean tactic, as
text or a `Lean` value); for `test`, the list of instances.
"""

from dataclasses import dataclass, field

from veriphy.packs.math.script._problem import Hyp

# the goal proposition: `goal.poly`, `goal.rel`, `goal.text`, `goal.expr`; `None` for a goal with no such form
Goal = Hyp | None


@dataclass(frozen=True)
class Found:
    """The script found what its verb needs.

    Args:
        value: The proof, the instances, or another artifact of the verb.
    """

    value: object


@dataclass(frozen=True)
class Refuted:
    """The script found the goal false.

    Args:
        values: Each universal binder's value, as Sage text, at which the goal fails.
        note: What was evaluated there, for the reader.
    """

    values: dict[str, str]
    note: str = ''


@dataclass(frozen=True)
class Unknown:
    """The script found nothing.

    Args:
        reason: Why, for the reader.
        details: Anything the reader may want, such as the candidates tried.
    """

    reason: str
    details: dict[str, object] = field(default_factory=dict)


Result = Found | Refuted | Unknown


def found(value: object) -> Found:
    """Return that the script found `value`, the artifact its verb needs.

    Args:
        value: The artifact.

    Returns:
        The result.

    Examples:
        >>> found('nlinarith [sq_nonneg (a - b)]').value
        'nlinarith [sq_nonneg (a - b)]'
    """
    return Found(value)


def refuted(values: dict[str, object], note: str = '') -> Refuted:
    """Return that the goal is false at `values`.

    Args:
        values: Each universal binder's value.
        note: What was evaluated there.

    Returns:
        The result, its values as Sage text.

    Examples:
        >>> refuted({'x': 2}).values
        {'x': '2'}
    """
    return Refuted({name: str(value) for name, value in values.items()}, note)


def unknown(reason: str, **details: object) -> Unknown:
    """Return that the script found nothing, and why.

    Args:
        reason: Why.
        **details: Anything else the reader may want.

    Returns:
        The result.

    Examples:
        >>> unknown('no certificate of degree 4').reason
        'no certificate of degree 4'
    """
    return Unknown(reason, dict(details))


def show_values(values: dict[str, str]) -> str:
    """Return values as `x := 1, y := 1/2`, as Lean reports them.

    Args:
        values: Each binder's value, as Sage text.

    Returns:
        The values, joined.

    Examples:
        >>> show_values({'x': '1', 'y': '1/2'})
        'x := 1, y := 1/2'
    """
    return ', '.join(f'{name} := {value}' for name, value in values.items())
