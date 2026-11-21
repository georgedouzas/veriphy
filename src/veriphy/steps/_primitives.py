"""Turn a primitive's output into a step's outcome: its status, its outputs, and the versions of its tools."""

from pathlib import Path

from veriphy.core._version import __version__
from veriphy.primitives import TOOLS_KEY, workspace_registry
from veriphy.steps._runner import Outcome


def call_primitive(root: Path, name: str, inputs: dict[str, object], status: str = 'status') -> Outcome:
    """Call a primitive of the workspace's packs and return the outcome of a step that wraps it.

    Args:
        root: The workspace root, whose configuration selects the primitives.
        name: The primitive.
        inputs: Its input.
        status: The output field that holds the status.

    Returns:
        The outcome: the status, the other outputs, and each tool's version with Veriphy's.
    """
    output = dict(workspace_registry(root.resolve()).call(name, inputs))
    used = output.pop(TOOLS_KEY, [])
    tools = {str(t['name']): str(t['version']) for t in used if isinstance(t, dict)} if isinstance(used, list) else {}
    value = str(output.pop(status, 'failed'))
    return Outcome(value, output, {**tools, 'veriphy': __version__})
