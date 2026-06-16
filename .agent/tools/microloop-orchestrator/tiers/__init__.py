"""Tier registry: maps execution_mode -> dispatch function.

Importing a tier is lazy so a platform missing one tier's deps never breaks the others
(portability)."""
import importlib

_MODES = {
    "inline-reload": "inline_reload",
    "fresh-session": "fresh_session",
    "subagent": "subagent",
}


def get_dispatch(mode):
    if mode not in _MODES:
        raise ValueError(f"unknown execution_mode: {mode}")
    module = importlib.import_module(f"tiers.{_MODES[mode]}")
    return module.dispatch
