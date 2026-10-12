# ngrok AI Gateway for Hermes

Use the [ngrok AI Gateway](https://ngrok.ai) as a Hermes model provider. One access key gets you every model provider configured on your gateway, with failover and key rotation handled by ngrok.

```bash
hermes plugins install ngrok-ai-gateway
```

The installer asks for your access key (`ng-…`, from [app.ngrok.ai/keys](https://app.ngrok.ai/keys)) and saves it as `NGROK_AI_GATEWAY_KEY`. Then choose **ngrok AI Gateway** in `hermes model`, pass `--provider ngrok`, or set `model.provider: ngrok`. Aliases: `ngrok-ai`, `ngrok-ai-gateway`.

- **Live model list** from your gateway's `/v1/models`. No hardcoded fallback list, so if the gateway is briefly unreachable the picker is empty rather than wrong.
- **Self-hosted endpoint:** set `NGROK_AI_GATEWAY_BASE_URL` to use your own gateway instead of `https://gateway.ngrok.ai/v1`.
- **Error mapping:** an unrouted model is treated as *model not found*. Access-policy and upstream-provider-key failures fall back without telling you your ngrok key is bad. Running out of credit is *billing*. Auth, rate-limit and 5xx errors follow Hermes' normal handling.
- **Auxiliary tasks** (compression, titles, vision) use your main model unless you set `auxiliary.<task>.provider: ngrok` and `model:` in `config.yaml`.
- **Attribution:** every request carries `User-Agent: hermes-agent/<version> (ngrok-plugin)`.
- **Per profile:** plugins install per Hermes profile. Install again in each profile that should see ngrok.

**Disclosure:** the plugin registers one provider profile. Hermes sends model requests and the model-list probe to `https://gateway.ngrok.ai/v1` (or `NGROK_AI_GATEWAY_BASE_URL`) with your access key. The plugin itself makes no other network calls, reads no files and starts no background processes.

Full documentation: [github.com/ngrok/hermes-ngrok](https://github.com/ngrok/hermes-ngrok#readme)
