"""The `step` group: `veriphy layers step <name>` runs a step, `list` lists them, `records` shows what they wrote."""

import json
import sys
from pathlib import Path

import click

from veriphy.core import RecordError, find_workspace_root
from veriphy.steps._declared import Reported
from veriphy.steps._records import RecordStore, read_record
from veriphy.steps._registry import load_steps, step_packs
from veriphy.steps._runner import USAGE_EXIT, Argument, Params, Result, Step, exit_code, run_step
from veriphy.steps._summary import summary

NUMBER = 'NUMBER'


def _parameter(argument: Argument) -> click.Parameter:
    """Return the click parameter of one step argument: positional, an option, or a repeatable option."""
    kind = click.Choice(list(argument.choices)) if argument.choices else click.types.convert_type(argument.type)
    if not argument.option:
        return click.Argument([argument.name], type=kind, help=argument.help or None)
    flag = argument.flag or '--' + argument.name.replace('_', '-')
    return click.Option(
        [flag, argument.name],
        type=kind,
        default=None if argument.many else argument.default,
        multiple=argument.many,
        help=argument.help or None,
        metavar=NUMBER if argument.type is Reported else None,
    )


def _params(step: Step, values: dict[str, object]) -> Params:
    """Return a step's parameters from the command's values, leaving out those not given."""
    names = [argument.name for argument in step.arguments]
    return {name: values[name] for name in names if values.get(name) not in (None, ())}


def step_command(step: Step, root: Path) -> click.Command:
    """Return the click command that runs a step in a workspace and prints its record.

    Args:
        step: The step.
        root: The workspace root.

    Returns:
        The command, exiting with status 1 when the step refused, found a counterexample or failed, 2 on bad input,
        and 3 when its result is unchecked or undecided.
    """

    def run(as_json: bool, rerun: bool, **values: object) -> None:
        """Run the step and print its record."""
        try:
            result = run_step(step, root, _params(step, values), rerun=rerun)
        except (RecordError, FileNotFoundError, KeyError, ValueError) as exc:
            sys.stderr.write(f'{step.name}: {exc}\n')
            raise SystemExit(USAGE_EXIT) from exc
        _print(result, as_json, root, step.arguments[0].name if step.arguments else None)
        code = exit_code(result.record.status)
        if code:
            raise SystemExit(code)

    shared = [
        click.Option(['--json', 'as_json'], is_flag=True, help='print the record as JSON, and nothing else'),
        click.Option(['--rerun'], is_flag=True, help='run even when a final record of the inputs exists'),
    ]
    return click.Command(step.name, callback=run, params=[*map(_parameter, step.arguments), *shared], help=step.help)


class StepGroup(click.Group):
    """A command group with one command per step of the workspace that `veriphy --root` names, and its own."""

    def _steps(self, ctx: click.Context) -> tuple[Path, dict[str, Step]]:
        """Return the workspace root and its steps."""
        root = find_workspace_root(ctx.find_root().params.get('root'))
        return root, load_steps(root)

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List the group's own commands and the workspace's steps."""
        return sorted({*super().list_commands(ctx), *self._steps(ctx)[1]})

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Return a command of the group, or the step of that name."""
        own = super().get_command(ctx, cmd_name)
        if own is not None:
            return own
        root, steps = self._steps(ctx)
        step = steps.get(cmd_name)
        return None if step is None else step_command(step, root)


def _print(result: Result, as_json: bool, root: Path, first: str | None) -> None:
    """Print a step's record as JSON, or say what the step did."""
    if as_json:
        sys.stdout.write(json.dumps(result.record.to_json(), indent=2, sort_keys=True, ensure_ascii=False) + '\n')
        return
    sys.stdout.write(summary(result, root, first))


@click.command(name='records', help='list the records, or show one by its digest')
@click.argument('digest', required=False)
@click.option('--step', default=None, help='only this step')
@click.pass_context
def records(ctx: click.Context, digest: str | None, step: str | None) -> None:
    """List the records, or show the one a digest names."""
    root = find_workspace_root(ctx.find_root().params.get('root'))
    paths = RecordStore(root).all(step)
    if digest is None:
        for path in paths:
            record = read_record(path)
            sys.stdout.write(f'{record.step}\t{record.status}\t{path.stem}\n')
        return
    matches = [path for path in paths if path.stem.startswith(digest)]
    if len(matches) != 1:
        sys.stderr.write(f"{len(matches)} records match '{digest}'\n")
        raise SystemExit(USAGE_EXIT)
    sys.stdout.write(matches[0].read_text())


@click.command(name='list', help="the workspace's steps, with their kind and the pack that defines each")
@click.pass_context
def list_command(ctx: click.Context) -> None:
    """List the workspace's steps."""
    root = find_workspace_root(ctx.find_root().params.get('root'))
    steps = load_steps(root)
    owners = step_packs(root)
    for name, step in sorted(steps.items()):
        sys.stdout.write(f'{name}\t{step.kind}\t{owners.get(name, "")}\t{step.help}\n')


step_group = StepGroup(name='step', help='Run a step of the workspace and record it, or list the steps and records.')
step_group.add_command(records)
step_group.add_command(list_command)
