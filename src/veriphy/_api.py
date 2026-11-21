"""The operation API: `veriphy.run(verb, target, **inputs)`, the same operation the shell runs as `veriphy <verb>`."""

from dataclasses import replace
from pathlib import Path

from veriphy.core import StepError, find_workspace_root
from veriphy.steps import Result, load_steps, resolve_verb, run_step


def run(
    verb: str,
    target: str | None = None,
    *,
    root: Path | None = None,
    rerun: bool = False,
    **inputs: object,
) -> Result:
    """Run an operation and return its result, replaying its record when the same inputs were run before.

    Args:
        verb: The operation, as `check`, `level` or `meaning`.
        target: What it acts on: the value of the step's first argument, such as a file or a module.
        root: The workspace root, found from the current directory by default.
        rerun: Run even when a final record of the same inputs exists.
        **inputs: The step's other parameters, by name.

    Returns:
        The result, with its record.

    Raises:
        StepError: If no step has the verb's name.
    """
    steps = load_steps()
    name = resolve_verb(verb)
    step = steps.get(name)
    if step is None:
        message = f"no operation is named '{verb}': the operations are {', '.join(sorted(steps))}"
        raise StepError(message)
    params = dict(inputs)
    if target is not None and step.arguments:
        params[step.arguments[0].name] = target
    result = run_step(step, find_workspace_root(root), params, rerun=rerun)
    return replace(result, target=target)
