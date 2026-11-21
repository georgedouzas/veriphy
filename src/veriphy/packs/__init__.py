"""Veriphy's own packs: `core` declares the built-ins, `lean` brings Lean, and `math` brings SageMath and its recipes.

A pack is a directory with a `pack.yaml` and the layer subpackages it needs (`primitives`, `steps`, `claims`,
`workflows`, `agents`). A pack's code in its layer-k subpackage imports only Veriphy's layers up to k.
"""
