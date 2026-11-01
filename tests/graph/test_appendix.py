"""Test the verification appendix in Markdown and LaTeX."""

from collections.abc import Callable
from pathlib import Path

from veriphy.graph import appendix, latex_escape, load_graph, reason


def test_appendix_markdown_lists_every_claim(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """Give one row per claim with its levels, and the verdict and the recheck command."""
    graph = load_graph(workspace)
    run = reason(graph, fake_checker('accepted'))
    text = appendix(graph, run, 'chapter9')
    assert '| thm-9.1 | certificate | oracle-test | lemma-8.4 | KK.vacuum |  |' in text
    assert 'accepted the run with the verdict entailed (OOCert.entails_of_builtin_horn)' in text
    assert f'recheck .veriphy/graph/runs/{run.directory.name}' in text
    assert 'agent' in text


def test_appendix_latex_escapes_and_tabulates(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """Write a tabular with escaped cells and a section heading."""
    graph = load_graph(workspace)
    text = appendix(graph, reason(graph, fake_checker('accepted')), 'chapter9', 'latex')
    assert text.startswith('\\section*{Verification of chapter9}')
    assert 'KK.killing\\_form\\_value' in text
    assert '\\begin{tabular}{llllll}' in text


def test_appendix_states_unchecked_levels(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """State that the levels are unchecked in the first paragraph and in the table header."""
    graph = load_graph(workspace)
    text = appendix(graph, reason(graph, fake_checker('rejected')), 'chapter9')
    first_paragraph = text.split('\n\n')[1]
    assert 'The effective levels are unchecked' in first_paragraph
    assert 'Effective level (unchecked)' in text


def test_latex_escape_handles_specials() -> None:
    """Escape every LaTeX special character."""
    assert latex_escape('a_b & c%d #e $f') == 'a\\_b \\& c\\%d \\#e \\$f'


def test_appendix_latex_compiles(
    workspace: Path,
    fake_checker: Callable[[str], Path],
    compile_latex: Callable[[str], None],
) -> None:
    """Compile the LaTeX appendix in a minimal document."""
    graph = load_graph(workspace)
    compile_latex(appendix(graph, reason(graph, fake_checker('accepted')), 'chapter9', 'latex'))
