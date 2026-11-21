"""Layer 0, primitives: deterministic operations, which write no record and read no workspace config.

A primitive is one typed operation, with input and output schemas and a trust class: a Python function called
in-process, a method of a tool speaking JSON-RPC 2.0 over stdio (SageMath, in its own interpreter), or a command that
writes one JSON result (a foreign tool). Tools are pinned. A composite is a primitive built from others. Every pack
declares its primitives in its `pack.yaml`, and `veriphy primitive list`, `describe` and `run` use them by hand.
`veriphy.primitives.graph` reaches the claim graph's engines. This package imports only `veriphy.core`.
"""

from veriphy.primitives._contracts import Found, Session, check_pin, run_files, start_session
from veriphy.primitives._descriptors import TRUST_CLASSES, Pin, Primitive, Tool, VersionProbe, composite_trust
from veriphy.primitives._registry import (
    TOOLS_KEY,
    Registry,
    composite,
    default_registry,
    load_registry,
    workspace_registry,
)
from veriphy.primitives._schema import check
from veriphy.primitives._testing import assert_deterministic

__all__ = [
    'TOOLS_KEY',
    'TRUST_CLASSES',
    'Found',
    'Pin',
    'Primitive',
    'Registry',
    'Session',
    'Tool',
    'VersionProbe',
    'assert_deterministic',
    'check',
    'check_pin',
    'composite',
    'composite_trust',
    'default_registry',
    'load_registry',
    'run_files',
    'start_session',
    'workspace_registry',
]
