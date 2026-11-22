## MODIFIED Requirements

### Requirement: Module and console entry points
The Sage session SHALL start with `python -m veriphy.packs.math.primitives.sage` under Sage's interpreter, and serve the
JSON-RPC 2.0 protocol, one message per line, on stdin and stdout. The package SHALL install no other entry point for
it.

#### Scenario: Module entry point
- **WHEN** `echo '{"jsonrpc":"2.0","id":1,"method":"ping"}' | sage -python -m veriphy.packs.math.primitives.sage` is run
- **THEN** it prints one line `{"jsonrpc": "2.0", "id": 1, "result": {"ok": true, "sage": "<version>", "veriphy": "<version>"}}`
