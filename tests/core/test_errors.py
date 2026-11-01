"""Test the named exceptions."""

from veriphy.core import GraphError, GraphExtraMissingError, ParamError, ScriptError, VeriphyError


def test_param_error_names_parameter() -> None:
    """Name the parameter and the reason in the message."""
    error = ParamError('vars', 'missing')
    assert str(error) == "parameter 'vars': missing"
    assert (error.param, error.reason) == ('vars', 'missing')
    assert isinstance(error, VeriphyError)


def test_script_error_appends_stdout() -> None:
    """Append the script's output to the message only when there is some."""
    assert str(ScriptError('boom', '')) == 'boom'
    assert str(ScriptError('boom', 'step 1\n')) == 'boom\n--- script stdout ---\nstep 1\n'


def test_graph_extra_missing_names_install_commands() -> None:
    """Name the missing module and both install commands."""
    error = GraphExtraMissingError('pyoxigraph')
    assert error.module == 'pyoxigraph'
    assert "veriphy[graph]" in str(error)
    assert 'checker build' in str(error)
    assert isinstance(error, GraphError)
