"""Test the research playbook: its commands exist, its Turtle templates load, and both skill copies point at it."""

import json
import re
import tempfile
from pathlib import Path

import pytest

from veriphy.__main__ import LAYERS, LEAN_VERBS
from veriphy.agents import content_dir
from veriphy.claims import COMMANDS, load_graph
from veriphy.core import BUILTIN_PACKS
from veriphy.steps import load_steps

ROOT = Path(__file__).resolve().parents[2]


def _all_steps() -> set[str]:
    """Return the steps the documents may name: every shipped pack's."""
    packs = ', '.join(p for p in BUILTIN_PACKS if p != 'core')
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / 'veriphy.yaml').write_text(f'version: 1\npacks: [{packs}]\n')
        return {*load_steps(), *load_steps(Path(tmp))}


STEPS = _all_steps()

PROMPTS = content_dir()
DOCUMENTS = [
    PROMPTS / 'research.md',
    *sorted((PROMPTS / 'research').glob('*.md')),
    PROMPTS / 'skills' / 'research' / 'SKILL.md',
    ROOT / 'docs' / 'overview' / 'user_guide.md',
    ROOT / 'README.md',
]
TEMPLATES = sorted((PROMPTS / 'research').glob('*.md'))


@pytest.mark.parametrize('document', DOCUMENTS, ids=lambda p: str(p.relative_to(ROOT)))
def test_research_documents_name_real_commands(document: Path) -> None:
    """Name only commands `veriphy layers claims` has."""
    commands = set(re.findall(r'veriphy layers claims (?:--root \S+ )?([a-z]+)', document.read_text()))
    assert commands <= set(COMMANDS)


@pytest.mark.parametrize('document', [*DOCUMENTS, PROMPTS / 'prove.md'], ids=lambda p: str(p.relative_to(ROOT)))
def test_documents_name_real_steps(document: Path) -> None:
    """Name only the groups, steps and Lean verbs `veriphy` has."""
    text = document.read_text()
    groups = set(re.findall(r'(?<![#\w.-])veriphy (?:--root \S+ )?([a-z]+)', text))
    assert groups <= {'layers', 'config', 'pack', 'help', *LEAN_VERBS}
    assert set(re.findall(r'(?<![#\w.-])veriphy layers ([a-z]+)', text)) <= set(LAYERS)
    assert set(re.findall(r'(?<![#\w.-])veriphy layers step ([a-z][a-z-]*)', text)) <= {*STEPS, 'list', 'records'}


@pytest.mark.parametrize('playbook', ['prove.md', 'research/triage.md'])
def test_playbooks_run_the_meaning_step(playbook: str) -> None:
    """Have the formalization step and the triage run the meaning check, and cite its record."""
    text = (PROMPTS / playbook).read_text()
    assert 'veriphy layers step sample <file> <declaration> --informal' in text
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


@pytest.mark.parametrize(
    ('pack', 'skill'),
    [('math', 'prove'), ('math', 'certify'), ('math', 'research'), ('statistics', 'reproduce')],
)
def test_each_skill_lives_in_its_pack_and_the_plugin_finds_it(pack: str, skill: str) -> None:
    """Keep each skill in its pack's agents layer, in a directory the plugin manifest names, reading the playbooks."""
    skills = ROOT / 'src' / 'veriphy' / 'packs' / pack / 'agents' / 'skills'
    manifest = json.loads((ROOT / '.claude-plugin' / 'plugin.json').read_text())
    assert f'./{skills.relative_to(ROOT)}' in manifest['skills']
    text = (skills / skill / 'SKILL.md').read_text()
    assert text.startswith(f'---\nname: {skill}\n')
    assert 'veriphy layers agents path' in text
    assert f'<prompts>/{skill}.md' in text
    assert 'VERIPHY_HOME' not in text
