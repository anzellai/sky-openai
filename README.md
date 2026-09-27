# sky-openai

An OpenAI provider package for [Sky](https://github.com/anzellai/sky)'s `Std.Ai`.
It gives you two `Std.Ai.Provider.Provider` backends:

- **`SkyOpenAI.Chat`** — the OpenAI Chat Completions endpoint.
- **`SkyOpenAI.Responses`** — the OpenAI Responses API (`POST /v1/responses`).

Both return an ordinary `Provider`, so they compose with `Std.Ai.Agent`,
`Std.Ai.Policy`, `Std.Ai.Trace`, and `cost` exactly like a built-in provider.

The Responses provider is built on `Std.Ai.Provider.customTools`; Chat is a thin
alias over the stdlib provider. Provider-specific wire logic lives here, while the
stdlib stays vendor-neutral.

## Requirements

You need **Sky v0.26.0 or later**: tool calling over the Responses API uses
`Std.Ai.Provider.customTools` and `ToolCall.continuation`, which first shipped in
v0.26.0. On an older Sky the package fails to compile (`ToolCall` has no
`continuation` field). Check with:

```bash
sky --version   # sky v0.26.0 or later
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

For reasoning-capable models, opt in to `reasoning.effort` with a typed level.
The available level remains model-dependent; as an example, GPT-5.6 Luna supports `None`, `Low`,
`Medium`, `High`, `XHigh`, and `Max`.

```elm
reasoningProvider : Provider.Provider
reasoningProvider =
    Responses.providerWithReasoningEffort
        (Secret.fromEnv "OPENAI_API_KEY")
        "gpt-5.6-luna"
        Responses.High
```


### Native local tools

`Responses.provider` also works with `Agent.nativeToolLoop`. It advertises each
`Std.Ai.Tool` as a flat Responses `function` tool, executes it locally through the
stdlib loop, and sends tool results back with `previous_response_id`. Tool arguments
remain the JSON string passed to the tool's `exec`; the current `Tool` contract only
supplies a name and description, so its function schema is a permissive object.

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
- `SkyOpenAI.Responses.providerWithReasoningEffort` /
  `providerAtWithReasoningEffort` — opt into `reasoning.effort` for models that
  support it.
- `SkyOpenAI.Responses.encodeRequest` / `decodeResponse` — encode or decode raw
  plain-chat Responses API bodies yourself.
- `SkyOpenAI.Responses.encodeToolRequest` / `decodeToolResponse` — encode and
  decode native function-calling requests and responses. Provider-owned
  continuations use `previous_response_id` after a tool call.


## Roadmap

- Server-side built-in tools (`web_search`, `file_search`, `code_interpreter`).
- Stateful chaining for ordinary chat, outside `Agent.nativeToolLoop`.

## Test

```bash
sky test tests/ResponsesTest.sky
```

The tests encode and decode Responses bodies offline. No network, no key.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
