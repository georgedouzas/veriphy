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
    """Signal a failed daemon method, with a message of the form `<method>: <reason>`."""


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
