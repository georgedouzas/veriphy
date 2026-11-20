"""Test step records: the digest, the store that never overwrites, and the rule that only checks carry a level."""

from pathlib import Path

import pytest

from veriphy.core import Record, RecordError, RecordStore, config_digest, input_digest, read_record


def _record(**fields: object) -> Record:
    """Return a record with sensible defaults."""
    values: dict[str, object] = {
        'step': 'reason',
        'kind': 'check',
        'digest': 'd' * 64,
        'config': config_digest(),
        'status': 'entailed',
    }
    values.update(fields)
    return Record.from_json(values)


def test_digest_follows_content_not_path(tmp_path: Path) -> None:
    """Give two files with the same content one digest, and a changed content another."""
    first, second = tmp_path / 'a.ttl', tmp_path / 'b' / 'a.ttl'
    second.parent.mkdir()
    first.write_text('x')
    second.write_text('x')
    digest = input_digest('validate', {'graph': first.read_text()}, config_digest())
    assert digest == input_digest('validate', {'graph': second.read_text()}, config_digest())
    second.write_text('y')
    assert digest != input_digest('validate', {'graph': second.read_text()}, config_digest())


def test_digest_covers_the_seed_and_the_config() -> None:
    """Change the digest with the seed and with the config."""
    base = input_digest('meaning', {'claim': 'c'}, 'config', seed=0)
    assert base != input_digest('meaning', {'claim': 'c'}, 'config', seed=1)
    assert base != input_digest('meaning', {'claim': 'c'}, 'other', seed=0)


def test_store_never_overwrites(tmp_path: Path) -> None:
    """Write a second record of the same inputs beside the first, and read both back."""
    store = RecordStore(tmp_path)
    first = store.write(_record())
    second = store.write(_record(status='rejected'))
    assert first != second
    assert [read_record(p).status for p in store.variants('reason', 'd' * 64)] == ['entailed', 'rejected']
    assert store.latest('reason', 'd' * 64) == _record(status='rejected')


def test_only_checks_and_derived_steps_carry_a_level() -> None:
    """Refuse a level on evidence and agent records, and an unknown kind."""
    assert _record(level='certificate').level == 'certificate'
    for kind in ('evidence', 'agent'):
        with pytest.raises(RecordError, match='grants no level'):
            _record(kind=kind, level='certificate')
    with pytest.raises(RecordError, match='unknown kind'):
        _record(kind='guess')


def test_unchecked_and_failed_are_not_final() -> None:
    """Replay only a status that depends on the inputs alone."""
    assert _record().final
    assert not _record(status='unchecked').final
    assert not _record(status='failed').final


def test_malformed_record_is_refused(tmp_path: Path) -> None:
    """Refuse a file that is not a record, naming what is wrong."""
    path = tmp_path / 'r.json'
    path.write_text('{"step": "reason"}')
    with pytest.raises(RecordError, match='kind'):
        read_record(path)
