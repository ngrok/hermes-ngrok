# hermes-ngrok

Use the [ngrok AI Gateway](https://ngrok.ai) as a model provider in [Hermes Agent](https://github.com/NousResearch/hermes-agent).

One access key gets you every model provider configured on your gateway, with failover and key rotation handled by ngrok. After install, **ngrok AI Gateway** shows up wherever Hermes lists providers: the `hermes model` picker, `hermes setup`, `--provider ngrok`, in-session `/model`, and `hermes doctor`.

The plugin registers one Hermes provider profile and nothing else. It adds no tools, hooks or middleware, makes no changes to Hermes core, and makes no network calls of its own.

## Install

```bash
hermes plugins install ngrok-ai-gateway
```

The installer asks for your ngrok AI Gateway access key (`ng-…`). Create one under **Keys** at [app.ngrok.ai](https://app.ngrok.ai). Hermes saves it as `NGROK_AI_GATEWAY_KEY` in `~/.hermes/.env`, where it keeps every other provider key.

To install an unreleased version from a checkout of this repository:

```bash
hermes plugins install ./model-providers/ngrok
```

### Multiple Hermes profiles

Plugins install **per Hermes profile**. A plugin installed in one profile (one `HERMES_HOME`) isn't visible to the others. If a second profile can't see ngrok, run the install command again while that profile is active.

## Use it

Choose **ngrok AI Gateway** in the picker:

```bash
hermes model
```

You can also pick it for a single run with `--provider ngrok`, or make it the default in `config.yaml`:

```yaml
model:
  provider: ngrok
  default: openai:gpt-4o
```

`ngrok-ai` and `ngrok-ai-gateway` work as aliases for `ngrok`.

The model list comes live from your gateway (`GET /v1/models`), so the picker shows the models your access key can route. Switch models mid-session with `/model`. Model IDs follow the gateway's naming: a bare catalog ID (`gpt-4o`) or a provider-qualified one (`anthropic:claude-sonnet-4-6`). See [Models](https://ngrok.com/docs/ai-gateway/concepts/models).

If the gateway can't be reached when Hermes starts, the picker is empty until it can. Hermes keeps running. The plugin ships no hardcoded fallback list because which models you can reach depends on your gateway configuration.

Hermes refuses models with a context window under 64K tokens, so a small-context model routed by your gateway won't run as the main model.

### Check your setup

```bash
hermes doctor
```

The **API Connectivity** section shows whether `NGROK_AI_GATEWAY_KEY` is set and whether the gateway accepts it.

## Self-hosted gateway endpoint

To use your own gateway endpoint instead of the hosted `https://gateway.ngrok.ai/v1`, set:

```bash
NGROK_AI_GATEWAY_BASE_URL=https://your-gateway.example.com/v1
```

Put it in `~/.hermes/.env` or your environment. Chat requests and the live model list both go to that endpoint.

## Auxiliary models

Hermes runs background tasks such as context compression, session titles and vision summaries on an *auxiliary* model. This plugin doesn't set a default auxiliary model: access keys can be scoped to particular providers and models, so no one cheap model is reachable for every user. Out of the box, auxiliary tasks run on your main model.

To run them on a cheaper model, set it per task in `config.yaml`:

```yaml
auxiliary:
  compression:
    provider: ngrok
    model: openai:gpt-4o-mini
  title_generation:
    provider: ngrok
    model: openai:gpt-4o-mini
  vision:
    provider: ngrok
    model: openai:gpt-4o-mini
```

Pick a model your access key can route. See Hermes' [Configuring models](https://hermes-agent.nousresearch.com/docs/user-guide/configuring-models) for every auxiliary task.

## Errors and recovery

Gateway errors are mapped onto Hermes' recovery behavior. The plugin reads the documented [gateway error codes](https://ngrok.com/docs/ai-gateway/reference/error-codes):

| Gateway error | Hermes treats it as |
| - | - |
| Unknown model, provider or model address (`ERR_NGROK_27224`, `27225`, `27229`, `27230`) | Model not found: falls back to your fallback model |
| Model or provider blocked by the key's access policy (`27231`, `27232`) | Model not available to this key: falls back. **Not** reported as a bad key |
| Upstream provider key missing or rejected, or model unavailable on a managed key (`27202`, `27211`, `27233`) | Model not available to this key: falls back. **Not** reported as a bad key |
| Out of credit (`4026`, `27206`) | Billing |
| Invalid or missing ngrok access key (`27201`) | Hermes' normal authentication guidance |
| Rate limits, timeouts, 5xx | Hermes' normal retry and backoff |

Every request carries a `User-Agent: hermes-agent/<version> (ngrok-plugin)` header, so you can tell Hermes traffic apart in your gateway's usage data.

## Update and remove

```bash
hermes plugins update ngrok-ai-gateway
```

```bash
hermes plugins remove ngrok-ai-gateway
```

Removing the plugin doesn't delete `NGROK_AI_GATEWAY_KEY` from `~/.hermes/.env`. Delete that line yourself if you no longer want the key stored.

## Development

The tests are hermetic. They need no Hermes install and no network access:

```bash
uv run pytest
```

Layout:

- `model-providers/ngrok/`: the plugin (`__init__.py`, `plugin.yaml`, and the README shown on the catalog page)
- `tests/`: loads the plugin against a stubbed Hermes and asserts on the profile it registers
- `upstream/plugin-catalog/ngrok-ai-gateway.yaml`: the exact entry submitted to `NousResearch/hermes-agent`
- `RELEASING.md`: release checklist

To support a new gateway error, add one row to `GATEWAY_ERROR_RULES` in `model-providers/ngrok/__init__.py` and a test case in `tests/test_error_classification.py`.

## License

MIT. See [LICENSE](LICENSE).
