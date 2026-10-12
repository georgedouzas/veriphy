"""Test that every recipe embeds its tested template, and that every template is exercised in Lean."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RECIPES = ROOT / 'prompts' / 'recipes'
TEMPLATES = sorted((RECIPES / 'templates').glob('*.sage'))
LEAN_TESTS = '\n'.join(p.read_text() for p in (ROOT / 'VeriphyTest').glob('*.lean'))
HEADER_KEYS = ('name', 'technique', 'goal', 'description')


@pytest.mark.parametrize('template', TEMPLATES, ids=lambda p: p.stem)
def test_recipe_embeds_template(template: Path) -> None:
    """Embed the template file verbatim in the recipe's Template section."""
    recipe = (RECIPES / f'{template.stem}.md').read_text()
    blocks = re.findall(r'```sage\n(.*?)\n```', recipe, re.S)
    assert blocks == [template.read_text().rstrip()]


@pytest.mark.parametrize('template', TEMPLATES, ids=lambda p: p.stem)
def test_template_runs_in_lean_tests(template: Path) -> None:
    """Run every template on a worked example in the Lean test suite."""
    assert f'prompts/recipes/templates/{template.name}' in LEAN_TESTS


@pytest.mark.parametrize('template', TEMPLATES, ids=lambda p: p.stem)
def test_template_header_is_complete(template: Path) -> None:
    """Start every template with the full catalog header."""
    head = template.read_text().splitlines()[: len(HEADER_KEYS)]
    assert [line.split(':')[0].lstrip('# ') for line in head] == list(HEADER_KEYS)


def test_every_recipe_has_a_template() -> None:
    """Pair each recipe with a template of the same name."""
    assert {p.stem for p in RECIPES.glob('*.md')} == {p.stem for p in TEMPLATES}
