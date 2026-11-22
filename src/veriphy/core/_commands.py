"""Run a click command from a list of arguments, as a program's `main(argv)` does, keeping its exit status."""

import sys
from collections.abc import Sequence

import click

from veriphy.core._errors import VeriphyError

FAILED = 1


def run_command(command: click.Command, argv: Sequence[str] | None, prog_name: str) -> None:
    """Run a click command on arguments, exiting with its status when it is not 0.

    Args:
        command: The command or group.
        argv: The arguments, `sys.argv[1:]` when `None`.
        prog_name: The program's name in usage and help, as `veriphy layers claims`.

    Raises:
        SystemExit: With the command's status when it is not 0, 2 on bad usage, and 1 on a Veriphy or file error.
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        command.main(args=arguments, prog_name=prog_name, standalone_mode=False)
    except click.exceptions.Exit as exc:
        if exc.exit_code:
            raise SystemExit(exc.exit_code) from exc
    except click.ClickException as exc:
        exc.show()
        raise SystemExit(exc.exit_code) from exc
    except (VeriphyError, OSError) as exc:
        sys.stderr.write(f'error: {exc}\n')
        raise SystemExit(FAILED) from exc
