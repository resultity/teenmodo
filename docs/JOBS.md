# Jobs

A job is a reusable YAML workload. It defines the input, runtime parameters, media type, and optional output expectations. A job does not install or select a model.

## Discover jobs

```bash
teenmodo job list
teenmodo job list --kind chat
teenmodo job show chat_big
```

Built-in jobs live under `jobs/` and are immutable examples.

## Create a custom job

```bash
teenmodo job create chat_big my_chat_big
```

TeenModo writes:

```text
volume/jobs/my_chat_big.yaml
```

Edit the copied file and run it:

```bash
nano volume/jobs/my_chat_big.yaml
teenmodo run ollama ministral14b my_chat_big
```

User jobs override built-ins with the same ID.

## Job fields

```yaml
version: 1
id: my_chat_big
kind: chat
media_type: text
description: Comparable long chat workload
input:
  messages:
    - role: user
      content: Write a hardware qualification guide.
parameters:
  temperature: 0.2
  max_output_tokens: 900
expect: {}
```

Current expectation checks support required response content and valid JSON. They are pass/fail checks, not a full model-quality benchmark.

## Built-in purposes

- `chat_smoke`: request path and exact response check;
- `chat_short`: short deterministic comparison;
- `chat_context`: prompt ingestion and recall;
- `chat_json`: structured output;
- `chat_big`: long generation throughput;
- `chat_sustained`: sustained decode and thermal load;
- `image_smoke`: fast image path check;
- `image_square`: larger image generation workload;
- `transcribe_short`: transcription input path;
- `vocalize_short`: text-to-speech path.

