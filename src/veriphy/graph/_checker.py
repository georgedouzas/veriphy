"""Set up and run `oo-horn`, the verified checker of Horn certificates, and the reasoner, from Open Ontologies."""

import hashlib
import json
import os
import platform
import shutil
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from veriphy.core import CheckerError, GraphExtraMissingError
from veriphy.graph._process import fetch_url, find_tool, run_process

CHECKER_VARIABLE = 'VERIPHY_OO_HORN'
SETUP_VARIABLE = 'VERIPHY_GRAPH_SETUP'
CHECKER_BINARY = Path('lean') / '.lake' / 'build' / 'bin' / 'oo-horn'
PREBUILT_BINARY = Path('bin') / 'oo-horn'
REASONER_SOURCE = Path('python') / 'src'
BUILD_COMMAND = 'sage -python -m veriphy.graph checker build'
ACCEPTED, REJECTED, UNREADABLE = 0, 1, 2
CHECK_TIMEOUT = 600
LINUX_MACHINES = ('x86_64', 'amd64')
SUM_FIELDS = 2

Notify = Callable[[str], None]


@dataclass(frozen=True)
class Release:
    """An Open Ontologies release that Veriphy fetches its reasoner and checker from.

    Args:
        repository: The git repository.
        tag: The release tag.
        commit: The commit the tag must point to.
        assets: The base URL of the release's downloadable assets.
        prebuilt: The asset name of the prebuilt `oo-horn` for Linux x86_64.
        prebuilt_sha256: The SHA-256 the prebuilt `oo-horn` must have.
    """

    repository: str
    tag: str
    commit: str
    assets: str
    prebuilt: str
    prebuilt_sha256: str


PINNED_RELEASE = Release(
    repository='https://github.com/fabio-rovai/open-ontologies',
    tag='v2.1.0',
    commit='ef6e781c71aaccaa35c2a1cd06169f0c862d5769',
    assets='https://github.com/fabio-rovai/open-ontologies/releases/download/v2.1.0',
    prebuilt='oo-horn-x86_64-unknown-linux-gnu',
    prebuilt_sha256='967224162167ddfa55dd3196e86ea719157f121b62981f283c0315381da0477b',
)


def notify_stderr(message: str) -> None:
    """Write a setup message to standard error.

    Args:
        message: The message.
    """
    sys.stderr.write(f'{message}\n')


@dataclass(frozen=True)
class Setup:
    """Where first-use setup fetches from, and where its messages go.

    Args:
        release: The release, the pinned one by default.
        notify: Receives a message for each setup step.
    """

    release: Release = PINNED_RELEASE
    notify: Notify = notify_stderr


def _env(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    """Return the environment to read, `os.environ` when `None`."""
    return os.environ if environ is None else environ


def cache_dir(environ: Mapping[str, str] | None = None, release: Release = PINNED_RELEASE) -> Path:
    """Return the directory that holds a release of Open Ontologies.

    Args:
        environ: The environment, `os.environ` when `None`.
        release: The release, the pinned one by default.

    Returns:
        `$XDG_CACHE_HOME/veriphy/open-ontologies/<tag>`, under `~/.cache` when the variable is unset.

    Examples:
        >>> cache_dir({'XDG_CACHE_HOME': '/tmp/cache'}).as_posix()
        '/tmp/cache/veriphy/open-ontologies/v2.1.0'
    """
    env = _env(environ)
    base = Path(env['XDG_CACHE_HOME']) if env.get('XDG_CACHE_HOME') else Path.home() / '.cache'
    return base / 'veriphy' / 'open-ontologies' / release.tag


def setup_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """Return whether Veriphy may set up the reasoner and the checker on first use.

    Args:
        environ: The environment, `os.environ` when `None`.

    Returns:
        `False` when `VERIPHY_GRAPH_SETUP` is `off`, else `True`.

    Examples:
        >>> setup_enabled({'VERIPHY_GRAPH_SETUP': 'off'}), setup_enabled({})
        (False, True)
    """
    return _env(environ).get(SETUP_VARIABLE, '').lower() != 'off'


@dataclass(frozen=True)
class CheckerLookup:
    """Where Veriphy looked for `oo-horn`, and what it found.

    Args:
        path: The executable, or `None` when none was found.
        searched: The paths looked at, in order.
        explicit: Whether the path came from `VERIPHY_OO_HORN`.
    """

    path: Path | None
    searched: tuple[Path, ...]
    explicit: bool = False


def _executable(path: Path) -> bool:
    """Return whether a path is an executable file."""
    return path.is_file() and os.access(path, os.X_OK)


def find_checker(environ: Mapping[str, str] | None = None, release: Release = PINNED_RELEASE) -> CheckerLookup:
    """Find `oo-horn`: the path `VERIPHY_OO_HORN` names, else the cached prebuilt binary, else the cached build.

    An explicit path is never replaced.

    Args:
        environ: The environment, `os.environ` when `None`.
        release: The release, the pinned one by default.

    Returns:
        The lookup.

    Examples:
        >>> find_checker({'VERIPHY_OO_HORN': '/missing/oo-horn'}).path is None
        True
    """
    env = _env(environ)
    explicit = env.get(CHECKER_VARIABLE)
    if explicit:
        path = Path(explicit)
        return CheckerLookup(path if _executable(path) else None, (path,), explicit=True)
    directory = cache_dir(env, release)
    candidates = (directory / PREBUILT_BINARY, directory / CHECKER_BINARY)
    return CheckerLookup(next((c for c in candidates if _executable(c)), None), candidates)


def _run(command: list[str], cwd: Path | None = None) -> str:
    """Run a command and return its output, raising with its output when it fails."""
    code, out, err = run_process(command, cwd)
    if code != 0:
        message = f'{" ".join(command)} failed ({code}):\n{out}{err}'
        raise CheckerError(message)
    return out


def _tool(name: str) -> str:
    """Return the path of a tool the setup needs."""
    return find_tool(name, 'setting up the checker needs git, and elan (which provides lake) where it is built')


def ensure_release(
    *,
    environ: Mapping[str, str] | None = None,
    release: Release = PINNED_RELEASE,
    notify: Notify = notify_stderr,
) -> tuple[Path, str]:
    """Fetch a release into the cache unless it is there, and refuse it unless its commit is the pinned one.

    Args:
        environ: The environment, `os.environ` when `None`.
        release: The release, the pinned one by default.
        notify: Receives a message when the release is fetched.

    Returns:
        The release's directory and its commit.

    Raises:
        CheckerError: When the tag points to another commit than the pinned one, naming both commits.
    """
    directory = cache_dir(environ, release)
    if not (directory / '.git').is_dir():
        notify(f'Fetching Open Ontologies {release.tag} into {directory}')
        directory.parent.mkdir(parents=True, exist_ok=True)
        clone = ['clone', '--quiet', '--depth', '1', '--branch', release.tag, release.repository, str(directory)]
        _run([_tool('git'), *clone])
    commit = _run([_tool('git'), 'rev-parse', 'HEAD'], cwd=directory).strip()
    if commit != release.commit:
        shutil.rmtree(directory)
        message = f'Open Ontologies {release.tag} points to commit {commit}, and Veriphy pins {release.commit}'
        raise CheckerError(message)
    return directory, commit


def ensure_reasoner(
    *,
    environ: Mapping[str, str] | None = None,
    release: Release = PINNED_RELEASE,
    notify: Notify = notify_stderr,
) -> Path:
    """Return the source directory of the release's reasoner, fetching the release on first use.

    Args:
        environ: The environment, `os.environ` when `None`.
        release: The release, the pinned one by default.
        notify: Receives a message when the release is fetched.

    Returns:
        The directory to import `open_ontologies_lite` from.

    Raises:
        GraphExtraMissingError: When the reasoner is missing and automatic setup is off or fails.
    """
    source = cache_dir(environ, release) / REASONER_SOURCE
    if (source / 'open_ontologies_lite' / 'horn').is_dir():
        return source
    module = 'open_ontologies_lite'
    if not setup_enabled(environ):
        raise GraphExtraMissingError(module)
    try:
        ensure_release(environ=environ, release=release, notify=notify)
    except CheckerError as exc:
        raise GraphExtraMissingError(module) from exc
    return source


def _listed_sha256(sums: str, name: str) -> str | None:
    """Return the SHA-256 that a `SHASUMS.txt` lists for an asset."""
    for line in sums.splitlines():
        fields = line.split()
        if len(fields) == SUM_FIELDS and fields[1].lstrip('*') == name:
            return fields[0]
    return None


def _download_prebuilt(directory: Path, release: Release, notify: Notify) -> Path | None:
    """Download and verify the prebuilt checker, returning it, or `None` when it does not run here."""
    notify(f'Downloading the prebuilt oo-horn of Open Ontologies {release.tag}')
    data = fetch_url(f'{release.assets}/{release.prebuilt}')
    listed = _listed_sha256(fetch_url(f'{release.assets}/SHASUMS.txt').decode(), release.prebuilt)
    digest = hashlib.sha256(data).hexdigest()
    if digest != release.prebuilt_sha256 or digest != listed:
        message = (
            f'the downloaded {release.prebuilt} has SHA-256 {digest}, while Veriphy pins {release.prebuilt_sha256} '
            f'and the release lists {listed}: it was not kept'
        )
        raise CheckerError(message)
    target = directory / PREBUILT_BINARY
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    target.chmod(0o755)
    if run_process([str(target), 'rules'])[0] != 0:
        target.unlink()
        notify('The prebuilt oo-horn does not run on this machine, so it will be built')
        return None
    return target


def _prebuilt_platform() -> bool:
    """Return whether the release ships a prebuilt checker for this machine."""
    return sys.platform.startswith('linux') and platform.machine().lower() in LINUX_MACHINES


def _setup_checker(environ: Mapping[str, str] | None, release: Release, notify: Notify, prebuilt: bool | None) -> Path:
    """Set up the checker in the cache: download it where the release ships one, else build it."""
    directory, _ = ensure_release(environ=environ, release=release, notify=notify)
    if _executable(directory / CHECKER_BINARY):
        return directory / CHECKER_BINARY
    try_prebuilt = _prebuilt_platform() if prebuilt is None else prebuilt
    found = _download_prebuilt(directory, release, notify) if try_prebuilt else None
    if found is not None:
        return found
    notify(f'Building oo-horn from Open Ontologies {release.tag} with its own Lean toolchain: this takes minutes')
    _run([_tool('lake'), 'build', 'oo-horn'], cwd=directory / 'lean')
    return directory / CHECKER_BINARY


def ensure_checker(
    *,
    environ: Mapping[str, str] | None = None,
    release: Release = PINNED_RELEASE,
    notify: Notify = notify_stderr,
    prebuilt: bool | None = None,
) -> Path:
    """Return `oo-horn`, setting it up on first use unless automatic setup is off.

    Args:
        environ: The environment, `os.environ` when `None`.
        release: The release, the pinned one by default.
        notify: Receives a message for each setup step.
        prebuilt: Whether to try the prebuilt binary, detected from the platform when `None`.

    Returns:
        The executable.

    Raises:
        CheckerError: When no checker is found and setup is off, or the explicit path is not an executable.
    """
    lookup = find_checker(environ, release)
    if lookup.path is not None:
        return lookup.path
    if lookup.explicit:
        message = f'{CHECKER_VARIABLE} names {lookup.searched[0]}, which is not an executable'
        raise CheckerError(message)
    if not setup_enabled(environ):
        message = f'no checker at {", ".join(map(str, lookup.searched))}, and {SETUP_VARIABLE} is off'
        raise CheckerError(message)
    return _setup_checker(environ, release, notify, prebuilt)


@dataclass(frozen=True)
class BuildReport:
    """What `build_checker` fetched and set up.

    Args:
        tag: The Open Ontologies release.
        commit: The commit the release points to.
        checker: The set-up `oo-horn`, or `None` when only the release was fetched.
        reasoner: The directory the reasoner is imported from.
    """

    tag: str
    commit: str
    checker: Path | None
    reasoner: Path


def build_checker(
    *,
    reasoner_only: bool = False,
    environ: Mapping[str, str] | None = None,
    release: Release = PINNED_RELEASE,
    notify: Notify = notify_stderr,
    prebuilt: bool | None = None,
) -> BuildReport:
    """Fetch the release, and download or build `oo-horn` unless it is there, whatever `VERIPHY_GRAPH_SETUP` says.

    Args:
        reasoner_only: Fetch the release, which holds the reasoner, without setting up the checker.
        environ: The environment, `os.environ` when `None`.
        release: The release, the pinned one by default.
        notify: Receives a message for each setup step.
        prebuilt: Whether to try the prebuilt binary, detected from the platform when `None`.

    Returns:
        The report.
    """
    directory, commit = ensure_release(environ=environ, release=release, notify=notify)
    checker = None if reasoner_only else _setup_checker(environ, release, notify, prebuilt)
    return BuildReport(release.tag, commit, checker, directory / REASONER_SOURCE)


def check_certificate(directory: Path, checker: Path) -> dict[str, object]:
    """Run `oo-horn check` on a certificate directory and return its report with the status it implies.

    The status is `accepted` (exit 0), `rejected` (exit 1), `unreadable` (exit 2) or `unchecked_error`. The verdict
    and the theorem are the checker's own words, copied from its report.

    Args:
        directory: The certificate directory, with `rules.tsv`, `asserted.tsv` and `horn.tsv`.
        checker: The `oo-horn` executable.

    Returns:
        The checker's JSON report, with `status` and `checker` added.
    """
    files = [str(directory / name) for name in ('rules.tsv', 'asserted.tsv', 'horn.tsv')]
    try:
        code, out, err = run_process([str(checker), 'check', *files], timeout=CHECK_TIMEOUT)
    except CheckerError as exc:
        return {'status': 'unchecked_error', 'checker': str(checker), 'error': str(exc)}
    statuses = {ACCEPTED: 'accepted', REJECTED: 'rejected', UNREADABLE: 'unreadable'}
    try:
        report = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
    except json.JSONDecodeError:
        report = {'output': out}
    if not isinstance(report, dict):
        report = {'output': out}
    status = statuses.get(code, 'unchecked_error')
    return {**report, 'status': status, 'checker': str(checker), 'stderr': err.strip()}


def builtin_rules(checker: Path) -> str:
    """Return the built-in rule table as the checker prints it.

    Args:
        checker: The `oo-horn` executable.

    Returns:
        The table.
    """
    return _run([str(checker), 'rules'])
