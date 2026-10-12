"""ngrok AI Gateway model provider profile.

Hermes' own agent loop drives models routed by the ngrok AI Gateway over its
OpenAI-compatible chat-completions API. Auth is a static access key
(``ng-…``) resolved by Hermes' built-in ladder (NGROK_AI_GATEWAY_KEY env ->
~/.hermes/.env -> setup wizard); NGROK_AI_GATEWAY_BASE_URL overrides the
hosted endpoint. This plugin adds no auth code, transport, or hooks beyond
the one registered profile.
"""

from providers import register_provider
from providers.base import ProviderProfile

HOSTED_BASE_URL = "https://gateway.ngrok.ai/v1"


def _hermes_version() -> str:
    """Hermes' release version, or "" when it can't be determined."""
    try:
        from hermes_cli.version_info import get_version_info

        version = get_version_info().base_version
    except Exception:
        try:
            from hermes_cli import __version__ as version
        except Exception:
            version = ""
    version = str(version or "").strip()
    return "" if version in ("unknown", "0.0.0") else version


def _user_agent() -> str:
    version = _hermes_version()
    return f"hermes-agent/{version} (ngrok-plugin)" if version else "hermes-agent (ngrok-plugin)"


# ── Error classification ──────────────────────────────────────────────
#
# The gateway's error body is OpenAI-shaped with the ngrok code embedded in
# the message (verified live 2026-10-12):
#   {"error": {"message": "[ERR_NGROK_27201] Authentication failed: ...",
#              "type": "authentication_error", "code": "authentication_error"}}
# Codes and statuses come from https://ngrok.com/docs/ai-gateway/reference/error-codes.
#
# Each rule is (ngrok error code, HTTP status, verdict). To support a new
# gateway error, add one row. Codes deliberately NOT listed defer to Hermes'
# built-in classifier, which already handles them correctly:
#   ERR_NGROK_27201 (401, bad/missing ngrok access key) -> auth guidance
#   ERR_NGROK_27217 (429, upstream rate limit)          -> backoff + retry
#   ERR_NGROK_27208 / 27227 / 27207 / 3810 / 27239 (5xx) -> retry
#   ERR_NGROK_3811  (413, input too large)              -> compress

_MODEL_NOT_FOUND = {"reason": "model_not_found", "retryable": False, "should_fallback": True}

# The access key works but can't reach this model (access policy, or no usable
# upstream provider credential). Not an ngrok-key problem: never surface it as
# "sign in again". Hermes benches the (credential, model) pair and falls back.
_NOT_ENTITLED = {"reason": "model_entitlement", "retryable": False, "should_fallback": True}

# The ngrok account itself is out of credit — a real billing wall.
_OUT_OF_CREDIT = {"reason": "billing", "retryable": False, "should_fallback": True}

GATEWAY_ERROR_RULES = (
    # Model address doesn't resolve to anything the gateway routes.
    ("ERR_NGROK_27224", 400, _MODEL_NOT_FOUND),  # Unknown model "X".
    ("ERR_NGROK_27225", 400, _MODEL_NOT_FOUND),  # Unknown provider "X".
    ("ERR_NGROK_27229", 400, _MODEL_NOT_FOUND),  # Invalid model address "X".
    ("ERR_NGROK_27230", 400, _MODEL_NOT_FOUND),  # "X" is not a known model, and "Y" is not a recognized provider.
    # Access-key scope excludes the provider/model.
    ("ERR_NGROK_27231", 403, _NOT_ENTITLED),  # Provider "X" is not allowed by the access policy.
    ("ERR_NGROK_27232", 403, _NOT_ENTITLED),  # Model "X" is not allowed by the access policy.
    # Upstream provider credentials missing or rejected.
    ("ERR_NGROK_27202", 502, _NOT_ENTITLED),  # No keys available for provider "X".
    ("ERR_NGROK_27211", 401, _NOT_ENTITLED),  # Upstream provider rejected the API key.
    ("ERR_NGROK_27233", 400, _NOT_ENTITLED),  # Model not available with an ngrok-managed key.
    # ngrok credits.
    ("ERR_NGROK_4026", 403, _OUT_OF_CREDIT),  # Your account has run out of credit.
    ("ERR_NGROK_27206", 402, _OUT_OF_CREDIT),  # Credit check failed.
)


def _classify_gateway_error(error=None, *, status_code=None, error_code=None, message=None, body=None, model=None):
    """Map documented gateway errors onto Hermes FailoverReasons; None defers.

    Passed to the profile as the ``classify_api_error`` constructor kwarg — it
    is a ProviderProfile dataclass FIELD, not a method hook; a same-named
    method on a subclass is silently overwritten by the dataclass __init__.
    """
    haystack = f"{message or ''} {body or ''}".lower()
    if "err_ngrok_" not in haystack:
        return None
    for code, status, verdict in GATEWAY_ERROR_RULES:
        # "[ERR_NGROK_4026]" must not match "[ERR_NGROK_40261]".
        if status_code == status and f"{code.lower()}]" in haystack:
            return dict(verdict)
    return None


ngrok = ProviderProfile(
    name="ngrok",
    # Never "ai-gateway"/"vercel"/"ai_gateway"/"aigateway": Hermes' built-in Vercel provider owns those.
    aliases=("ngrok-ai", "ngrok-ai-gateway"),
    display_name="ngrok AI Gateway",
    description="One access key for all your model providers, with failover",
    signup_url="https://ngrok.ai",
    auth_type="api_key",
    # Key first; the *_BASE_URL entry is Hermes' user base-URL override.
    env_vars=("NGROK_AI_GATEWAY_KEY", "NGROK_AI_GATEWAY_BASE_URL"),
    base_url=HOSTED_BASE_URL,
    # The model list is per-account gateway configuration, so a hardcoded list
    # would advertise models a user can't reach. Live catalog only: a transient
    # catalog failure means an empty picker until recovery.
    fallback_models=(),
    # No default_aux_model: no cheap model is guaranteed routable for every
    # access key (scopes and provider keys are per-account). Auxiliary tasks use
    # the main model unless the user sets auxiliary.<task>.model.
    #
    # Hermes forwards default_headers to its chat clients and to the /models
    # catalog probe, so this UA identifies every request the plugin makes.
    default_headers={"User-Agent": _user_agent()},
    # Dataclass FIELD (not a method hook) — see _classify_gateway_error.
    classify_api_error=_classify_gateway_error,
)

register_provider(ngrok)
