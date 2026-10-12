"""The plugin manifest Hermes reads at install time."""

import re

import yaml

from conftest import PLUGIN_DIR


def test_manifest():
    manifest = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text())
    assert manifest["name"] == "ngrok-ai-gateway"
    assert manifest["kind"] == "model-provider"
    assert manifest["author"] == "ngrok"
    assert re.fullmatch(r"\d+\.\d+\.\d+", str(manifest["version"]))
    assert re.fullmatch(r">=\d+\.\d+(\.\d+)?", manifest["requires_hermes"])
    (env,) = manifest["requires_env"]
    assert env["name"] == "NGROK_AI_GATEWAY_KEY"
    assert env["secret"] is True
    assert env["url"] == "https://app.ngrok.ai/keys"
