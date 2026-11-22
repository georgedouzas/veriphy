"""Test that every recipe embeds its tested template, and that every template is exercised in Lean."""

import ast
import re
from pathlib import Path

import pytest

from veriphy.agents import content_dir

ROOT = Path(__file__).resolve().parents[2]
RECIPES = content_dir() / 'recipes'
TEMPLATES = sorted((RECIPES / 'templates').glob('*.sage'))
LIBRARY_TEMPLATES = sorted(RECIPES.glob('*/templates/*.sage'))
LEAN_TESTS = '\n'.join(
    p.read_text() for p in (ROOT / 'src' / 'veriphy' / 'packs' / 'math' / 'lean' / 'VeriphyTest').glob('*.lean')
)
# library recipes run in the coverage runner, which imports the libraries
RUNNER_TESTS = '\n'.join(
    p.read_text() for p in (ROOT / 'src' / 'veriphy' / 'packs' / 'math' / 'lean' / 'coverage').glob('*.lean')
)
SCRIPT_KEYS = ['name', 'serves', 'technique', 'goal', 'description', 'inputs']


def declaration(template: Path) -> dict[str, object]:
    """Return a template's `SCRIPT` declaration, the script contract's header."""
    for node in ast.parse(template.read_text().split('\n\n\ndef run', 1)[0]).body:
        if isinstance(node, ast.Assign) and [getattr(t, 'id', None) for t in node.targets] == ['SCRIPT']:
            value = ast.literal_eval(node.value)
            assert isinstance(value, dict)
            return value
    return {}


@pytest.mark.parametrize('template', TEMPLATES, ids=lambda p: p.stem)
def test_recipe_embeds_template(template: Path) -> None:
    """Embed the template file verbatim in the recipe's Template section."""
    recipe = (RECIPES / f'{template.stem}.md').read_text()
    blocks = re.findall(r'```sage\n(.*?)\n```', recipe, re.S)
    assert blocks == [template.read_text().rstrip()]


@pytest.mark.parametrize('template', TEMPLATES, ids=lambda p: p.stem)
def test_template_runs_in_lean_tests(template: Path) -> None:
    """Run every template on a worked example in the Lean test suite, which names it from the Lean package."""
    assert f'"../agents/recipes/templates/{template.name}"' in LEAN_TESTS


@pytest.mark.parametrize('template', TEMPLATES, ids=lambda p: p.stem)
def test_template_follows_the_script_contract(template: Path) -> None:
    """Start every template with its full `SCRIPT` declaration, and end it with `run(goal, inputs)` returning found."""
    text = template.read_text()
    assert text.startswith('SCRIPT = {')
    assert list(declaration(template)) == SCRIPT_KEYS
    assert declaration(template)['name'] == template.stem
    assert '\ndef run(goal, inputs):\n' in text
    assert text.rstrip().splitlines()[-1].startswith('    return found(')


def test_every_recipe_has_a_template() -> None:
    """Pair each recipe with a template of the same name."""
    assert {p.stem for p in RECIPES.glob('*.md')} == {p.stem for p in TEMPLATES}


@pytest.mark.parametrize('template', LIBRARY_TEMPLATES, ids=lambda p: f'{p.parents[1].name}/{p.stem}')
def test_library_recipe_embeds_template_and_runs(template: Path) -> None:
    """Embed each library template in its recipe, declare it with `SCRIPT`, and run it in the coverage runner."""
    library = template.parents[1]
    recipe = (library / f'{template.stem}.md').read_text()
    assert re.findall(r'```sage\n(.*?)\n```', recipe, re.S) == [template.read_text().rstrip()]
    assert list(declaration(template)) == SCRIPT_KEYS
    assert f'src/veriphy/packs/math/agents/recipes/{library.name}/templates/{template.name}' in RUNNER_TESTS


def test_templates_exist() -> None:
    """Find the templates in the installed package, so the tests above never run on nothing."""
    assert len(TEMPLATES) > 30
    assert LIBRARY_TEMPLATES
