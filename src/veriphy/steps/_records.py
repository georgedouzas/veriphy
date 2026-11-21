"""Write and replay step records: one JSON file per step run, keyed by the digest of the step's inputs."""

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path

from veriphy.core import RecordError, canonical_json, content_digest, project_dir, resolve

KINDS = ('agent', 'evidence', 'check', 'derived')
LEVELLED_KINDS = frozenset({'check', 'derived'})
# a status that describes the machine rather than the inputs; such a record is kept but never replayed
NOT_FINAL = frozenset({'unchecked', 'failed'})
RUNS_DIR = 'runs'


def config_digest(root: Path) -> str:
    """Return the digest of the configuration a step runs under: the workspace's resolved configuration.

    Args:
        root: The workspace root.

    Returns:
        The digest; a comment or a reordering in `veriphy.yaml` leaves it unchanged.
    """
    return resolve(root).digest()


def input_digest(step: str, inputs: Mapping[str, str | bytes], config: str, seed: int | None = None) -> str:
    """Return the digest of a step's inputs: its name, each input's content, the config digest and the seed.

    Paths are not part of the inputs, so moving a file with the same content keeps its digest.

    Args:
        step: The step's name.
        inputs: Each input's name and content.
        config: The config digest.
        seed: The seed of a random step.

    Returns:
        The digest, in hexadecimal.

    Examples:
        >>> a = input_digest('validate', {'graph': 'x'}, 'c')
        >>> a == input_digest('validate', {'graph': 'x'}, 'c'), a == input_digest('validate', {'graph': 'y'}, 'c')
        (True, False)
    """
    contents = {name: content_digest(value) for name, value in inputs.items()}
    return content_digest(canonical_json({'step': step, 'inputs': contents, 'config': config, 'seed': seed}))


def _mapping(value: object) -> dict[str, object]:
    """Return a JSON object as a dictionary with string keys, and an absent one as an empty dictionary."""
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        message = f'not a step record: expected an object, found {type(value).__name__}'
        raise RecordError(message)
    return {str(key): item for key, item in value.items()}


@dataclass(frozen=True)
class Record:
    """What one run of a step did.

    Args:
        step: The step's name.
        kind: `agent`, `evidence`, `check` or `derived`.
        digest: The input digest.
        config: The config digest.
        status: What happened, such as `accepted`, `refused`, `entailed`, `unchecked` or `failed`.
        inputs: Where each input came from, such as file paths, for the reader. They do not enter the digest.
        outputs: What the step produced.
        tools: The name and version of each tool the step ran.
        seed: The seed of a random step.
        level: The level a check or derived step grants, if any.
    """

    step: str
    kind: str
    digest: str
    config: str
    status: str
    inputs: dict[str, object] = field(default_factory=dict)
    outputs: dict[str, object] = field(default_factory=dict)
    tools: dict[str, str] = field(default_factory=dict)
    seed: int | None = None
    level: str | None = None

    def __post_init__(self) -> None:
        """Refuse an unknown kind, and a level on a kind that cannot grant one."""
        if self.kind not in KINDS:
            message = f"step '{self.step}': unknown kind '{self.kind}' (known: {', '.join(KINDS)})"
            raise RecordError(message)
        if self.level is not None and self.kind not in LEVELLED_KINDS:
            message = f"step '{self.step}' is of kind '{self.kind}', which grants no level, but it gave '{self.level}'"
            raise RecordError(message)

    @property
    def final(self) -> bool:
        """Whether the status depends on the inputs alone, so the record may be replayed."""
        return self.status not in NOT_FINAL

    def to_json(self) -> dict[str, object]:
        """Return the record as a JSON object, without the empty optional fields."""
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}

    @classmethod
    def from_json(cls, data: Mapping[str, object]) -> 'Record':
        """Return the record a JSON object describes.

        Args:
            data: The object, as `to_json` writes it.

        Returns:
            The record.

        Raises:
            RecordError: If a field is missing or has the wrong type.
        """
        missing = [key for key in ('step', 'kind', 'digest', 'config', 'status') if not isinstance(data.get(key), str)]
        seed, level = data.get('seed'), data.get('level')
        if missing or not (seed is None or isinstance(seed, int)) or not (level is None or isinstance(level, str)):
            message = f'not a step record: missing or malformed {", ".join(missing) or "seed or level"}'
            raise RecordError(message)
        return cls(
            step=str(data['step']),
            kind=str(data['kind']),
            digest=str(data['digest']),
            config=str(data['config']),
            status=str(data['status']),
            inputs=_mapping(data.get('inputs')),
            outputs=_mapping(data.get('outputs')),
            tools={key: str(value) for key, value in _mapping(data.get('tools')).items()},
            seed=seed,
            level=level,
        )

    def same_result(self, other: 'Record') -> bool:
        """Return whether two records of the same inputs have the same status, outputs and level.

        Args:
            other: The other record.

        Returns:
            Whether the results match.
        """
        return (self.status, self.outputs, self.level) == (other.status, other.outputs, other.level)


class RecordStore:
    """The records of a workspace, under `.veriphy/runs/<step>/<digest>.json`.

    Args:
        root: The workspace root.
    """

    def __init__(self, root: Path) -> None:
        self.directory = project_dir(root) / RUNS_DIR

    def path(self, step: str, digest: str, variant: int = 0) -> Path:
        """Return the path of a record, with a numeric suffix for a later, different result of the same inputs.

        Args:
            step: The step's name.
            digest: The input digest.
            variant: 0 for the first record, then 1, 2 and so on.

        Returns:
            The path.
        """
        name = digest if variant == 0 else f'{digest}.{variant}'
        return self.directory / step / f'{name}.json'

    def variants(self, step: str, digest: str) -> list[Path]:
        """Return the existing records of a step's inputs, oldest first.

        Args:
            step: The step's name.
            digest: The input digest.

        Returns:
            The paths.
        """
        found: list[Path] = []
        while (path := self.path(step, digest, len(found))).is_file():
            found.append(path)
        return found

    def latest(self, step: str, digest: str) -> Record | None:
        """Return the newest record of a step's inputs, or `None`.

        Args:
            step: The step's name.
            digest: The input digest.

        Returns:
            The record.
        """
        paths = self.variants(step, digest)
        return read_record(paths[-1]) if paths else None

    def write(self, record: Record) -> Path:
        """Write a record, after any existing record of the same inputs, and never over one.

        Args:
            record: The record.

        Returns:
            The path it was written to.

        Raises:
            RecordError: If a file already holds that path, which only a race can cause.
        """
        path = self.path(record.step, record.digest, len(self.variants(record.step, record.digest)))
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open('x') as stream:
                stream.write(json.dumps(record.to_json(), indent=2, sort_keys=True, ensure_ascii=False) + '\n')
        except FileExistsError as exc:
            message = f'{path} exists; a record is never overwritten'
            raise RecordError(message) from exc
        return path

    def all(self, step: str | None = None) -> list[Path]:
        """Return the paths of every record, or of one step's, sorted.

        Args:
            step: The step's name, or `None` for every step.

        Returns:
            The paths.
        """
        pattern = f'{step}/*.json' if step else '*/*.json'
        return sorted(self.directory.glob(pattern)) if self.directory.is_dir() else []


def read_record(path: Path) -> Record:
    """Read a record file.

    Args:
        path: The file.

    Returns:
        The record.

    Raises:
        RecordError: If the file is not valid JSON or not a record.
    """
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        message = f'{path}: {exc}'
        raise RecordError(message) from exc
    if not isinstance(data, dict):
        message = f'{path}: not a JSON object'
        raise RecordError(message)
    return Record.from_json(data)
