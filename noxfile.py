"""Development tasks."""

import json
import re
import shlex
import shutil
import tempfile
import tomllib
from pathlib import Path
from typing import Any

import nox
from git_changelog.cli import build_and_render

nox.options.default_venv_backend = 'uv'
nox.options.error_on_external_run = True
nox.options.reuse_existing_virtualenvs = True

PYTHON_VERSIONS: list[str] = ['3.11', '3.12', '3.13', '3.14']

FILES: list[str] = ['src', 'tests', 'docs', 'noxfile.py']
# the math pack's Lean workspace, and where its Python copies of the translation tables live
LEAN = Path('src/veriphy/packs/math/lean')
TABLES = Path('src/veriphy/packs/math/script')
DIAGRAMS = Path('docs/architecture/diagrams')
LEAN_IMPORT = re.compile(r'^import (\S+)$', re.MULTILINE)
CHANGELOG_ARGS: dict[str, Any] = {
    'repository': '.',
    'convention': 'angular',
    'template': 'keepachangelog',
    'parse_trailers': True,
    'parse_refs': False,
    'sections': ['feat', 'fix', 'docs', 'style', 'refactor', 'tests', 'chore'],
    'bump_latest': True,
    'output': 'CHANGELOG.md',
}


def check_cli(session: nox.Session, args: list[str], default: str = 'all') -> str:
    """Check the CLI arguments.

    Arguments:
        session: The nox session.
        args: The available CLI arguments.
        default: The subcommand used when none is given.
    """
    available_args = ', '.join([f'`{arg}`' for arg in args])
    msg = f'Available subcommands are one of {available_args}.'
    session_args = list(session.posargs) or [default]
    if len(session_args) > 1 or session_args[0] not in args:
        session.skip(f'{msg} Instead `{" ".join(session_args)}` was given')
    return session_args[0]


@nox.session
def clean(session: nox.Session) -> None:
    """Clean build artifacts and cache files.

    Arguments:
        session: The nox session.
    """
    paths = [
        '.mypy_cache',
        '.pytest_cache',
        'tests/.pytest_cache',
        'build',
        'dist',
        'htmlcov',
        'pip-wheel-metadata',
        'site',
        '__pycache__',
        'docs/generated',
        '.nox',
        '.ruff_cache',
        'coverage.xml',
    ]
    for path in paths:
        shutil.rmtree(path, ignore_errors=True)
    for cache_path in Path().rglob('__pycache__'):
        shutil.rmtree(cache_path, ignore_errors=True)
    for file in Path().rglob('*.rej'):
        if file.exists():
            file.unlink()
    for file in Path().rglob('.coverage*'):
        if file.exists():
            file.unlink()


@nox.session
def docs(session: nox.Session) -> None:
    """Build or serve the documentation.

    Arguments:
        session: The nox session.
    """
    arg = check_cli(session, ['serve', 'build'], default='serve')
    # Not `--only-dev`: mkdocstrings imports the package to document it.
    session.run('uv', 'sync', '--active', external=True)
    session.run('properdocs', arg)


@nox.session
@nox.parametrize('file', FILES)
def formatting(session: nox.Session, file: str) -> None:
    """Format the code.

    Arguments:
        session: The nox session.
        file: The file to be formatted.
    """
    arg = check_cli(session, ['all', 'code', 'docstrings'])
    session.run('uv', 'sync', '--only-dev', '--active', external=True)
    if arg in ['code', 'all']:
        session.run('black', file)
    if arg in ['docstrings', 'all']:
        session.run('docformatter', file)


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize('file', FILES)
def checks(session: nox.Session, file: str) -> None:
    """Check code quality, dependencies or type annotations.

    Arguments:
        session: The nox session.
        file: The file to be checked.
    """
    arg = check_cli(session, ['all', 'quality', 'dependencies', 'types', 'security', 'docs'])
    session.run('uv', 'sync', '--only-dev', '--active', external=True)
    if arg in ['quality', 'all']:
        session.run('ruff', 'check', file)
    if arg in ['types', 'all']:
        session.run('mypy', file)
    if arg in ['security', 'all']:
        session.run('bandit', '-c', 'pyproject.toml', '-r', file)
    if arg in ['docs', 'all'] and file == 'src':
        session.run('interrogate', file)
        session.run('pydoclint', file)
    if arg in ['dependencies', 'all']:
        requirements_path = (Path(session.create_tmp()) / 'requirements.txt').as_posix()
        session.run(
            'uv',
            'export',
            '--format',
            'requirements-txt',
            '--group',
            'dev',
            '--no-emit-project',
            '--output-file',
            requirements_path,
            external=True,
        )
        config = tomllib.loads(Path('pyproject.toml').read_text())
        ignored = config.get('tool', {}).get('pip-audit', {}).get('ignore-vulns', [])
        ignore_args = [flag for vuln in ignored for flag in ('--ignore-vuln', vuln)]
        session.run('pip-audit', '-r', requirements_path, *ignore_args)
        session.run('deptry', 'src', 'tests')


@nox.session(python=False)
def tests(session: nox.Session) -> None:
    """Run tests, doctests and coverage in SageMath's environment, from a venv that sees Sage's site-packages.

    Arguments:
        session: The nox session.
    """
    sage = shutil.which('sage')
    if sage is None:
        session.skip('the tests need SageMath on PATH (`sage`)')
    venv = Path(session.create_tmp()) / 'sage-venv'
    if not (venv / 'bin' / 'python').exists():
        session.run(sage, '-python', '-m', 'venv', '--without-pip', str(venv), external=True)
    sage_paths = session.run(
        sage,
        '-python',
        '-c',
        'import site; print("\\n".join(site.getsitepackages()))',
        external=True,
        silent=True,
    )
    purelib = session.run(
        str(venv / 'bin' / 'python'),
        '-c',
        'import sysconfig; print(sysconfig.get_path("purelib"))',
        external=True,
        silent=True,
    )
    Path(str(purelib).strip(), 'sage.pth').write_text(str(sage_paths))
    env = {'VIRTUAL_ENV': str(venv)}
    session.run('uv', 'sync', '--active', env=env, external=True)
    session.run(
        str(venv / 'bin' / 'python'),
        '-m',
        'veriphy',
        'layers',
        'claims',
        'checker',
        'build',
        '--reasoner-only',
        env=env,
        external=True,
    )
    selection = ['-k', *session.posargs] if session.posargs else []
    commands = [
        [str(venv / 'bin' / 'pytest'), '-n', 'auto', *selection, 'tests', 'src'],
        *([str(venv / 'bin' / 'coverage'), step] for step in ('report', 'html', 'xml')),
    ]
    # The release is fetched above, so no test reaches the network through first-use setup.
    for command in commands:
        session.run(sage, '-sh', '-c', shlex.join(command), env={**env, 'VERIPHY_GRAPH_SETUP': 'off'}, external=True)


@nox.session
def changelog(session: nox.Session) -> None:
    """Build the changelog.

    Arguments:
        session: The nox session.
    """
    session.run('uv', 'sync', '--only-dev', '--active', external=True)
    build_and_render(**CHANGELOG_ARGS)


@nox.session
def release(session: nox.Session) -> None:
    """Kick off a release process.

    Arguments:
        session: The nox session.
    """
    session.run('uv', 'sync', '--only-dev', '--active', external=True)

    changelog, _ = build_and_render(**CHANGELOG_ARGS)
    if changelog.versions_list[0].tag:
        session.skip('Commit has already a tag. Release is aborted.')
    version = changelog.versions_list[0].planned_tag
    if version is None:
        session.skip('Next version was not possible to be specified. Release is aborted.')

    # Create release branch and commit changelog
    session.run('git', 'checkout', '-b', f'release_{version}', external=True)
    session.run('git', 'add', 'CHANGELOG.md', external=True)
    session.run('git', 'commit', '-m', f'chore: Release {version}', '--allow-empty', external=True)
    session.run('git', 'push', '-u', 'origin', f'release_{version}', external=True)

    # Create and merge PR from release branch to main
    session.run('gh', 'pr', 'create', '--base', 'main', '--fill', external=True)
    session.run('gh', 'pr', 'merge', '--rebase', '--delete-branch', external=True)

    # Create and push the release tag, which is what the pipeline reacts to
    session.run('git', 'checkout', 'main', external=True)
    session.run('git', 'pull', '--rebase', external=True)
    session.run('git', 'tag', version, external=True)
    session.run('git', 'push', 'origin', version, external=True)


@nox.session(python=False)
def diagrams(session: nox.Session) -> None:
    """Render the D2 sources of the architecture documentation to the SVG files the docs embed.

    Arguments:
        session: The nox session.
    """
    for source in sorted(DIAGRAMS.glob('*.d2')):
        # `_style.d2` and `legend.d2` are imported by the diagrams, not diagrams themselves
        if source.name.startswith('_') or source.name == 'legend.d2':
            continue
        session.run(
            'd2',
            '--layout',
            'elk',
            '--theme',
            '0',
            '--pad',
            '24',
            str(source),
            str(source.with_suffix('.svg')),
        )


def _clean(value: object) -> object:
    """Return a table with its keys sorted and its empty fields dropped, as the Python copies keep it."""
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in sorted(value.items()) if item is not None}
    if isinstance(value, list):
        return [_clean(item) for item in value]
    return value


@nox.session(python=False)
def tables(session: nox.Session) -> None:
    """Regenerate the Python copies of the translation tables from their Lean definitions.

    A Sage-free Lean test, `VeriphyTest.Kit`, fails until the copies match the Lean tables.

    Arguments:
        session: The nox session.
    """
    with tempfile.TemporaryDirectory() as tmp:
        program = Path(tmp) / 'Gen.lean'
        program.write_text(
            'import Veriphy.Kit.Packs\n'
            '#eval IO.println (Lean.toJson Veriphy.coreTable).compress\n'
            '#eval do for p in Veriphy.shippedPacks do IO.println (Lean.toJson p.table).compress\n',
        )
        with session.chdir(LEAN):
            output = session.run('lake', 'env', 'lean', str(program), silent=True, external=True)
    lines = [json.loads(line) for line in str(output).splitlines() if line.startswith('{')]
    core, packs = lines[0], lines[1:]
    targets = [(TABLES / 'core_table.json', core)]
    targets += [(TABLES / 'packs' / f"{table['namespace']}.json", table) for table in packs]
    for path, table in targets:
        path.write_text(json.dumps(_clean(table), indent=2, ensure_ascii=False) + '\n')
        session.log(f'wrote {path}')


def _check_modules(name: str, ordered: list[str]) -> None:
    """Append a `VeriphyCheck` module after the `VeriphyCheck` modules it imports, each once."""
    if name in ordered:
        return
    for dependency in LEAN_IMPORT.findall(LEAN.joinpath(*name.split('.')).with_suffix('.lean').read_text()):
        if dependency.startswith('VeriphyCheck'):
            _check_modules(dependency, ordered)
    ordered.append(name)


@nox.session(python=False)
def bundle(session: nox.Session) -> None:
    """Bundle the VeriphyCheck library into one Lean file, `dist/VeriphyCheck.lean`, that imports mathlib only.

    A project that can't depend on Veriphy, such as a mathlib or Physlib contribution, copies the file in to use the
    checkers.

    Arguments:
        session: The nox session.
    """
    modules: list[str] = []
    for name in LEAN_IMPORT.findall((LEAN / 'VeriphyCheck.lean').read_text()):
        _check_modules(name, modules)
    imports: list[str] = []
    bodies: list[str] = []
    for name in modules:
        source = LEAN.joinpath(*name.split('.')).with_suffix('.lean').read_text()
        imports += [i for i in LEAN_IMPORT.findall(source) if not i.startswith('VeriphyCheck') and i not in imports]
        bodies.append(f'/-! ## {name} -/\n\n' + LEAN_IMPORT.sub('', source).strip() + '\n')
    header = '-- VeriphyCheck, bundled by `nox -s bundle` from the Veriphy repository; imports mathlib only.\n'
    output = Path('dist') / 'VeriphyCheck.lean'
    output.parent.mkdir(exist_ok=True)
    output.write_text(header + ''.join(f'import {i}\n' for i in imports) + '\n' + '\n'.join(bodies))
    session.log(f'wrote {output}')
