"""Test the research playbook: its commands exist, its Turtle templates load, and both skill copies point at it."""

import re
from pathlib import Path

import pytest

from veriphy.graph import COMMANDS, load_graph

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = [
    ROOT / 'prompts' / 'research.md',
    *sorted((ROOT / 'prompts' / 'research').glob('*.md')),
    ROOT / 'skills' / 'research' / 'SKILL.md',
    ROOT / '.claude' / 'skills' / 'research' / 'SKILL.md',
    ROOT / 'docs' / 'overview' / 'user_guide.md',
    ROOT / 'README.md',
]
TEMPLATES = sorted((ROOT / 'prompts' / 'research').glob('*.md'))


@pytest.mark.parametrize('document', DOCUMENTS, ids=lambda p: str(p.relative_to(ROOT)))
def test_research_documents_name_real_commands(document: Path) -> None:
    """Name only commands the graph CLI has."""
    commands = set(re.findall(r'python -m veriphy\.graph (?:--root \S+ )?([a-z]+)', document.read_text()))
    assert commands <= set(COMMANDS)


@pytest.mark.parametrize('document', TEMPLATES, ids=lambda p: p.stem)
def test_research_templates_load(document: Path, tmp_path: Path) -> None:
    """Load each Turtle template as an agent file of a workspace."""
    blocks = re.findall(r'```turtle\n(.*?)\n```', document.read_text(), re.DOTALL)
    (tmp_path / 'lakefile.toml').write_text('')
    sources = tmp_path / '.veriphy' / 'graph' / 'sources'
    sources.mkdir(parents=True)
    for index, block in enumerate(blocks):
        (sources / f'chapter9-{index}.agent.ttl').write_text(block + '\n')
    assert load_graph(tmp_path).assertions


def test_research_skill_has_both_copies() -> None:
    """Point the plugin copy and the repository copy of the skill at the playbook."""
    for skill in (ROOT / 'skills' / 'research' / 'SKILL.md', ROOT / '.claude' / 'skills' / 'research' / 'SKILL.md'):
        text = skill.read_text()
        assert text.startswith('---\nname: research\n')
        assert 'prompts/research.md' in text
