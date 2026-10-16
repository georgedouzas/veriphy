"""Read the test records `sage_test` writes to `.veriphy/tests/`, and rerun their oracle instances."""

import importlib
import json
from collections.abc import Callable
from pathlib import Path

from veriphy.core import VeriphyError

TESTS_DIR = 'tests'


def records(root: Path) -> list[Path]:
    """Return the test records of a workspace, by target name.

    Args:
        root: The Lean workspace root.

    Returns:
        The record files.
    """
    directory = root / '.veriphy' / TESTS_DIR
    return sorted(directory.glob('*.json')) if directory.is_dir() else []


def _read(path: Path) -> dict[str, object]:
    """Return a record's contents."""
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        message = f'{path}: not a test record ({exc})'
        raise VeriphyError(message) from exc
    if not isinstance(data, dict):
        message = f'{path}: not a test record'
        raise VeriphyError(message)
    return data


def _instances(data: object) -> list[dict[str, object]]:
    """Return the instances of a record (or of a rerun's reply), skipping malformed entries."""
    items = data.get('instances', []) if isinstance(data, dict) else []
    return [i for i in items if isinstance(i, dict)] if isinstance(items, list) else []


def describe(path: Path) -> str:
    """Return one line describing a record: target, level, accepted kernel and oracle instances, seed, Sage version.

    Args:
        path: The record file.

    Returns:
        The line.
    """
    data = _read(path)
    instances = [i for i in _instances(data) if i.get('accepted')]
    kernel = sum(1 for i in instances if i.get('kind') == 'kernel')
    oracle = len(instances) - kernel
    return (
        f"{data.get('target')}: {data.get('level')} ({kernel} kernel, {oracle} oracle; seed {data.get('seed')}, "
        f"Sage {data.get('sage_version')})"
    )


def _key(instance: dict[str, object]) -> tuple[str, ...]:
    """Return an instance's values, which identify it across runs."""
    values = instance.get('values', [])
    return tuple(str(v) for v in values) if isinstance(values, list) else ()


def find(root: Path, target: str) -> Path | None:
    """Return the record of a target, or `None`.

    Args:
        root: The Lean workspace root.
        target: The tested claim's name.

    Returns:
        The record file, if any.
    """
    path = root / '.veriphy' / TESTS_DIR / f'{target}.json'
    return path if path.is_file() else None


def _runner() -> Callable[[object, str, int], dict[str, object]]:
    """Return the daemon's test-script runner, which needs Sage."""
    try:
        oracle = importlib.import_module('veriphy.oracle')
    except ImportError:
        message = 'rerunning a test needs Sage: run `sage -python -m veriphy.certificates tests --rerun <target>`'
        raise VeriphyError(message) from None
    runner: Callable[[object, str, int], dict[str, object]] = oracle.run_test_script
    return runner


def rerun(path: Path, runner: Callable[[object, str, int], dict[str, object]] | None = None) -> list[str]:
    """Rerun a record's script on its recorded problem and compare the oracle verdicts with the record's.

    Kernel instances are rechecked by Lean when the project builds; only the oracle part needs Sage again.

    Args:
        path: The record file.
        runner: The test-script runner; the daemon's when `None`.

    Returns:
        One line per oracle instance whose verdict or evaluation changed; empty when the record still holds.
    """
    data = _read(path)
    run = runner if runner is not None else _runner()
    fresh = run(data.get('problem'), str(data.get('script', '')), 600)
    before = {_key(i): i for i in _instances(data) if i.get('kind') == 'oracle'}
    changes = []
    for instance in _instances(fresh):
        if instance.get('kind') != 'oracle':
            continue
        key = _key(instance)
        old = before.get(key)
        if old is None:
            changes.append(f'{list(key)}: a new oracle instance')
        elif not instance.get('verdict'):
            changes.append(f"{list(key)}: Sage now refutes the claim: {instance.get('evaluation')}")
        elif instance.get('evaluation') != old.get('evaluation'):
            changes.append(
                f"{list(key)}: the evaluation changed: {old.get('evaluation')} → {instance.get('evaluation')}",
            )
    return changes
