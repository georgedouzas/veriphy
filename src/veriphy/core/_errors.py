"""Define the named exceptions veriphy raises."""


class VeriphyError(Exception):
    """Signal a failure inside veriphy."""


class ParamError(VeriphyError):
    """Signal a request parameter that failed validation.

    Args:
        param: The name of the parameter.
        reason: What is wrong with the parameter.
    """

    def __init__(self, param: str, reason: str) -> None:
        message = f"parameter '{param}': {reason}"
        super().__init__(message)
        self.param = param
        self.reason = reason


class MethodError(VeriphyError):
    """Signal a failed Sage method, with a message of the form `<method>: <reason>`."""


class CertificateError(VeriphyError):
    """Signal that no certificate exists or that a supplied certificate is malformed."""


class EncodingError(VeriphyError):
    """Signal a method result that has no exact JSON encoding."""


class ScriptError(VeriphyError):
    """Signal a Sage script that failed, carrying the output it printed before failing.

    Args:
        reason: Why the script failed.
        stdout: The output the script printed, possibly empty.
    """

    def __init__(self, reason: str, stdout: str) -> None:
        message = reason + (f'\n--- script stdout ---\n{stdout}' if stdout else '')
        super().__init__(message)
        self.reason = reason
        self.stdout = stdout


class TableError(VeriphyError):
    """Signal a translation-table file that does not follow the schema.

    Args:
        source: The file the table came from.
        field: The field at fault.
        reason: What is wrong with it.
    """

    def __init__(self, source: str, field: str, reason: str) -> None:
        message = (
            f"{source}: {reason} '{field}'" if reason == 'missing field' else f"{source}: field '{field}' {reason}"
        )
        super().__init__(message)
        self.source = source
        self.field = field
        self.reason = reason


class GraphError(VeriphyError):
    """Signal a research graph that cannot be loaded, reasoned over or written."""


class ReasonerMissingError(GraphError):
    """Signal that the claim graph's reasoner is not set up, and automatic setup is off or failed.

    Args:
        module: The module that could not be imported.
    """

    def __init__(self, module: str) -> None:
        message = (
            f"the claim graph's reasoner ('{module}') is not set up: run `veriphy layers claims checker build`, "
            'or unset VERIPHY_GRAPH_SETUP so the first command that needs it sets it up'
        )
        super().__init__(message)
        self.module = module


class CheckerError(GraphError):
    """Signal that `oo-horn`, the certificate checker, could not be built or run."""


class RecordError(VeriphyError):
    """Signal a step record that cannot be written or read, such as an attempt to overwrite one."""


class StepError(VeriphyError):
    """Signal a step that broke the step contract, such as an evidence step that returned a level."""


class ToolError(VeriphyError):
    """Signal an external program that is not installed, could not start or did not finish in time."""


class PrimitiveError(VeriphyError):
    """Signal a primitive that cannot run as asked: unknown, refused by a schema, or its tool missing or failing."""


class PinError(PrimitiveError):
    """Signal a tool that does not match its pin, so the primitive does not run."""


class PackError(VeriphyError):
    """Signal a pack that cannot be loaded: no such pack, or a `pack.yaml` that does not read."""
