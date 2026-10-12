"""Hermetic fixtures: load the plugin against a stubbed Hermes and capture what it registers.

The plugin imports ``providers`` / ``providers.base``, which only exist inside a
Hermes install. The ``registered`` fixture stubs both, imports the plugin, and
returns the captured profiles — the one seam every test goes through.
"""

import importlib.util
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "model-providers" / "ngrok"


class StubProviderProfile:
    """Field-capturing stand-in for ``providers.base.ProviderProfile`` (a dataclass).

    Mirrors the defaults the plugin could otherwise rely on implicitly, so a
    missing kwarg shows up as the real default rather than an AttributeError.
    """

    def __init__(self, **kwargs):
        self.api_mode = "chat_completions"
        self.default_aux_model = ""
        self.default_headers = {}
        self.fallback_models = ()
        self.classify_api_error = None
        for key, value in kwargs.items():
            setattr(self, key, value)


def _install_hermes_stubs(monkeypatch, *, hermes_version):
    registered = []

    providers_mod = types.ModuleType("providers")
    providers_mod.register_provider = registered.append
    base_mod = types.ModuleType("providers.base")
    base_mod.ProviderProfile = StubProviderProfile
    monkeypatch.setitem(sys.modules, "providers", providers_mod)
    monkeypatch.setitem(sys.modules, "providers.base", base_mod)

    if hermes_version is None:
        # Hermes' CLI package absent: the plugin must still import.
        monkeypatch.setitem(sys.modules, "hermes_cli", None)
        monkeypatch.setitem(sys.modules, "hermes_cli.version_info", None)
    else:
        version_info_mod = types.ModuleType("hermes_cli.version_info")
        version_info_mod.get_version_info = lambda: types.SimpleNamespace(base_version=hermes_version)
        hermes_cli_mod = types.ModuleType("hermes_cli")
        hermes_cli_mod.version_info = version_info_mod
        monkeypatch.setitem(sys.modules, "hermes_cli", hermes_cli_mod)
        monkeypatch.setitem(sys.modules, "hermes_cli.version_info", version_info_mod)
    return registered


def load_plugin(monkeypatch, *, hermes_version="0.21.7"):
    """Import the plugin fresh against stubbed Hermes; return the profiles it registered."""
    registered = _install_hermes_stubs(monkeypatch, hermes_version=hermes_version)
    spec = importlib.util.spec_from_file_location("hermes_ngrok_plugin", PLUGIN_DIR / "__init__.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return registered


@pytest.fixture
def profile(monkeypatch):
    registered = load_plugin(monkeypatch)
    assert len(registered) == 1
    return registered[0]
