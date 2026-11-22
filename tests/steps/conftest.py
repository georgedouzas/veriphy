"""Provide the step fixtures: forgetting only the records a test itself writes into a shared workspace."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from veriphy.steps import Record, RecordStore


@pytest.fixture
def forget_own_records(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[Path]]:
    """Delete, after the test, the records it wrote, and no other: tests in parallel share the repository's records."""
    written: list[Path] = []
    original = RecordStore.write

    def write(store: RecordStore, record: Record) -> Path:
        """Write a record and remember its file."""
        path = original(store, record)
        written.append(path)
        return path

    monkeypatch.setattr(RecordStore, 'write', write)
    yield written
    for path in written:
        path.unlink(missing_ok=True)
