# Proposal

## Why

Veriphy has two installable products, the Lean library (Lake, from git) and the Python package (PyPI), and a third body
of content with no installed home: the playbooks, recipes and templates in `prompts/`. The skills reach it through
`VERIPHY_HOME` or the plugin's copy of the repository, so anyone without the plugin needs a clone, and nothing ties the
playbooks to the toolkit version they describe. A recipe's template calls toolkit functions, so a template and a
toolkit from different versions can disagree.

## What Changes

- `prompts/` moves into the Python package as `src/veriphy/prompts/`, so `sage -pip install veriphy` installs the
  playbooks, recipes and templates at the same version as the toolkit and the daemon.
- The recipe assets (`lean/assets/VeriphyAssets/`) ship in the wheel too, from their place in `lean/`, where Lake keeps
  building them.
- A new command, `sage -python -m veriphy.prompts`, gives agents the installed content: `path` prints the directory,
  `list` lists playbooks, recipes, templates and assets, `show <name>` prints one, and `copy <name>` copies a template
  into the project's `.veriphy/certificates/` or an asset into `.veriphy/lean/VeriphyAssets/`.
- The skills find the playbooks through that command. **BREAKING** for manual installs: `VERIPHY_HOME` is no longer
  read, and copying the three `SKILL.md` files is enough. Plugin users see no change.
- The Lean tests and the coverage runner name templates at their new path. This also fixes the coverage runner's
  template paths, which pointed at `lean/prompts/` since the Lean sources moved.

## Capabilities

### New Capabilities

- `distribution/packaged-playbooks`: the playbooks, recipes, templates and assets ship in the Python package, and the
  `veriphy.prompts` command gives agents access to them.

### Modified Capabilities

- `certificates/procedures`: recipes are read from the installed package.
- `certificates/translation-extensions`: library-specific recipes live under the package's `recipes/<library>/`.
- `certificates/representation-bridge`: the recipe index is named as the `prove` playbook, not by its repository path.

## Impact

- New: `src/veriphy/prompts/` (moved content, plus `__init__.py`, `__main__.py`, `_cli.py`), wheel packaging of the
  assets in `pyproject.toml`.
- Lean: template paths in `lean/VeriphyTest/*.lean` and `lean/coverage/PhyslibRecipes.lean`. No library code changes.
- Skills: both copies of `prove`, `certify` and `research`.
- Tests: `tests/recipes/*`, a new `tests/prompts/`.
- Documents: README (manual install), user guide, developer guide, constitution scope, recipes that mention paths.
- Release: a minor release, since manual skill installs change.
