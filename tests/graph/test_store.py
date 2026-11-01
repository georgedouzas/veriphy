"""Test loading a project's research graph, its provenance, and editing its source files."""

from pathlib import Path

import pytest

from veriphy.core import GraphError
from veriphy.graph import confirm, graph_dir, lean_iri, load_graph, resolve_term, source_iri, vp

SOURCES = Path('.veriphy') / 'graph' / 'sources'


def test_load_graph_reads_every_file_with_counts(workspace: Path) -> None:
    """Read the sources and the export, and count the triples of each file."""
    graph = load_graph(workspace)
    names = {path.name: count for path, count in graph.files}
    assert set(names) == {'chapter9.agent.ttl', 'arXiv:0808.3236.human.ttl', 'export.nt'}
    assert sum(names.values()) == len(graph.assertions)


def test_load_graph_finds_the_root_from_a_subdirectory(workspace: Path) -> None:
    """Resolve `.veriphy/` from a subdirectory of the workspace."""
    sub = workspace / 'Project' / 'Sub'
    sub.mkdir(parents=True)
    assert load_graph(sub).root == workspace


def test_load_graph_records_provenance(workspace: Path) -> None:
    """Give each assertion the provenance its file names."""
    graph = load_graph(workspace)
    claim = source_iri('chapter9', 'lemma-5.2')
    assert graph.provenance((claim, vp('assumes'), source_iri('chapter9', 'half'))) == {'agent'}
    assert graph.provenance((lean_iri('KK.vacuum'), vp('hasLevel'), vp('certificate'))) == {'lean'}


def test_load_graph_names_a_syntax_error(workspace: Path) -> None:
    """Name the file and the line of a Turtle syntax error."""
    (workspace / SOURCES / 'chapter3.agent.ttl').write_text('@prefix vp: <urn:veriphy:vocabulary#> .\n<#a> vp:uses .\n')
    with pytest.raises(GraphError, match=r'chapter3\.agent\.ttl: .*line 2'):
        load_graph(workspace)


def test_load_graph_refuses_a_file_without_provenance(workspace: Path) -> None:
    """Ask for the name `<source>.<provenance>.ttl`."""
    (workspace / SOURCES / 'chapter3.ttl').write_text('')
    with pytest.raises(GraphError, match=r'<source>\.<provenance>\.ttl'):
        load_graph(workspace)


def test_load_graph_refuses_an_undeclared_term(workspace: Path) -> None:
    """Name a Veriphy-namespace property the vocabulary does not declare, and its file."""
    (workspace / SOURCES / 'chapter3.agent.ttl').write_text(
        '@prefix vp: <urn:veriphy:vocabulary#> .\n<#a> vp:dependsOn <#b> .\n',
    )
    with pytest.raises(GraphError, match=r'chapter3\.agent\.ttl: .*dependsOn.* not declared'):
        load_graph(workspace)


def test_load_graph_refuses_blank_nodes(workspace: Path) -> None:
    """Ask for an IRI instead of a blank node."""
    (workspace / SOURCES / 'chapter3.agent.ttl').write_text(
        '@prefix vp: <urn:veriphy:vocabulary#> .\n<#a> vp:uses [ vp:uses <#b> ] .\n',
    )
    with pytest.raises(GraphError, match='blank nodes are not allowed'):
        load_graph(workspace)


def test_load_graph_follows_links_across_sources(workspace: Path) -> None:
    """Resolve a `uses` into another source's node."""
    (workspace / SOURCES / 'chapter3.agent.ttl').write_text(
        '@prefix vp: <urn:veriphy:vocabulary#> .\n<#eq-3.12> vp:uses <urn:veriphy:source:arXiv:0808.3236#thm-2> .\n',
    )
    graph = load_graph(workspace)
    assert graph.objects(source_iri('chapter3', 'eq-3.12'), 'uses') == (source_iri('arXiv:0808.3236', 'thm-2'),)


def test_resolve_term_reads_short_terms() -> None:
    """Resolve labels, other sources, Lean names, vocabulary predicates and full IRIs."""
    assert resolve_term('thm-1', 'ch') == source_iri('ch', 'thm-1')
    assert resolve_term('lean:KK.vacuum', 'ch') == lean_iri('KK.vacuum')
    assert resolve_term('<urn:x>', 'ch') == '<urn:x>'
    assert resolve_term('vp:uses', 'ch', predicate=True) == vp('uses')


def test_confirm_moves_exactly_one_triple(workspace: Path) -> None:
    """Move one triple from the agent file to the human file, and leave the others."""
    triple = (source_iri('chapter9', 'lemma-5.2'), vp('assumes'), source_iri('chapter9', 'half'))
    before = load_graph(workspace)
    path = confirm(workspace, 'chapter9', triple)
    after = load_graph(workspace)
    assert path == graph_dir(workspace) / 'sources' / 'chapter9.human.ttl'
    assert after.provenance(triple) == {'human'}
    assert after.triples() == before.triples()
    assert len(after.assertions) == len(before.assertions)


def test_confirm_refuses_a_triple_the_agent_file_lacks(workspace: Path) -> None:
    """Name the agent file when it does not assert the triple."""
    triple = (source_iri('chapter9', 'eq-4.1'), vp('uses'), source_iri('chapter9', 'thm-9.1'))
    with pytest.raises(GraphError, match='does not assert'):
        confirm(workspace, 'chapter9', triple)
