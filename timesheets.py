"""Port: picks the cloud or local timesheet reader.

Both concrete readers (``timesheets_api`` for the cloud, ``timesheets_ollama``
for local) implement the same ``read_all_timesheets(folder, out_csv) -> int``
function, so callers can swap between them without any other code changing.

The module is chosen at run time, not imported here, so you only need the
dependencies of the option you actually use (``anthropic`` for cloud,
``ollama``/``pymupdf`` for local).
"""

from __future__ import annotations

import importlib
import os
from types import ModuleType

READER_MODULES = {
    "cloud": "timesheets_api",
    "local": "timesheets_ollama",
}


def get_reader(name: str | None = None) -> ModuleType:
    """Return the reader module for ``name`` ('cloud' or 'local').

    ``name`` wins if given (e.g. from a ``--reader`` flag); otherwise falls
    back to the ``READER`` environment variable, then to 'cloud'.
    """
    name = name or os.environ.get("READER", "cloud")
    try:
        module_name = READER_MODULES[name]
    except KeyError:
        raise ValueError(
            f"Unknown reader {name!r}. Use 'cloud' or 'local' "
            "(--reader flag, or READER= in .env)."
        ) from None
    return importlib.import_module(module_name)
