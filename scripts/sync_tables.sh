#!/bin/sh
# Regenerate the Python toolkit's JSON copies of the core translation table and the shipped library packs from
# their Lean definitions. A Sage-free test in VeriphyTest/Kit.lean fails until the copies match.
set -e
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
cat > "$tmp/Gen.lean" <<'LEAN'
import Veriphy.Kit.Packs
#eval IO.println (Lean.toJson Veriphy.coreTable).compress
#eval do for p in Veriphy.shippedPacks do IO.println (Lean.toJson p.table).compress
LEAN
lake env lean "$tmp/Gen.lean" > "$tmp/tables.jsonl"
python3 - "$tmp/tables.jsonl" <<'PY'
import json, sys

def clean(x):
    if isinstance(x, dict):
        return {k: clean(v) for k, v in sorted(x.items()) if v is not None}
    if isinstance(x, list):
        return [clean(v) for v in x]
    return x

tables = [json.loads(line) for line in open(sys.argv[1]) if line.strip()]
core, packs = tables[0], tables[1:]
targets = [('src/veriphy/toolkit/core_table.json', core)]
targets += [(f"src/veriphy/toolkit/packs/{t['namespace']}.json", t) for t in packs]
for path, table in targets:
    with open(path, 'w') as out:
        out.write(json.dumps(clean(table), indent=2, ensure_ascii=False) + '\n')
    print('wrote', path)
PY
rm -rf "$tmp"
