"""The registered profile's classify_api_error, called the way Hermes calls it.

Hermes passes ``message`` lower-cased (str(error) plus the body's message) and
``body`` as the parsed JSON. Bodies below follow the gateway's real shape.
"""

import pytest


def gateway_error(code, text, error_type="invalid_request_error"):
    message = f"[{code}] {text}"
    body = {"error": {"message": message, "type": error_type, "param": None, "code": error_type}}
    return message.lower(), body


def classify(profile, status, code, text, error_type="invalid_request_error", model="gpt-4o"):
    message, body = gateway_error(code, text, error_type)
    return profile.classify_api_error(
        Exception(message), status_code=status, error_code=error_type, message=message, body=body, model=model
    )


MODEL_NOT_FOUND = {"reason": "model_not_found", "retryable": False, "should_fallback": True}
NOT_ENTITLED = {"reason": "model_entitlement", "retryable": False, "should_fallback": True}
OUT_OF_CREDIT = {"reason": "billing", "retryable": False, "should_fallback": True}


@pytest.mark.parametrize(
    "status, code, text",
    [
        (400, "ERR_NGROK_27224", 'Unknown model "gpt-9". Did you mean "gpt-4o"?'),
        (400, "ERR_NGROK_27225", 'Unknown provider "opneai".'),
        (400, "ERR_NGROK_27229", 'Invalid model address "a:b:c".'),
        (400, "ERR_NGROK_27230", '"foo:bar" is not a known model, and "foo" is not a recognized provider.'),
    ],
)
def test_unrouted_model_is_model_not_found(profile, status, code, text):
    assert classify(profile, status, code, text) == MODEL_NOT_FOUND


@pytest.mark.parametrize(
    "status, code, text",
    [
        (403, "ERR_NGROK_27231", 'Provider "openai" is not allowed by the access policy.'),
        (403, "ERR_NGROK_27232", 'Model "gpt-4o" is not allowed by the access policy.'),
        (502, "ERR_NGROK_27202", 'No keys available for provider "anthropic".'),
        (401, "ERR_NGROK_27211", "Upstream provider rejected the API key."),
        (400, "ERR_NGROK_27233", 'Model "x" is not available with an ngrok-managed key for provider "y".'),
    ],
)
def test_upstream_credential_and_policy_failures_are_not_auth(profile, status, code, text):
    verdict = classify(profile, status, code, text)
    assert verdict == NOT_ENTITLED
    assert verdict["reason"] not in ("auth", "auth_permanent")


@pytest.mark.parametrize(
    "status, code, text",
    [
        (403, "ERR_NGROK_4026", "Your account has run out of credit."),
        (402, "ERR_NGROK_27206", "Credit check failed: insufficient balance"),
    ],
)
def test_out_of_credit_is_billing(profile, status, code, text):
    assert classify(profile, status, code, text) == OUT_OF_CREDIT


@pytest.mark.parametrize(
    "status, code, text, error_type",
    [
        # Bad/missing ngrok access key: Hermes' own auth guidance applies.
        (401, "ERR_NGROK_27201", "Authentication failed: invalid or missing API key", "authentication_error"),
        # Rate limits and 5xx: Hermes' retry/backoff applies.
        (429, "ERR_NGROK_27217", "Upstream provider rate limit exceeded.", "rate_limit_error"),
        (502, "ERR_NGROK_27208", "All retries exhausted, last error: boom", "api_error"),
        (502, "ERR_NGROK_27227", "No backend available: none", "api_error"),
        (503, "ERR_NGROK_27239", 'ngrok can\'t serve "x" on provider "y" right now.', "api_error"),
        (504, "ERR_NGROK_27207", "Upstream request timed out.", "api_error"),
        (504, "ERR_NGROK_3810", "Request timed out after 120s.", "api_error"),
        # Oversized input: Hermes compresses.
        (413, "ERR_NGROK_3811", "Input too large: 300000 tokens (max 200000).", "invalid_request_error"),
    ],
)
def test_defers_to_hermes(profile, status, code, text, error_type):
    assert classify(profile, status, code, text, error_type) is None


def test_defers_on_non_gateway_errors(profile):
    assert profile.classify_api_error(
        Exception("connection reset"), status_code=None, error_code="", message="connection reset", body={}, model="m"
    ) is None
    assert profile.classify_api_error(
        Exception("x"), status_code=500, error_code="", message="internal server error", body={}, model="m"
    ) is None


def test_requires_matching_status(profile):
    # A documented code on an unexpected status isn't a documented response: defer.
    assert classify(profile, 500, "ERR_NGROK_27224", 'Unknown model "x".') is None


def test_code_match_is_exact(profile):
    # ERR_NGROK_4026 must not match a longer code that shares its prefix.
    assert classify(profile, 403, "ERR_NGROK_40261", "something else") is None


def test_matches_code_in_body_when_message_lacks_it(profile):
    _, body = gateway_error("ERR_NGROK_27224", 'Unknown model "gpt-9".')
    verdict = profile.classify_api_error(
        Exception("bad request"), status_code=400, error_code="invalid_request_error",
        message="error code: 400", body=body, model="gpt-9",
    )
    assert verdict == MODEL_NOT_FOUND


def test_tolerates_missing_message_and_body(profile):
    assert profile.classify_api_error(
        None, status_code=400, error_code=None, message=None, body=None, model=None
    ) is None


def test_verdicts_are_independent_copies(profile):
    first = classify(profile, 400, "ERR_NGROK_27224", 'Unknown model "x".')
    first["retryable"] = True
    assert classify(profile, 400, "ERR_NGROK_27224", 'Unknown model "x".') == MODEL_NOT_FOUND
