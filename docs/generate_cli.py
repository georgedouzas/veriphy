"""Generate the command reference from the CLI, in a workspace that selects every shipped pack."""

import tempfile
from collections.abc import Iterator
from pathlib import Path

import click
import mkdocs_gen_files

from veriphy.__main__ import veriphy
from veriphy.core import BUILTIN_PACKS
from veriphy.steps._registry import step_packs

PAGE = 'overview/commands.md'
STEP_GROUP = 'veriphy layers step'
PIPE = '\\|'
HELP = '--help'
TOP_ORDER = ('layers', 'pack', 'config', 'help')
STEPS = '<!-- steps -->'
UNAVAILABLE = 'needs SageMath, which this build lacks: the [math pack](../packs/math.md#commands) lists its commands'
INTRO = """# Commands

Every command and option, generated from the CLI. The [tutorial](tutorial.md) shows each command in use on one example,
and `--help` after any command prints the same text.

`veriphy --root <dir> …` runs a command in another workspace. A step exits with status 0 when it accepts, 1 when it
refuses or finds a counterexample, 2 on wrong usage, and 3 when the result is unchecked or undecided.
"""


def walk(command: click.Command, ctx: click.Context) -> Iterator[tuple[click.Command, click.Context]]:
    """Yield every command below a command, with its context, in the CLI's order."""
    yield command, ctx
    if isinstance(command, click.Group):
        for name in command.list_commands(ctx):
            try:
                child = command.get_command(ctx, name)
            except ImportError:
                child = click.Command(name, help=UNAVAILABLE)
            if child is not None:
                yield from walk(child, click.Context(child, parent=ctx, info_name=name))


def escape(text: str) -> str:
    """Return help text for a Markdown table: pipes and brackets escaped, so they read as text."""
    return text.replace('|', PIPE).replace('[', '\\[').replace(']', '\\]')


def options(command: click.Command, ctx: click.Context) -> list[str]:
    """Return the Markdown table of a command's arguments and options."""
    rows = []
    for param in command.get_params(ctx):
        record = param.get_help_record(ctx)
        if isinstance(param, click.Argument):
            about = escape(str(getattr(param, 'help', None) or ''))
            rows.append(f'| `{param.human_readable_name}` | {about} |')
        elif record is not None and HELP not in param.opts:
            about = escape(record[1])
            rows.append(f'| `{record[0]}` | {about} |')
    return ['| Argument or option | Help |', '|---|---|', *rows, ''] if rows else []


def section(command: click.Command, ctx: click.Context, level: int) -> list[str]:
    """Return a command's section: its heading, its help, its usage and its options."""
    path = ctx.command_path
    usage = ' '.join(command.collect_usage_pieces(ctx))
    help_text = (command.help or command.short_help or '').strip()
    lines = [f'{"#" * level} `{path}`', '']
    if help_text:
        lines += [help_text[0].upper() + help_text[1:].rstrip('.') + '.', '']
    if not isinstance(command, click.Group) and command.help != UNAVAILABLE:
        lines += ['```text', f'{path} {usage}'.rstrip(), '```', '', *options(command, ctx)]
    return lines


def write_page(root: Path) -> str:
    """Return the page for the workspace at `root`: the commands by group in layer order, and the steps by pack."""
    ctx = click.Context(veriphy, info_name='veriphy')
    ctx.params['root'] = root
    owners = step_packs(root)
    groups: dict[str, list[str]] = {}
    steps: dict[str, list[str]] = {}
    for command, context in walk(veriphy, ctx):
        words = context.command_path.split()
        if len(words) == 1:
            continue
        if context.command_path.startswith(f'{STEP_GROUP} ') and context.info_name in owners:
            steps.setdefault(owners[context.info_name], []).extend(section(command, context, 5))
        else:
            groups.setdefault(words[1], []).extend(section(command, context, min(len(words), 4)))
            if context.command_path == STEP_GROUP:
                groups[words[1]].append(STEPS)
    by_pack = ['#### The steps of each pack', '', 'A workspace has the steps of the packs it selects.', '']
    for pack in BUILTIN_PACKS:
        if pack in steps:
            by_pack += [f'##### The `{pack}` pack', '', *steps[pack]]
    order = [name for name in TOP_ORDER if name in groups] + sorted(set(groups) - set(TOP_ORDER))
    lines = [INTRO, *(line for name in order for line in groups[name])]
    body = '\n'.join(lines)
    generic_end = body.index('### `veriphy layers claims`')
    body = body[:generic_end] + '\n'.join(by_pack) + '\n' + body[generic_end:]
    return body.replace(STEPS + '\n', '') + '\n'


with tempfile.TemporaryDirectory() as tmp:
    Path(tmp, 'veriphy.yaml').write_text(f'version: 1\npacks: [{", ".join(BUILTIN_PACKS)}]\n')
    with mkdocs_gen_files.open(PAGE, 'w') as page:
        page.write(write_page(Path(tmp)))
