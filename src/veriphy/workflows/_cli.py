"""The workflow commands: `veriphy next <workflow> <target>` and `veriphy run <workflow> <target>`."""

import sys
from pathlib import Path

import click

from veriphy.core import StepError, find_workspace_root
from veriphy.workflows._engine import next_step, run_workflow

FAILED = 1


def _root(ctx: click.Context) -> Path:
    """Return the workspace root the `veriphy` group's `--root` names."""
    return find_workspace_root(ctx.find_root().params.get('root'))


@click.command(name='next', help="the workflow's next step for a target, from its records")
@click.argument('workflow')
@click.argument('target')
@click.pass_context
def next_command(ctx: click.Context, workflow: str, target: str) -> None:
    """Print the next step, or why the workflow stopped or finished."""
    try:
        planned = next_step(_root(ctx), workflow, target)
    except StepError as exc:
        sys.stderr.write(f'next: {exc}\n')
        raise SystemExit(FAILED) from exc
    who = ' (an agent step)' if planned.agent else ''
    sys.stdout.write(f'{planned.step}{who}: {planned.reason}\n' if planned.step else f'{planned.reason}\n')


@click.command(name='run', help="run a workflow's steps for a target until an agent step or its end")
@click.argument('workflow')
@click.argument('target')
@click.option('--input', 'given', multiple=True, help='a step input, as name=value; repeat for several')
@click.pass_context
def run_command(ctx: click.Context, workflow: str, target: str, given: tuple[str, ...]) -> None:
    """Run the workflow and print each step it ran, then what happens next."""
    inputs = dict(item.split('=', 1) for item in given if '=' in item)
    try:
        lines = run_workflow(_root(ctx), workflow, target, inputs)
    except StepError as exc:
        sys.stderr.write(f'run: {exc}\n')
        raise SystemExit(FAILED) from exc
    sys.stdout.write(''.join(f'{line}\n' for line in lines))
