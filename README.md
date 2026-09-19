# sky-openai

An OpenAI provider package for [Sky](https://github.com/anzellai/sky)'s `Std.Ai`.
It gives you two `Std.Ai.Provider.Provider` backends:

- **`SkyOpenAI.Chat`** — the OpenAI Chat Completions endpoint.
- **`SkyOpenAI.Responses`** — the OpenAI Responses API (`POST /v1/responses`).

Both return an ordinary `Provider`, so they compose with `Std.Ai.Agent`,
`Std.Ai.Policy`, `Std.Ai.Trace`, and `cost` exactly like a built-in provider.

The package is built entirely on `Std.Ai.Provider.custom`, the stdlib extension
point. Provider-specific logic lives here, not in the Sky stdlib, which stays
vendor-neutral. This repo is the reference use case for `Provider.custom`: it
shows how to add a new backend, wire format, or API to Sky without any compiler
or stdlib change.

## Requirements

You need a Sky toolchain that includes `Std.Ai.Provider.custom`. That is Sky
**after** v0.25.6. On an older Sky the package will not resolve `Provider.custom`.
Check with:

```bash
sky doc Std.Ai.Provider | grep custom
```

## Install

```bash
sky add --sky github.com/anzellai/sky-openai
```

This records the package under `[dependencies]` in your `sky.toml` and fetches it
into `.skydeps/`.

## Use

The Responses API:

```elm
import SkyOpenAI.Responses as Responses
import Sky.Core.Secret as Secret
import Std.Ai.Provider as Provider

provider : Provider.Provider
provider =
    Responses.provider (Secret.fromEnv "OPENAI_API_KEY") "gpt-4o-mini"

-- Provider.chat provider [ Provider.user "Say hello." ]
--     |> Task.map .content
```

Chat Completions (also built into the stdlib as `Provider.openai`; exposed here
so the whole OpenAI surface is in one package):

```elm
import SkyOpenAI.Chat as Chat

chatProvider =
    Chat.provider (Secret.fromEnv "OPENAI_API_KEY") "gpt-4o-mini"
```

A specific endpoint (an Azure deployment or a proxy):

```elm
Responses.providerAt "https://my-resource.openai.azure.com/openai/responses"
    (Secret.fromEnv "OPENAI_API_KEY") "gpt-4o-mini"
```

Because a provider is a value, it drops straight into an agent:

```elm
import Std.Ai.Agent as Agent

Agent.oneShot db (Responses.provider key "gpt-4o-mini")
    "You are terse." [ Provider.user "..." ]
```

## What is covered

- `SkyOpenAI.Chat.provider` / `compatible` — Chat Completions.
- `SkyOpenAI.Responses.provider` / `providerAt` — a single Responses call: the
  messages go out as the Responses `input`, the `output_text` parts and the token
  `usage` come back as a `Provider.ChatResponse`.
- `SkyOpenAI.Responses.decodeResponse` — decode a raw Responses body yourself.

## Roadmap

Each item stays inside this package, no stdlib change:

- Stateful chaining with `previous_response_id`.
- The server-side built-in tools (web_search, file_search, code_interpreter).
- Native function-calling, via `Std.Ai.Provider.customTools`.

## Test

```bash
sky test tests/ResponsesTest.sky
```

The tests decode a canonical Responses body offline. No network, no key.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
