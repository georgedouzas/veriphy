# Design

## Context

`lakefile.toml` at the root declares the package `veriphy` with the libraries `Veriphy`, `VeriphyCheck`, `VeriphyTest`
(globs `VeriphyTest`, `VeriphyTest.+`) and `VeriphyAssets` (`srcDir = "assets"`). `coverage/` is a separate Lake
project that requires Veriphy with `path = ".."`. `veriphy.core._project` finds the workspace root as the nearest
directory holding a lakefile, and the tracked `.veriphy/certificates/` at the root holds the scripts the Lean tests run.
CI builds Lake targets from the root and keys its cache on `lean-toolchain` and `lake-manifest.json`.

## Goals / Non-Goals

**Goals:**

- One directory, `lean/`, holds every Lean source of the repository.
- Nothing a user writes or runs changes.
- File history follows the moves.

**Non-Goals:**

- Moving the Lake configuration, which would make users add `subDir = "lean"` to their `require`.
- Shrinking the plugin cache. A clone used as a plugin source still carries the root `.lake/`.
- Renaming modules or libraries.

## Decisions

### D1. A package-level `srcDir`, configuration at the root

`lakefile.toml` gains `srcDir = "lean"`. Lake joins each library's `srcDir` onto the package's (`LeanLib.srcDir` in
Lake's source), so `VeriphyAssets` keeps `srcDir = "assets"` and resolves to `lean/assets`. A Lake dependency resolves
the lakefile at the repository root, and elan reads `lean-toolchain` there, so both stay. The alternative, the whole
package under `lean/`, needs `subDir = "lean"` in every user's `require` and breaks `lake update` for anyone who bumps
`rev` without it.

### D2. `.veriphy/` stays at the root

It belongs to the Lean workspace, and the workspace root stays at the root because the lakefile does. The Lean tests
run `sage_run file` against `.veriphy/certificates/` and `sage_test` against `prompts/recipes/templates/`, both resolved
from the workspace root, so neither moves.

### D3. The coverage project moves with the sources

`coverage/` becomes `lean/coverage/` and requires Veriphy with `path = "../.."`. The package libraries list explicit
roots and globs, so the nested project's files never join Veriphy's build.

### D4. Moves through `git mv`

Every `.lean` file moves with `git mv`, so `git log --follow` keeps its history and the module names stay the same. The
only content that changes is a path literal: four test fixtures named relative to the repository root
(`VeriphyTest/fixtures/…` in `Kit.lean` and `SageRun.lean`) become `lean/VeriphyTest/fixtures/…`, and so do the Python
tests that read Lean files or fixtures.

### D5. Specs name modules

The one spec that names a file path, `Veriphy/Kit/Linear.lean`, names the module `Veriphy.Kit.Linear`. Other mentions
are file names that do not depend on the directory (`VeriphyTest.lean`) and stay.

## Risks / Trade-offs

- [A path mention is missed and a document points to a file that no longer exists] → A task checks with `git grep`
  that no tracked file names a moved path without the `lean/` prefix, outside the archive and the changelog.
- [Lake rebuilds everything once, because the source paths changed] → One full rebuild locally and in CI. The mathlib
  cache is unaffected.
- [Contributors' editors open files at old paths] → None after a pull, since the files move in one commit.
