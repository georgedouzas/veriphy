"""The `veriphy` command: `layers` (a group per layer), `config`, `pack` (the packs and their programs), `help`."""

import importlib
import sys
from collections.abc import Sequence
from pathlib import Path

import click

from veriphy.core import find_workspace_root, pack_commands, resolve
from veriphy.core._commands import run_command
from veriphy.core._config_cli import config
from veriphy.steps import load_steps

# the layers' groups, in layer order, each loaded only when named, so `--help` imports none of them
LAYERS = {
    'primitive': ('veriphy.primitives._cli', 'primitive', 'layer 0: list, describe or run a primitive, with no record'),
    'step': ('veriphy.steps._cli', 'step_group', 'layer 1: run a step and record it, list the steps and records'),
    'claims': ('veriphy.claims._cli', 'claims', 'layer 2: the research claim graph: validate, reason, slice, …'),
    'workflow': ('veriphy.workflows._cli', 'workflow', "layer 3: the workflows, and a target's next steps"),
    'agents': ('veriphy.agents._cli', 'agents', 'layer 4: the playbooks, recipes and templates agents follow'),
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


def _import(target: str) -> click.Command | None:
    """Return the click command a `<module>:<attribute>` target names."""
    module, _, attribute = target.partition(':')
    command = getattr(importlib.import_module(module), attribute)
    return command if isinstance(command, click.Command) else None


class PackGroup(click.Group):
    """The programs one pack declares, each imported only when named; `pack_group` builds one."""

    # each program's import target and help line, by name
    programs: dict[str, tuple[str, str]]

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List the pack's programs."""
        return sorted(self.programs)

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """List the programs in the help without importing them."""
        with formatter.section('Commands'):
            formatter.write_dl(sorted((name, about) for name, (_, about) in self.programs.items()))

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Return a program by importing its module."""
        program = self.programs.get(cmd_name)
        return None if program is None else _import(program[0])


def pack_group(name: str, programs: dict[str, tuple[str, str]]) -> PackGroup:
    """Return the group of a pack's programs.

    Args:
        name: The pack's name, the group's.
        programs: Each program's import target and help line, by name.

    Returns:
        The group.
    """
    group = PackGroup(name=name, help=f"The {name} pack's programs.")
    group.programs = programs
    return group


def _root(ctx: click.Context) -> Path:
    """Return the workspace root the `veriphy` command's `--root` names."""
    return find_workspace_root(ctx.find_root().params.get('root'))


class LayersGroup(click.Group):
    """`veriphy layers`: one group per layer, each imported only when named."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List the layers' groups, in layer order."""
        return list(LAYERS)

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """List the layers' groups in layer order without importing them, some of which import SageMath."""
        with formatter.section('Commands'):
            formatter.write_dl([(name, about) for name, (_, _, about) in LAYERS.items()])

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Return a layer's group by importing its module."""
        layer = LAYERS.get(cmd_name)
        return None if layer is None else _import(f'{layer[0]}:{layer[1]}')


class PacksGroup(click.Group):
    """`veriphy pack`: `list`, and one group per selected pack that declares programs."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List `list` and the packs that declare programs."""
        return sorted({*super().list_commands(ctx), *pack_commands(resolve(_root(ctx)))})

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """List `list` and each pack's programs, without importing them."""
        rows = [(name, command.help or '') for name, command in self.commands.items()]
        programs = pack_commands(resolve(_root(ctx)))
        rows += [(pack, f"the {pack} pack's programs: {', '.join(sorted(p))}") for pack, p in programs.items()]
        with formatter.section('Commands'):
            formatter.write_dl(sorted(rows))

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Return `list`, or a pack's group of programs."""
        own = super().get_command(ctx, cmd_name)
        if own is not None:
            return own
        programs = pack_commands(resolve(_root(ctx))).get(cmd_name)
        return None if programs is None else pack_group(cmd_name, programs)


layers = LayersGroup(name='layers', help='One group per layer: primitive, step, claims, workflow, agents.')
packs = PacksGroup(name='pack', help="The workspace's selected packs, and the programs they declare.")


@packs.command(name='list', help='the selected packs, each after the packs it requires, with where it is')
@click.pass_context
def pack_list(ctx: click.Context) -> None:
    """List the selected packs with their directory and the packs they require."""
    for pack in resolve(_root(ctx)).packs:
        requires = pack.declared.get('requires')
        needs = ', '.join(requires) if isinstance(requires, list) else ''
        sys.stdout.write(f'{pack.name}\t{pack.directory}\t{needs}\n')


def help_text(root: Path | None = None) -> str:
    """Return what `veriphy help` prints: the groups, the workspace's steps and pack programs, and Lean's verbs.

    Args:
        root: The workspace root, found from the current directory when `None`.

    Returns:
        The text.
    """
    workspace = find_workspace_root(root)
    lines = ['Layers (veriphy layers <layer> …):']
    lines += [f'  {name:<14}{about}' for name, (_, _, about) in LAYERS.items()]
    lines += ['', 'Steps (veriphy layers step <name> …, or veriphy.run(name, target, …) in Python):']
    steps = load_steps(workspace)
    lines += [f'  {name:<14}{step.kind:<10}{step.help}' for name, step in sorted(steps.items())]
    for pack, programs in sorted(pack_commands(resolve(workspace)).items()):
        lines += ['', f'The {pack} pack (veriphy pack {pack} <program> …):']
        lines += [f'  {name:<14}{about}' for name, (_, about) in sorted(programs.items())]
    lines += ['', 'In Lean:']
    lines += [f'  {name:<14}{about}' for name, about in LEAN_VERBS.items()]
    return '\n'.join(lines) + '\n'


ROOT = click.Option(
    ['--root'],
    type=click.Path(path_type=Path),
    default=None,
    help='the workspace root (found by default)',
    # before `--help`, which is eager too, so the help lists the packs of the workspace given
    is_eager=True,
)
veriphy = click.Group(name='veriphy', params=[ROOT], help='Veriphy: its layers, its configuration and its packs.')
veriphy.add_command(layers)
veriphy.add_command(config)
veriphy.add_command(packs)


@veriphy.command(name='help', help='the layers, steps, pack programs and Lean verbs')
@click.pass_context
def help_command(ctx: click.Context) -> None:
    """Print the groups, the steps, the packs' programs and Lean's verbs."""
    sys.stdout.write(help_text(ctx.find_root().params.get('root')))


def main(argv: Sequence[str] | None = None) -> None:
    """Run a command of a layer, the configuration or a pack, or print the help.

    Args:
        argv: The command-line arguments, `sys.argv[1:]` when `None`.
    """
    run_command(veriphy, argv, 'veriphy')


if __name__ == '__main__':
    main()
