"""The `veriphy` command: `veriphy <verb> …` runs an operation, and `veriphy claims|agents|…` runs a program."""

import importlib
import sys
from collections.abc import Sequence

from veriphy.steps import load_steps
from veriphy.steps import main as run_verb

# programs of the layers and packs, each with its own subcommands
PROGRAMS = {
    'primitive': ('veriphy.primitives', 'list, describe or run a primitive by hand, with no record'),
    'claims': ('veriphy.claims', 'the research claim graph: extract, slice, reason, report'),
    'agents': ('veriphy.agents', 'the playbooks, recipes and templates agents follow'),
    'certificates': ('veriphy.packs.math.steps.certificates', "the project's saved certificate scripts"),
    'translations': ('veriphy.packs.math.primitives.translations', 'the Lean ↔ Sage translation entries in force'),
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
    """Return what `veriphy help` prints: the shell's verbs and programs, and Lean's verbs."""
    lines = ['Operations (veriphy <verb> …, or veriphy.run(verb, target, …) in Python):']
    lines += [f'  {name:<14}{step.kind:<10}{step.help}' for name, step in sorted(load_steps().items())]
    lines += ['  records       list the records, or show one by its digest', '', 'Programs:']
    lines += [f'  {name:<14}{about}' for name, (_, about) in PROGRAMS.items()]
    lines += ['', 'In Lean:']
    lines += [f'  {name:<14}{about}' for name, about in LEAN_VERBS.items()]
    return '\n'.join(lines) + '\n'


def main(argv: Sequence[str] | None = None) -> None:
    """Run an operation or a program, or print the help.

    Args:
        argv: The command-line arguments, `sys.argv[1:]` when `None`.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {'help', '-h', '--help'}:
        sys.stdout.write(help_text())
        return
    program = PROGRAMS.get(args[0])
    if program is not None:
        importlib.import_module(program[0]).main(args[1:])
        return
    run_verb(args)


if __name__ == '__main__':
    main()
