"""Compute a workflow's next step from the records of its target, read in time order, and run it up to an agent."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from veriphy.core import StepError, level_trust, resolve, workflow_entries
from veriphy.steps import Record, RecordStore, load_steps, read_record, run_step

STOP = 'stop'
# a bound on the entries `next` walks, past which a workflow loops on records that never change
MAX_STEPS = 1000


@dataclass(frozen=True)
class Next:
    """What a workflow does next for a target.

    Args:
        step: The step to run, or `None` when the workflow stopped or finished.
        reason: Why: the status or condition that stopped it, `done` at the end, or what the step waits for.
        agent: Whether the step is an agent's, which `run` does not run.
    """

    step: str | None
    reason: str
    agent: bool = False


def _names(root: Path, target: str) -> set[str]:
    """Return the values a record's inputs may name the target by: as given, and as a path of the workspace."""
    names = {target}
    path = Path(target) if Path(target).is_absolute() else root / target
    if path.exists():
        names |= {str(path), str(path.resolve())}
    return names


def _records(root: Path, target: str) -> list[tuple[int, Record]]:
    """Return the target's records, each with the time it was written, oldest first."""
    names = _names(root, target)
    found = []
    for path in RecordStore(root).all():
        record = read_record(path)
        if names & {str(v) for v in record.inputs.values()}:
            found.append((path.stat().st_mtime_ns, record))
    return sorted(found, key=lambda item: item[0])


def _holds(when: object, records: list[tuple[int, Record]], trusts: Mapping[str, str]) -> bool:
    """Return whether an entry's condition holds: `{without: <class>}` when no record grants a level of that class."""
    if not isinstance(when, dict):
        return True
    absent = when.get('without')
    return not any(trusts.get(str(r.level)) == absent for _, r in records if r.level)


def _index(entries: list[tuple[str, dict[str, object]]], step: str) -> int:
    """Return the position of a workflow's first entry for a step."""
    return next(i for i, (name, _) in enumerate(entries) if name == step)


def _spent(name: str, rules: dict[str, object], count: int) -> str | None:
    """Return where to go once a step's attempts are used up (`stop`, or an entry), or `None` while some remain."""
    attempts = rules.get('attempts')
    if not isinstance(attempts, int) or count < attempts:
        return None
    return str(rules.get('exhausted', STOP))


def _walk(
    entries: list[tuple[str, dict[str, object]]],
    agents: set[str],
    trusts: Mapping[str, str],
    records: list[tuple[int, Record]],
) -> Next:
    """Walk the entries from the start, consuming each step's newest record after the one consumed before it."""
    position, after = 0, -1
    for _ in range(MAX_STEPS):
        if position >= len(entries):
            return Next(None, 'done')
        name, rules = entries[position]
        if not _holds(rules.get('when'), records, trusts):
            position += 1
            continue
        own = [(time, r) for time, r in records if r.step == name]
        newer = [(time, r) for time, r in own if time > after]
        spent = _spent(name, rules, len(own))
        if not newer:
            if spent is None:
                return Next(name, 'an artifact to record' if name in agents else 'not run yet', name in agents)
            if spent == STOP:
                return Next(None, f'{name} used its {rules["attempts"]} attempts')
            position = _index(entries, spent)
            continue
        after, record = newer[-1]
        destination = rules.get(record.status)
        if destination == STOP:
            return Next(None, record.status)
        if isinstance(destination, str) and spent is not None:
            destination = spent
            if destination == STOP:
                return Next(None, f'{name} used its {rules["attempts"]} attempts')
        position = _index(entries, destination) if isinstance(destination, str) else position + 1
    message = 'the workflow loops without its records changing'
    raise StepError(message)


def next_step(root: Path, workflow: str, target: str) -> Next:
    """Return a workflow's next step for a target, from its records alone.

    Args:
        root: The workspace root.
        workflow: The workflow's name.
        target: What the steps' inputs name, such as a Lean file.

    Returns:
        The next step, or why the workflow stopped or finished.

    Raises:
        StepError: If the workspace has no such workflow.
    """
    config = resolve(root)
    declared = config.section('workflows').get(workflow)
    if declared is None:
        message = f"no workflow is named '{workflow}': the workflows are {', '.join(config.section('workflows'))}"
        raise StepError(message)
    agents = {name for name, step in load_steps(root).items() if step.kind == 'agent'}
    return _walk(workflow_entries(declared), agents, level_trust(config), _records(root, target))


def run_workflow(root: Path, workflow: str, target: str, inputs: Mapping[str, object]) -> list[str]:
    """Run a workflow's steps that are not an agent's, in order, until an agent step or the end.

    Args:
        root: The workspace root.
        workflow: The workflow's name.
        target: What the steps' inputs name; a step's first input defaults to it.
        inputs: The other inputs, by name, each given to the steps that take it.

    Returns:
        One line per step run, and a last line saying what happens next.

    Raises:
        StepError: If the workflow neither reaches an agent step nor its end within its bound of steps.
    """
    steps = load_steps(root)
    lines: list[str] = []
    for _ in range(MAX_STEPS):
        planned = next_step(root, workflow, target)
        if planned.step is None:
            return [*lines, f'{workflow}: {planned.reason}']
        step = steps[planned.step]
        if planned.agent:
            first = step.arguments[0].name if step.arguments else 'artifact'
            return [*lines, f'{workflow}: waiting for {step.name}: record the {first}, as veriphy {step.name} {target}']
        names = [argument.name for argument in step.arguments]
        params = {name: inputs[name] for name in names if name in inputs}
        if names and names[0] not in params:
            params[names[0]] = target
        result = run_step(step, root, params)
        lines.append(f'{step.name}: {result.record.status}' + (' (replayed)' if result.replayed else ''))
        if result.replayed:
            # a replayed record keeps the time it was written, older than the workflow's position: its time stamp
            # (not its content) moves to now, so the workflow reads it as this run's
            result.path.touch()
    message = f'the workflow {workflow} did not reach an agent step or its end'
    raise StepError(message)
