"""Say what a step did in plain words: what it checked, the result and why, the level and its class, the record."""

from pathlib import Path

from veriphy.core import level_trust, resolve
from veriphy.steps._runner import Result

# what each status means, said to a person
STATUS_WORDS = {
    'accepted': 'accepted',
    'refused': 'refused',
    'failed': 'failed: the tool did not finish',
    'agrees': 'agrees',
    'differs': 'differs from the claim',
    'counterexample': 'counterexample found',
    'undecided': 'undecided: no value could be tested',
    'written': 'recorded',
    'reported': 'reported',
    'conforms': 'conforms',
    'violations': 'has violations',
    'entailed': 'entailed: oo-horn accepted the derivation',
    'rejected': 'rejected: oo-horn refused the derivation',
    'unchecked': 'unchecked: no checker ran',
    'incomplete': 'incomplete: the reasoning stopped early',
    'robust': 'robust under every variation',
    'fragile': 'fragile',
}
DETAIL_LIMIT = 3


def _number(value: object) -> str:
    """Return a number to six significant digits, as a person reads it, and anything else as it is.

    Args:
        value: The value a record holds.

    Returns:
        The value as the summary shows it.

    Examples:
        >>> _number(0.09455343346738476), _number(3.5373801659773317e-10), _number([5.14, 5.18])
        ('0.0945534', '3.53738e-10', '[5.14, 5.18]')
    """
    return f'{value:.6g}' if isinstance(value, float) else str(value)


def _target(result: Result, argument: str | None) -> str:
    """Return what the step ran on: its first argument's input, relative to the working directory."""
    first = result.record.inputs.get(argument, '') if argument else ''
    if not isinstance(first, str):
        return ''
    path = Path(first)
    try:
        return str(path.relative_to(Path.cwd())) if path.is_absolute() else first
    except ValueError:
        return first


def _errors(outputs: dict[str, object]) -> list[str]:
    """Return the first errors a tool reported, each on one line with its line number when it has one."""
    found: list[str] = []
    error = outputs.get('error')
    if isinstance(error, str) and error:
        found.append(error.strip().splitlines()[0])
    errors = outputs.get('errors')
    for item in errors if isinstance(errors, list) else []:
        if isinstance(item, dict):
            text = str(item.get('message', '')).strip().splitlines()
            line = item.get('line')
            found.append(f"{f'line {line}: ' if line else ''}{text[0] if text else ''}")
    return found[:DETAIL_LIMIT]


def _details(outputs: dict[str, object]) -> list[str]:
    """Return the lines that explain a result: errors, the comparison, a counterexample, what breaks, who wrote."""
    lines = [f'why: {e}' for e in _errors(outputs)]
    if isinstance(outputs.get('result'), str):
        lines.append(f"the tool said: {outputs['result']}")
    compared = outputs.get('compared')
    if isinstance(compared, dict):
        lines.append(
            f"found {_number(compared.get('found'))}, the claim says {_number(compared.get('claimed'))} "
            f"(tolerance {_number(compared.get('tolerance'))})",
        )
    counterexample = outputs.get('counterexample')
    if isinstance(counterexample, dict):
        values = counterexample.get('values')
        at = ', '.join(f'{k} = {v}' for k, v in values.items()) if isinstance(values, dict) else values
        lines.append(
            f"at {at}: {counterexample.get('statement')} gives {counterexample.get('lhs')} and "
            f"{counterexample.get('rhs')}",
        )
    breaking = outputs.get('breaking')
    if isinstance(breaking, list) and breaking:
        lines.append('breaks under: ' + '; '.join(str(b) for b in breaking))
    violations = outputs.get('violations')
    if isinstance(violations, list) and violations:
        lines.append(f'{len(violations)} violation(s), the first: {violations[0]}')
    if isinstance(outputs.get('author'), str):
        lines.append(f"written by {outputs['author']}")
    concepts = outputs.get('concepts')
    if isinstance(concepts, dict) and concepts:
        lines.append('concepts: ' + '; '.join(f'{name} is "{label}"' for name, label in sorted(concepts.items())))
    if isinstance(outputs.get('hint'), str):
        lines.append(f"to fix: {outputs['hint']}")
    if isinstance(outputs.get('path'), str):
        lines.append(f"wrote {outputs['path']}")
    return lines


def summary(result: Result, root: Path, first: str | None = None) -> str:
    """Return what a step did, for a person.

    Args:
        result: The step's result.
        root: The workspace root, whose levels give a level its trust class.
        first: The name of the step's first argument, what it ran on.

    Returns:
        The lines to print: the step, what it ran on and the result; why; the level; the record.
    """
    record = result.record
    words = STATUS_WORDS.get(record.status, record.status)
    target = _target(result, first)
    lines = [f"{record.step}{' ' + target if target else ''}: {words}"]
    lines += [f'  {line}' for line in _details(record.outputs)]
    if record.level:
        trust = level_trust(resolve(root)).get(record.level, '')
        lines.append(f"  level: {record.level}{f' ({trust})' if trust else ''}")
    how = ', replayed: its inputs did not change' if result.replayed else ''
    how = ', unchanged from the earlier run' if result.changed is False else how
    lines.append(f'  record: {_relative(result.path)}{how}')
    if result.changed:
        lines.append('  the result differs from the earlier record of the same inputs')
    return '\n'.join(lines) + '\n'


def _relative(path: Path) -> str:
    """Return a path relative to the working directory when it is inside it."""
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
