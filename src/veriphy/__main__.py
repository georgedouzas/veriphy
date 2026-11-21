"""The `veriphy` command: one click group of the workspace's operations and the layers' and packs' programs."""

import importlib
import sys
from collections.abc import Sequence

import click

from veriphy.core import find_workspace_root
from veriphy.core._commands import run_command
from veriphy.steps import load_steps
from veriphy.steps._cli import ROOT, StepGroup, records, steps_command

# programs of the layers and packs, each a click group, loaded only when named (some import SageMath)
PROGRAMS = {
    'config': ('veriphy.core._config_cli', 'config', "the workspace's resolved configuration: show, check"),
    'primitive': ('veriphy.primitives._cli', 'primitive', 'list, describe or run a primitive by hand, with no record'),
    'claims': ('veriphy.claims._cli', 'claims', 'the research claim graph: validate, reason, slice, appendix, …'),
    'agents': ('veriphy.agents._cli', 'agents', 'the playbooks, recipes and templates agents follow'),
    'next': ('veriphy.workflows._cli', 'next_command', "a workflow's next step for a target, from its records"),
    'run': ('veriphy.workflows._cli', 'run_command', "run a workflow's steps for a target until an agent step"),
    'certificates': (
        'veriphy.packs.math.steps.certificates._catalog',
        'certificates',
        "the project's saved certificate scripts",
    ),
    'translations': (
        'veriphy.packs.math.primitives.translations._catalog',
        'translations',
        'the Lean ↔ Sage translation entries in force',
    ),
}
# verbs Lean runs, as `veriphy <verb>` (a tactic, on the goal) and `#veriphy <verb>` (a command, on a claim)
LEAN_VERBS = {
    'certify': 'veriphy certify "<script>": Sage finds a certificate, Lean checks the proof built from it',
    'search': 'veriphy search "<script>": run a script for guidance, closing nothing',
    'meaning': '#veriphy meaning c: test the statement of c at seeded values',
    'test': '#veriphy test c "<script>": check c at instances, by the kernel or Sage',
    'level': '#veriphy level P: the level of each declaration under the prefixes P',
    'export': '#veriphy export P: the Lean claims under P, for the claim graph',
    'translate': '#veriphy translate e: how a Lean expression reaches Sage, and back',
    'translations': '#veriphy translations [check]: the translation tables in force, or a check of them',
    'coverage': '#veriphy coverage [d, …]: which goals of the declarations translate',
}


def help_text() -> str:
    """Return what `veriphy help` prints: the workspace's operations, the programs, and Lean's verbs."""
    lines = ['Operations (veriphy <verb> …, or veriphy.run(verb, target, …) in Python):']
    steps = load_steps(find_workspace_root())
    lines += [f'  {name:<14}{step.kind:<10}{step.help}' for name, step in sorted(steps.items())]
    lines += ['  records       list the records, or show one by its digest', '', 'Programs:']
    lines += [f'  {name:<14}{about}' for name, (_, _, about) in PROGRAMS.items()]
    lines += ['', 'In Lean:']
    lines += [f'  {name:<14}{about}' for name, about in LEAN_VERBS.items()]
    return '\n'.join(lines) + '\n'


class Veriphy(StepGroup):
    """The `veriphy` group: the workspace's operations, `records`, `help`, and the programs, loaded when named."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List the operations, `records`, `help` and the programs."""
        return sorted({*super().list_commands(ctx), *PROGRAMS})

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """List the commands in the help without importing the programs, some of which import SageMath."""
        root = find_workspace_root(ctx.params.get('root'))
        rows = [(name, step.help) for name, step in load_steps(root).items()]
        rows += [(name, command.help or '') for name, command in self.commands.items()]
        rows += [(name, about) for name, (_, _, about) in PROGRAMS.items()]
        with formatter.section('Commands'):
            formatter.write_dl(sorted(rows))

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Return a program by importing its module, or an operation or own command."""
        program = PROGRAMS.get(cmd_name)
        if program is None:
            return super().get_command(ctx, cmd_name)
        command = getattr(importlib.import_module(program[0]), program[1])
        return command if isinstance(command, click.Command) else None


veriphy = Veriphy(name='veriphy', params=[ROOT], help='Run a Veriphy operation and record it, or a program.')
veriphy.add_command(records)
veriphy.add_command(steps_command)


@veriphy.command(name='help', help='the operations, programs and Lean verbs')
def help_command() -> None:
    """Print the operations, the programs and Lean's verbs."""
    sys.stdout.write(help_text())


def main(argv: Sequence[str] | None = None) -> None:
    """Run an operation or a program, or print the help.

    Args:
        argv: The command-line arguments, `sys.argv[1:]` when `None`.
    """
    run_command(veriphy, argv, 'veriphy')


if __name__ == '__main__':
    main()
