"""List and show the translation and rewrite entries in force for a project, by namespace."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from veriphy.core import TableError, find_workspace_root, project_dir
from veriphy.toolkit import SHIPPED_PACKS, Table, load_core_table, load_pack, parse_table

TRANSLATIONS_DIR = 'translations'
PROJECT_NAMESPACE = 'project'
NOT_FOUND = 1


def _load_project(root: Path) -> tuple[list[tuple[str, Table]], list[str]]:
    """Return the project's tables with their file names, and an error line for each file that does not parse."""
    directory = project_dir(root) / TRANSLATIONS_DIR
    tables: list[tuple[str, Table]] = []
    errors: list[str] = []
    for path in sorted(directory.glob('*.json')) if directory.is_dir() else []:
        source = f'{TRANSLATIONS_DIR}/{path.name}'
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            tables.append((source, parse_table(data, source, PROJECT_NAMESPACE)))
        except json.JSONDecodeError as exc:
            errors.append(f'{source}: not valid JSON: {exc}')
        except TableError as exc:
            errors.append(str(exc))
    return tables, errors


def _sources(root: Path, *, everything: bool) -> tuple[list[tuple[str, Table]], list[str]]:
    """Return the tables to list, with their sources: the project's, preceded by the core and packs when asked."""
    project, errors = _load_project(root)
    if not everything:
        return project, errors
    shipped = [('core_table.json', load_core_table())]
    shipped += [(f'packs/{name}.json', load_pack(name)) for name in SHIPPED_PACKS]
    return shipped + project, errors


def _condition_text(table: Table, lean: str) -> str:
    """Return a function entry's conditions, in the schema's terms."""
    for entry in table.functions:
        if entry.lean == lean:
            parts = [f'{c.kind} #{c.arg}' if c.arg is not None else f'{c.lhs} ≤ {c.rhs}' for c in entry.conditions]
            return ', '.join(parts)
    return ''


def _shipped_owners() -> dict[str, str]:
    """Return the namespace of the core or pack entry for each Lean constant they translate."""
    owners: dict[str, str] = {}
    for table in (load_core_table(), *(load_pack(name) for name in SHIPPED_PACKS)):
        for lean in (*(f.lean for f in table.functions), *(c.lean for c in table.constants), *table.coercions):
            owners.setdefault(lean, table.namespace)
    return owners


def _lines(tables: list[tuple[str, Table]]) -> list[str]:
    """Return one catalog line per entry: namespace, file, Lean name, Sage name or rewrite, conditions."""
    owners = _shipped_owners()
    lines = []
    for source, table in tables:
        for f in table.functions:
            role = f' ({f.role})' if f.role else ''
            line = f'{table.namespace} | {source} | {f.lean} | {f.sage}{role} | {_condition_text(table, f.lean)}'
            owner = owners.get(f.lean)
            if table.namespace == PROJECT_NAMESPACE and owner is not None:
                line += f'  (conflicts with the {owner} entry; not loaded)'
            lines.append(line)
        lines += [f'{table.namespace} | {source} | {c.lean} | {c.sage} | ' for c in table.constants]
        for r in table.rewrites:
            arrow = '← ' if r.reverse else ''
            lines.append(
                f'{table.namespace} | {source} | rw [{arrow}{r.lemma}] | {", ".join(r.functions)} | '
                + ', '.join(r.side),
            )
    return lines


def _find(tables: list[tuple[str, Table]], name: str) -> str | None:
    """Return the full description of the entry for a Lean constant or lemma."""
    for source, table in tables:
        for entry in (*table.functions, *table.constants, *table.rewrites):
            key = getattr(entry, 'lean', None) or getattr(entry, 'lemma', None)
            if key == name:
                return f'namespace: {table.namespace}\nfile: {source}\n{entry}\n'
    return None


def _parser() -> argparse.ArgumentParser:
    """Return the command-line parser: `list [--all] [--root DIR]` and `show <name> [--root DIR]`."""
    parser = argparse.ArgumentParser(prog='python -m veriphy.translations')
    commands = parser.add_subparsers(dest='command', required=True)
    listing, showing = commands.add_parser('list'), commands.add_parser('show')
    for command in (listing, showing):
        command.add_argument('--root', type=Path, default=None, help='the Lean workspace root (found by default)')
        command.add_argument('--all', action='store_true', help='include the core table and the shipped packs')
    showing.add_argument('name', help='a Lean constant or lemma name')
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """List the translation entries in force for the project, or show one.

    Args:
        argv: The command-line arguments, `sys.argv[1:]` when `None`.

    Raises:
        SystemExit: With status 1 when `show` finds no entry of that name, and 2 on bad usage.
    """
    args = _parser().parse_args(list(sys.argv[1:] if argv is None else argv))
    tables, errors = _sources(find_workspace_root(args.root), everything=args.all or args.command == 'show')
    for error in errors:
        sys.stderr.write(f'invalid: {error}\n')
    if args.command == 'list':
        sys.stdout.write(''.join(f'{line}\n' for line in _lines(tables)))
        return
    found = _find(tables, args.name)
    if found is None:
        sys.stderr.write(f"no translation entry for '{args.name}'\n")
        raise SystemExit(NOT_FOUND)
    sys.stdout.write(found)
