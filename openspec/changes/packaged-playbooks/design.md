# Design

## Context

`prompts/` holds 81 files: the playbooks (`prove.md`, `certify.md`, `research.md`, `research/`), one recipe per
technique in `recipes/`, their Sage templates in `recipes/templates/`, and library recipes in `recipes/physlib/`. The
skills resolve the repository through `$VERIPHY_HOME` or `${CLAUDE_PLUGIN_ROOT}`. The Lean tests run every template
through `sage_run file "prompts/recipes/templates/<name>.sage"`, a path `resolveScriptPath` resolves against the
workspace root. The recipe assets live in `lean/assets/VeriphyAssets/` and are built by the Lake library
`VeriphyAssets`. The wheel is built by hatch from `src/veriphy`, and pytest runs with `--doctest-modules` over `src`.

## Goals / Non-Goals

**Goals:**

- One install of the Python package gives an agent everything it reads or copies.
- The playbooks always match the installed toolkit.
- Each file has one source in the repository.

**Non-Goals:**

- Shipping the Lean library through PyPI. Lake reads it from git.
- Warning when the Lean `rev` and the Python package differ.
- Changing the content of any playbook or recipe beyond paths.

## Decisions

### D1. `veriphy.prompts` is a package holding data and a small command

`src/veriphy/prompts/` keeps the current tree and gains `__init__.py`, `__main__.py` and `_cli.py`. The directory
name stays `prompts`, so the playbooks keep their relative references (`recipes/<name>.md`, `research/triage.md`).
Content is located from the module's own file, which works for wheel and editable installs alike, since pip installs
packages as directories. Hatch includes
non-Python files under `src/veriphy` in the wheel by default, and a task checks the built wheel lists them.

### D2. Four subcommands

`path` prints the directory, for agents that read files themselves. `list` prints the playbooks, recipes, templates
and assets, one per line. `show <name>` prints one file, where the name is relative and the extension optional
(`prove`, `recipes/sos`, `recipes/templates/sos`). `copy <name>` copies a template into `.veriphy/certificates/` or an
asset into `.veriphy/lean/VeriphyAssets/` of the current workspace, refuses to overwrite an existing file, and prints
the destination. The command returns exit code 1 for an unknown name, naming the closest matches.

### D3. Assets stay in `lean/` and are force-included in the wheel

`lean/assets/VeriphyAssets/` stays the source, so Lake keeps building it. Hatch's `force-include` maps it to
`veriphy/prompts/assets/VeriphyAssets/` in the wheel. An editable install has no such copy, so the command falls back
to the repository's `lean/assets/` when the package directory lacks `assets/`. This is the only place the command
looks outside the package.

### D4. The skills ask the package

Each `SKILL.md` runs `sage -python -m veriphy.prompts path` once per session and reads the playbook from there. If the
command fails, the skill asks the user to run `sage -pip install veriphy` and stops. The two copies of each skill
(`skills/` for the plugin, `.claude/skills/` for this repository) become identical, and a test enforces it.

### D5. Lean tests name the new path

`sage_run file` already resolves any relative path against the workspace root, so the tests change only the path text
(`src/veriphy/prompts/recipes/templates/<name>.sage`). The coverage runner's workspace is `lean/coverage/`, so its
paths become `../../src/veriphy/prompts/recipes/physlib/templates/<name>.sage`.

### D6. Markdown and Sage files are not modules

pytest's `--doctest-modules` collects only Python modules, so the moved `.md` and `.sage` files add nothing to the
test run. The API reference generator documents `veriphy.prompts` like any other package: only its command module.

## Risks / Trade-offs

- [A path to `prompts/` is missed] → A task checks with `git grep` that no tracked file outside the archive and the
  changelog names `prompts/` without `src/veriphy/`.
- [Manual installs break silently on upgrade] → The README states the new manual install, and the release notes say
  `VERIPHY_HOME` is gone.
- [The plugin and the installed package can be different versions] → The skills read the installed package, so the
  playbook always matches the toolkit that runs. A newer plugin with an older package reads the older playbooks, which
  is the consistent pair.
- [The wheel grows by the playbooks and assets] → About 300 KB.
