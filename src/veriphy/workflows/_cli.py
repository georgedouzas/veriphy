"""The `workflow` group: `veriphy layers workflow list`, `next <workflow> <target>` and `run <workflow> <target>`."""

import sys
from pathlib import Path

import click

from veriphy.core import StepError, find_workspace_root, resolve, workflow_entries
from veriphy.workflows._engine import next_step, run_workflow

FAILED = 1


def _root(ctx: click.Context) -> Path:
    """Return the workspace root the `veriphy` group's `--root` names."""
    return find_workspace_root(ctx.find_root().params.get('root'))


@click.group(name='workflow', help="The workspace's workflows: list them, and compute or run a target's next steps.")
def workflow() -> None:
    """Group the workflow commands."""


@workflow.command(name='list', help="the workspace's workflows, with their steps in order")
@click.pass_context
def list_command(ctx: click.Context) -> None:
    """List each workflow with its steps."""
    for name, declared in sorted(resolve(_root(ctx)).section('workflows').items()):
        steps = ', '.join(step for step, _ in workflow_entries(declared))
        sys.stdout.write(f'{name}\t{steps}\n')


@workflow.command(name='next', help="the workflow's next step for a target, from its records")
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


@workflow.command(name='run', help="run a workflow's steps for a target until an agent step or its end")
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
