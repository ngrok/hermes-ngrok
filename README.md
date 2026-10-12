# hermes-ngrok

A Hermes model-provider plugin for the [ngrok AI Gateway](https://ngrok.ai). See the [AI Gateway docs](https://ngrok.com/docs/ai-gateway/overview) to set up providers, keys and models.

## Install

```bash
hermes plugins install ngrok-ai-gateway
```

Enter your access key (`ng-…`, from [app.ngrok.ai/keys](https://app.ngrok.ai/keys)) when prompted. Hermes saves it as `NGROK_AI_GATEWAY_KEY`.

## Use

Select **ngrok AI Gateway** in `hermes model`, or use `--provider ngrok`. The model list comes from your gateway. Model IDs follow the gateway's [naming](https://ngrok.com/docs/ai-gateway/concepts/models), for example `openai:gpt-4o`.

To use your own gateway endpoint, set `NGROK_AI_GATEWAY_BASE_URL` (default `https://gateway.ngrok.ai/v1`).

## Development

```bash
uv run pytest
```

To install from a local checkout (committed `HEAD` only):

```bash
hermes plugins install "file://$PWD#model-providers/ngrok"
```

See [RELEASING.md](RELEASING.md) for the release process.

## License

MIT
