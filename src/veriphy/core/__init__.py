"""Provide the shared leaves of veriphy: its named exceptions, the protocol's type vocabulary, the project layout."""

import importlib
import warnings

from veriphy.core._digests import canonical_json, content_digest
from veriphy.core._errors import (
    CertificateError,
    CheckerError,
    EncodingError,
    GraphError,
    GraphExtraMissingError,
    MethodError,
    PackError,
    ParamError,
    PinError,
    PrimitiveError,
    RecordError,
    ScriptError,
    StepError,
    TableError,
    ToolError,
    VeriphyError,
)
from veriphy.core._packs import BUILTIN_PACKS, PACK_FILE, pack_dir, pack_packages, read_pack
from veriphy.core._process import find_tool, run_process
from veriphy.core._project import PROJECT_DIR_NAME, find_workspace_root, project_dir
from veriphy.core._types import RELATIONS, Coercer, JsonObject, JsonValue, Method

__all__ = [
    'BUILTIN_PACKS',
    'PACK_FILE',
    'PROJECT_DIR_NAME',
    'RELATIONS',
    'CertificateError',
    'CheckerError',
    'Coercer',
    'EncodingError',
    'GraphError',
    'GraphExtraMissingError',
    'JsonObject',
    'JsonValue',
    'Method',
    'MethodError',
    'PackError',
    'ParamError',
    'PinError',
    'PrimitiveError',
    'RecordError',
    'ScriptError',
    'StepError',
    'TableError',
    'ToolError',
    'VeriphyError',
    'canonical_json',
    'content_digest',
    'find_tool',
    'find_workspace_root',
    'pack_dir',
    'pack_packages',
    'project_dir',
    'read_pack',
    'run_process',
]

# deprecated: the record store moved to `veriphy.steps`, the layer that writes records
_MOVED_TO_STEPS = frozenset(
    {'KINDS', 'LEVELLED_KINDS', 'Record', 'RecordStore', 'config_digest', 'input_digest', 'read_record'},
)


def __getattr__(name: str) -> object:
    """Return a name that moved to `veriphy.steps`, warning that it moved."""
    if name not in _MOVED_TO_STEPS:
        message = f"module 'veriphy.core' has no attribute '{name}'"
        raise AttributeError(message)
    warnings.warn(f'veriphy.core.{name} moved to veriphy.steps.{name}', DeprecationWarning, stacklevel=2)
    return getattr(importlib.import_module('veriphy.steps'), name)
