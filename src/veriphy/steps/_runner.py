"""Run a step: hash its inputs, replay a final record of the same inputs, or run it and record what it did."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from veriphy.core import StepError
from veriphy.steps._records import LEVELLED_KINDS, Record, RecordStore, config_digest, input_digest

Params = Mapping[str, object]
# statuses that mean the tool refused, found a counterexample or did not run; anything else not listed accepts
REFUSING = frozenset({'refused', 'rejected', 'violations', 'counterexample', 'failed', 'mismatch'})
UNCHECKED = frozenset({'unchecked', 'incomplete', 'undecided'})
REFUSED_EXIT = 1
USAGE_EXIT = 2
UNCHECKED_EXIT = 3


@dataclass(frozen=True)
class Prepared:
    """A step's inputs, read before anything runs.

    Args:
        contents: Each input's name and content, which enter the digest.
        sources: Where each input came from, such as file paths, for the reader of the record.
        seed: The seed of a random step.
        context: Anything the step read while preparing and needs again when it runs, such as a loaded graph.
    """

    contents: Mapping[str, str | bytes]
    sources: dict[str, object] = field(default_factory=dict)
    seed: int | None = None
    context: object = None


@dataclass(frozen=True)
class Outcome:
    """What a step's run produced.

    Args:
        status: What happened.
        outputs: What the step produced.
        tools: The name and version of each tool the step ran.
        level: The level a check or derived step grants, if any.
    """

    status: str
    outputs: dict[str, object] = field(default_factory=dict)
    tools: dict[str, str] = field(default_factory=dict)
    level: str | None = None


@dataclass(frozen=True)
class Argument:
    """One argument of a step's command: a parameter, its help, and how the command line spells it.

    Args:
        name: The parameter's name.
        help: One line on what it is.
        option: Given as `--name` instead of positionally.
        type: Converts the command-line text, `str` by default.
        default: The value when an option is not given.
        choices: The values allowed, when they are few.
        flag: The option's spelling when it differs from `--name`, as `--prefix` for `prefixes`.
        many: An option that may be repeated, collecting a list.
    """

    name: str
    help: str = ''
    option: bool = False
    type: Callable[[str], object] = str
    default: object = None
    choices: tuple[str, ...] = ()
    flag: str | None = None
    many: bool = False


@dataclass(frozen=True)
class Step:
    """A step: its name, its kind, how it reads its inputs and how it runs.

    Args:
        name: The step's name, also the directory of its records.
        kind: `agent`, `evidence`, `check` or `derived`.
        prepare: Reads the inputs from the workspace root and the parameters.
        execute: Runs the step on what `prepare` read.
        help: One line on what the step does, for the command's help.
        arguments: The step's parameters on the command line.
    """

    name: str
    kind: str
    prepare: Callable[[Path, Params], Prepared]
    execute: Callable[[Path, Params, Prepared], Outcome]
    help: str = ''
    arguments: tuple[Argument, ...] = ()


@dataclass(frozen=True)
class Result:
    """The result of an operation: its record, and how it was obtained.

    Args:
        record: The record.
        path: Its file.
        replayed: Whether an existing record was returned without running the step.
        changed: On a run with an earlier final record of the same inputs, whether the result differs from it.
        target: What the operation acted on, as the caller named it.
    """

    record: Record
    path: Path
    replayed: bool
    changed: bool | None = None
    target: str | None = None

    @property
    def verb(self) -> str:
        """The operation's verb, its step's name."""
        return self.record.step

    @property
    def status(self) -> str:
        """What happened."""
        return self.record.status

    @property
    def outputs(self) -> dict[str, object]:
        """What the operation produced."""
        return self.record.outputs

    @property
    def level(self) -> str | None:
        """The level a check or derived operation grants, if any."""
        return self.record.level


def run_step(step: Step, root: Path, params: Params | None = None, *, rerun: bool = False) -> Result:
    """Run a step in a workspace, or replay its final record of the same inputs.

    Args:
        step: The step.
        root: The workspace root, under which records are written.
        params: The step's parameters.
        rerun: Run even when a final record of the same inputs exists.

    Returns:
        The record and how it was obtained. A rerun with the same result writes nothing and returns the earlier
        record; a different result is written beside it.

    Raises:
        StepError: If a step of kind `agent` or `evidence` returns a level.

    Examples:
        >>> import tempfile
        >>> step = Step('echo', 'evidence', lambda root, p: Prepared({'x': str(p['x'])}),
        ...             lambda root, p, prepared: Outcome('accepted', {'x': p['x']}))
        >>> with tempfile.TemporaryDirectory() as tmp:
        ...     first = run_step(step, Path(tmp), {'x': 1})
        ...     second = run_step(step, Path(tmp), {'x': 1})
        ...     first.replayed, second.replayed, second.record == first.record
        (False, True, True)
    """
    given = params or {}
    store = RecordStore(root)
    prepared = step.prepare(root, given)
    digest = input_digest(step.name, prepared.contents, config_digest(), prepared.seed)
    latest = store.latest(step.name, digest)
    if latest is not None and latest.final and not rerun:
        return Result(latest, store.variants(step.name, digest)[-1], replayed=True)
    outcome = step.execute(root, given, prepared)
    if outcome.level is not None and step.kind not in LEVELLED_KINDS:
        message = f"step '{step.name}' is of kind '{step.kind}', which grants no level, but it gave '{outcome.level}'"
        raise StepError(message)
    record = Record(
        step=step.name,
        kind=step.kind,
        digest=digest,
        config=config_digest(),
        status=outcome.status,
        inputs=prepared.sources,
        outputs=outcome.outputs,
        tools=outcome.tools,
        seed=prepared.seed,
        level=outcome.level,
    )
    earlier = latest if latest is not None and latest.final else None
    if earlier is not None and earlier.same_result(record):
        return Result(earlier, store.variants(step.name, digest)[-1], replayed=False, changed=False)
    return Result(record, store.write(record), replayed=False, changed=None if earlier is None else True)


def exit_code(status: str) -> int:
    """Return the command's exit status for a record status.

    Args:
        status: The record's status.

    Returns:
        0 when the step accepted, 1 when it refused, found a counterexample or failed, 3 when it is unchecked.

    Examples:
        >>> exit_code('entailed'), exit_code('refused'), exit_code('unchecked')
        (0, 1, 3)
    """
    if status in REFUSING:
        return REFUSED_EXIT
    if status in UNCHECKED:
        return UNCHECKED_EXIT
    return 0
