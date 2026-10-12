"""The plugin manifest and the in-repo catalog entry agree, and the entry fits the catalog schema.

Schema per NousResearch/hermes-agent plugin-catalog/README.md.
"""

import re

import pytest
import yaml

from conftest import PLUGIN_DIR, REPO_ROOT

CATALOG_ENTRY = REPO_ROOT / "upstream" / "plugin-catalog" / "ngrok-ai-gateway.yaml"


@pytest.fixture
def manifest():
    return yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text())


@pytest.fixture
def raw_entry():
    return CATALOG_ENTRY.read_text()


@pytest.fixture
def entry(raw_entry):
    return yaml.safe_load(raw_entry)


def test_manifest(manifest):
    assert manifest["name"] == "ngrok-ai-gateway"
    assert manifest["kind"] == "model-provider"
    assert manifest["author"] == "ngrok"
    assert re.fullmatch(r"\d+\.\d+\.\d+", str(manifest["version"]))
    (env,) = manifest["requires_env"]
    assert env["name"] == "NGROK_AI_GATEWAY_KEY"
    assert env["secret"] is True
    assert env["description"]
    assert env["url"].startswith("https://ngrok.ai")


def test_entry_matches_manifest(manifest, entry):
    assert entry["name"] == manifest["name"]
    assert entry["version"] == str(manifest["version"])
    assert entry["requires_hermes"] == manifest["requires_hermes"]
    assert entry["capabilities"]["requires_env"] == [e["name"] for e in manifest["requires_env"]]


def test_entry_points_at_plugin_dir(entry):
    assert entry["repo"] == "https://github.com/ngrok/hermes-ngrok"
    assert entry["subdir"] == "model-providers/ngrok"
    assert (REPO_ROOT / entry["subdir"] / "__init__.py").is_file()


def test_entry_schema(entry, raw_entry):
    assert re.fullmatch(r"[a-z0-9_-]{1,64}", entry["name"])
    assert entry["repo"].startswith("https://")
    assert re.fullmatch(r"[0-9a-f]{40}", entry["sha"])
    assert re.fullmatch(r"[A-Za-z0-9._/-]+", entry["subdir"])
    assert not any(seg in ("", ".", "..") for seg in entry["subdir"].split("/"))
    assert re.search(r'^version: "[^"]+"$', raw_entry, re.MULTILINE), "version must be quoted"
    assert entry["tier"] == "community"
    assert entry["category"] == "models"
    assert entry["maintainer"] == "ngrok"
    assert entry["description"]
    assert re.fullmatch(r">=\d+\.\d+(\.\d+)?", entry["requires_hermes"])


def test_entry_declares_no_tools_hooks_or_middleware(entry):
    caps = entry["capabilities"]
    assert caps["provides_tools"] == []
    assert caps["provides_hooks"] == []
    assert caps["provides_middleware"] == []
