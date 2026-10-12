# Releasing

Each release is a commit in this repository, followed by a PR to `NousResearch/hermes-agent` that adds or bumps `plugin-catalog/ngrok-ai-gateway.yaml`.

## Before the first release

These two questions are open with the ngrok.ai team:

- [ ] **Default auxiliary model.** Is there a cheap, fast model that *every* access key can route, whatever its scope and provider keys? If there is, set `default_aux_model=` on the profile in `model-providers/ngrok/__init__.py`, update `test_no_default_aux_model`, and update the auxiliary-model note in `model-providers/ngrok/README.md`. If there isn't, leave it unset.
- [ ] **`GET /v1/models` response shape.** The public docs list only `/v1/chat/completions`, `/v1/completions`, `/v1/embeddings` and `/v1/responses`. The plugin uses Hermes' default catalog fetch, which expects the OpenAI shape `{"data": [{"id": ...}]}`. Confirm the gateway serves that. If the shape differs, override `fetch_models` on a `ProviderProfile` subclass. Parse leniently, and defer to `super()` when the caller passes a custom `base_url`.

## Each release

1. Bump `version` in `model-providers/ngrok/plugin.yaml`.
2. Run the hermetic tests:

   ```bash
   uv run pytest
   ```

3. Commit and push to `main`. Note the full 40-character SHA.
4. Run Hermes' validator at that commit:

   ```bash
   hermes plugins validate ./model-providers/ngrok --install-deps
   ```

   Every name containing "ngrok" makes the security scan report `caution` findings under the `tunnel_service` pattern. They're expected for this plugin and don't fail validation. Call them out in the catalog PR.
5. Run the live smoke test in an isolated Hermes home with a real access key:

   ```bash
   export HERMES_HOME="$(mktemp -d)"
   hermes plugins install --force "file://$PWD#model-providers/ngrok"
   ```

   - [ ] `hermes doctor` shows "ngrok AI Gateway" passing
   - [ ] `hermes model` → ngrok AI Gateway lists your gateway's live models
   - [ ] One plain completion succeeds
   - [ ] One tool call succeeds
   - [ ] Hermes sends `reasoning_effort: medium` by default, and the gateway accepts it (or ignores it) on a reasoning model and a non-reasoning model
   - [ ] An unrouted model name (`/model nope:not-a-model`) produces Hermes' "model isn't available" message, not a generic error
   - [ ] The gateway's usage data shows `User-Agent: hermes-agent/<version> (ngrok-plugin)`

6. Open a PR to `NousResearch/hermes-agent` that adds or updates `plugin-catalog/ngrok-ai-gateway.yaml`. Set `sha:` to the release commit and `version:` to match `plugin.yaml` (both quoted). For later releases, the PR is a one-line SHA bump plus the `version` label. Include the disclosure: the plugin registers one provider profile, sends model and model-list requests to the gateway with the user's access key, and does nothing else.

## `requires_hermes`

`>=0.21.6` is the first Hermes release whose `ProviderProfile` has the `classify_api_error` field. On older versions the plugin would fail to import. The plugin was validated against `NousResearch/hermes-agent@7cc3fb8` (v0.21.7). Keep the floor the same in `plugin.yaml` and in the catalog entry.
