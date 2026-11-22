"""The `workflow` group: `veriphy layers workflow list`, `next <workflow> <target>` and `run <workflow> <target>`."""

import sys
from pathlib import Path

import click

from veriphy.core import StepError, find_workspace_root, resolve, workflow_entries
from veriphy.steps import load_steps
from veriphy.workflows._engine import explain, next_step, run_workflow

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
    root = _root(ctx)
    try:
        planned = next_step(root, workflow, target)
    except StepError as exc:
        sys.stderr.write(f'next: {exc}\n')
        raise SystemExit(FAILED) from exc
    sys.stdout.write(''.join(f'{line}\n' for line in explain(workflow, target, planned, load_steps(root))))


def _options(arguments: list[str]) -> dict[str, object]:
    """Return the step inputs given as `--name value` or `--name=value`, by name, a repeated one as a list."""
    found: dict[str, object] = {}
    rest = list(arguments)
    while rest:
        flag = rest.pop(0)
        if not flag.startswith('--') or flag == '--':
            message = f"expected an input as --name value, got '{flag}'"
            raise click.UsageError(message)
        name, has_value, value = flag[2:].partition('=')
        if not has_value:
            if not rest:
                message = f'the input {flag} has no value'
                raise click.UsageError(message)
            value = rest.pop(0)
        key = name.replace('-', '_')
        earlier = found.get(key)
        found[key] = value if earlier is None else [*(earlier if isinstance(earlier, list) else [earlier]), value]
    return found


@workflow.command(
    name='run',
    help="run a workflow's steps for a target until an agent step or its end; give the steps' inputs as --name value",
    context_settings={'ignore_unknown_options': True},
)
@click.argument('workflow')
@click.argument('target')
@click.argument('inputs', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def run_command(ctx: click.Context, workflow: str, target: str, inputs: tuple[str, ...]) -> None:
    """Run the workflow and print each step it ran, then what happens next."""
    try:
        lines = run_workflow(_root(ctx), workflow, target, _options(list(inputs)))
    except StepError as exc:
        sys.stderr.write(f'run: {exc}\n')
        raise SystemExit(FAILED) from exc
    sys.stdout.write(''.join(f'{line}\n' for line in lines))
