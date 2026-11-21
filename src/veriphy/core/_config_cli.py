"""The config command: `veriphy config show` and `check`, on the workspace's resolved configuration."""

import json
import sys
from collections.abc import Sequence
from pathlib import Path

import click

from veriphy.core._commands import run_command
from veriphy.core._config import Resolved, check, resolve
from veriphy.core._errors import PackError
from veriphy.core._project import find_workspace_root


@click.group(name='config', help="The workspace's resolved configuration.")
@click.option('--root', type=click.Path(path_type=Path), default=None, help='the workspace root (found by default)')
@click.pass_context
def config(ctx: click.Context, root: Path | None) -> None:
    """Resolve the workspace's configuration for the subcommand."""
    try:
        ctx.obj = resolve(find_workspace_root(root))
    except PackError as exc:
        sys.stderr.write(f'config: {exc}\n')
        raise SystemExit(1) from exc


@config.command(help='the resolved configuration, with the pack or file each entry comes from')
@click.pass_obj
def show(resolved: Resolved) -> None:
    """Print the resolved configuration and each entry's source."""
    shown = {'packs': [p.name for p in resolved.packs], 'config': resolved.config, 'sources': resolved.sources}
    sys.stdout.write(json.dumps(shown, indent=2, sort_keys=True, ensure_ascii=False) + '\n')


@config.command(name='check', help='refuse collisions and references that do not resolve')
@click.pass_obj
def check_command(resolved: Resolved) -> None:
    """Exit with status 1 on a collision or a reference that does not resolve."""
    problems = check(resolved)
    for problem in problems:
        sys.stderr.write(f'config: {problem}\n')
    if problems:
        raise SystemExit(1)
    sys.stdout.write(f'config: {len(resolved.packs)} packs, no problems\n')


def main(argv: Sequence[str] | None = None) -> None:
    """Show or check the resolved configuration of a workspace.

    Args:
        argv: The command-line arguments, `sys.argv[1:]` when `None`.
    """
    run_command(config, argv, 'veriphy config')
