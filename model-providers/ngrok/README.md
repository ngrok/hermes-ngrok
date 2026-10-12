# ngrok AI Gateway for Hermes

Use the [ngrok AI Gateway](https://ngrok.ai) as a model provider in Hermes. The gateway gives you one access key for all the model providers you've set up in ngrok, with failover and key rotation. See the [AI Gateway docs](https://ngrok.com/docs/ai-gateway/overview) to set up providers, keys and models.

## Install

```bash
hermes plugins install ngrok-ai-gateway
```

Enter your access key from [app.ngrok.ai/keys](https://app.ngrok.ai/keys) when prompted. Hermes saves it as `NGROK_AI_GATEWAY_KEY`.

Plugins are installed per Hermes profile, so install it again in any other profile that needs it.

## Use

Select **ngrok AI Gateway** in `hermes model`, or pass `--provider ngrok`. The model list comes from your gateway.

To use a different gateway endpoint, set `NGROK_AI_GATEWAY_BASE_URL`. The default is `https://gateway.ngrok.ai/v1`.

Background tasks like compression and title generation use your main model. To use a cheaper model for them, set `auxiliary.<task>.provider: ngrok` and `auxiliary.<task>.model` in `config.yaml`.

## Disclosure

The plugin sends chat and model-list requests to the gateway endpoint with your access key. Each request has a `User-Agent: hermes-agent/<version> (ngrok-plugin)` header. The plugin makes no other network requests, doesn't read files, and doesn't run background processes.
