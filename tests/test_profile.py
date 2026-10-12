"""What Hermes sees when it loads the plugin: the one registered provider profile."""

import re

from conftest import load_plugin

# Hermes' built-in Vercel provider (plugins/model-providers/ai-gateway).
VERCEL_NAMES = {"ai-gateway", "vercel", "vercel-ai-gateway", "ai_gateway", "aigateway"}


def test_registers_exactly_one_profile(monkeypatch):
    registered = load_plugin(monkeypatch)
    assert len(registered) == 1
    assert registered[0].name == "ngrok"


def test_identity(profile):
    assert profile.aliases == ("ngrok-ai", "ngrok-ai-gateway")
    assert profile.display_name == "ngrok AI Gateway"
    assert "failover" in profile.description
    assert profile.signup_url == "https://ngrok.ai"


def test_aliases_do_not_collide_with_vercel_ai_gateway(profile):
    assert not ({profile.name, *profile.aliases} & VERCEL_NAMES)


def test_auth_and_env_var_order(profile):
    assert profile.auth_type == "api_key"
    # Key first; Hermes treats the *_BASE_URL entry as the base-URL override.
    assert profile.env_vars == ("NGROK_AI_GATEWAY_KEY", "NGROK_AI_GATEWAY_BASE_URL")
    assert profile.env_vars[-1].endswith("_BASE_URL")


def test_hosted_endpoint_over_chat_completions(profile):
    assert profile.base_url == "https://gateway.ngrok.ai/v1"
    assert profile.api_mode == "chat_completions"


def test_live_catalog_only(profile):
    assert profile.fallback_models == ()


def test_no_default_aux_model(profile):
    # No cheap model is routable for every access key; aux tasks use the main
    # model unless the user configures auxiliary.<task>.model.
    assert profile.default_aux_model == ""


def test_user_agent_carries_hermes_version(profile):
    assert profile.default_headers["User-Agent"] == "hermes-agent/0.21.7 (ngrok-plugin)"


def test_user_agent_format(profile):
    assert re.fullmatch(r"hermes-agent(/\S+)? \(ngrok-plugin\)", profile.default_headers["User-Agent"])


def test_user_agent_without_hermes_version(monkeypatch):
    (profile,) = load_plugin(monkeypatch, hermes_version=None)
    assert profile.default_headers["User-Agent"] == "hermes-agent (ngrok-plugin)"


def test_user_agent_with_unstamped_hermes(monkeypatch):
    (profile,) = load_plugin(monkeypatch, hermes_version="unknown")
    assert profile.default_headers["User-Agent"] == "hermes-agent (ngrok-plugin)"


def test_error_classifier_is_a_constructor_field(profile):
    # classify_api_error is a ProviderProfile dataclass field; a method of the
    # same name would be overwritten by the dataclass __init__.
    assert callable(profile.classify_api_error)
