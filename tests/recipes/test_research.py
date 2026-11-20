"""Test the research playbook: its commands exist, its Turtle templates load, and both skill copies point at it."""

import re
from pathlib import Path

import pytest

from veriphy.graph import COMMANDS, load_graph
from veriphy.prompts import content_dir
from veriphy.steps import STEPS

ROOT = Path(__file__).resolve().parents[2]
PROMPTS = content_dir()
DOCUMENTS = [
    PROMPTS / 'research.md',
    *sorted((PROMPTS / 'research').glob('*.md')),
    ROOT / 'skills' / 'research' / 'SKILL.md',
    ROOT / '.claude' / 'skills' / 'research' / 'SKILL.md',
    ROOT / 'docs' / 'overview' / 'user_guide.md',
    ROOT / 'README.md',
]
TEMPLATES = sorted((PROMPTS / 'research').glob('*.md'))


@pytest.mark.parametrize('document', DOCUMENTS, ids=lambda p: str(p.relative_to(ROOT)))
def test_research_documents_name_real_commands(document: Path) -> None:
    """Name only commands the graph CLI has."""
    commands = set(re.findall(r'python -m veriphy\.graph (?:--root \S+ )?([a-z]+)', document.read_text()))
    assert commands <= set(COMMANDS)


@pytest.mark.parametrize('document', [*DOCUMENTS, PROMPTS / 'prove.md'], ids=lambda p: str(p.relative_to(ROOT)))
def test_documents_name_real_steps(document: Path) -> None:
    """Name only steps `python -m veriphy` has."""
    steps = set(re.findall(r'python -m veriphy (?:--root \S+ )?([a-z]+)', document.read_text()))
    assert steps <= {*STEPS, 'records'}


@pytest.mark.parametrize('playbook', ['prove.md', 'research/triage.md'])
def test_playbooks_run_the_meaning_step(playbook: str) -> None:
    """Have the formalization step and the triage run the meaning check, and cite its record."""
    text = (PROMPTS / playbook).read_text()
    assert 'python -m veriphy meaning <file> <declaration> --informal' in text
    assert '.veriphy/runs/meaning/' in text or "record's path" in text or 'path of the record' in text


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


def test_research_templates_exist() -> None:
    """Find the research templates in the installed package, so the tests above never run on nothing."""
    assert [p.stem for p in TEMPLATES] == ['extraction', 'triage']


@pytest.mark.parametrize('skill', ['prove', 'certify', 'research'])
def test_skill_copies_are_identical_and_read_the_package(skill: str) -> None:
    """Keep the plugin copy and the repository copy of each skill identical, reading the installed playbooks."""
    plugin, repository = (base / 'skills' / skill / 'SKILL.md' for base in (ROOT, ROOT / '.claude'))
    text = plugin.read_text()
    assert text == repository.read_text()
    assert text.startswith(f'---\nname: {skill}\n')
    assert 'sage -python -m veriphy.prompts path' in text
    assert f'<prompts>/{skill}.md' in text
    assert 'VERIPHY_HOME' not in text
