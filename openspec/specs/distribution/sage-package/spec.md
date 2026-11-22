# distribution/sage-package Specification

## Purpose
Defines the `veriphy` Python distribution that carries the Sage session: what it contains, how it is installed into an existing Sage and started, and the guarantee that packaging leaves the Sage session's protocol unchanged.

## Requirements

### Requirement: Installable into an existing Sage
The Sage session SHALL be published as the Python distribution `veriphy`, installable into a SageMath installation with `sage -pip install veriphy`. The distribution SHALL NOT declare SageMath or any Sage component as a dependency.

#### Scenario: Install into Sage
- **WHEN** a user with SageMath 10.9 runs `sage -pip install veriphy`
- **THEN** the install succeeds without downloading any Sage component, and `sage -python -c "import veriphy.packs.math.primitives.sage"` succeeds

#### Scenario: Installed outside Sage
- **WHEN** the package is installed into a plain Python without Sage and its Sage session is started
- **THEN** it exits with a message saying that it must run under SageMath (`sage -python -m veriphy.packs.math.primitives.sage`), not with an import traceback

### Requirement: Module and console entry points
The Sage session SHALL start with `python -m veriphy.packs.math.primitives.sage` under Sage's interpreter, and serve the
JSON-RPC 2.0 protocol, one message per line, on stdin and stdout. The package SHALL install no other entry point for
it.

#### Scenario: Module entry point
- **WHEN** `echo '{"jsonrpc":"2.0","id":1,"method":"ping"}' | sage -python -m veriphy.packs.math.primitives.sage` is run
- **THEN** it prints one line `{"jsonrpc": "2.0", "id": 1, "result": {"ok": true, "sage": "<version>", "veriphy": "<version>"}}`

### Requirement: Protocol unchanged by packaging
The packaged Sage session SHALL expose exactly the methods, parameters and result shapes of the pre-packaging `sage_bridge/server.py`, so a Lean library of the same version works with it unchanged.

#### Scenario: Existing tactic suite against the package
- **WHEN** `lake build VeriphyTest` runs with the Sage session started from the installed package
- **THEN** every example elaborates exactly as it did with the in-repo script

### Requirement: Version visible at runtime
The installed package SHALL report its version, derived from the release tag, through `veriphy.__version__`. `ping` SHALL include it alongside the Sage version.

#### Scenario: Ping reports both versions
- **WHEN** a client sends `ping` to a Sage session installed from the `0.4.0` release
- **THEN** the result contains `"sage": "<sage version>"` and `"veriphy": "0.4.0"`

### Requirement: Sage-only code stays importable for tooling
Importing `veriphy` SHALL NOT import Sage. Only starting the Sage session or calling its methods MAY require Sage, so packaging, linting and metadata tools run in a plain Python.

#### Scenario: Metadata without Sage
- **WHEN** `python -c "import veriphy; print(veriphy.__version__)"` runs in a plain Python where the package is installed
- **THEN** it prints the version without error
