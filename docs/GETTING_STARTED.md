# Getting started

This guide performs one complete computer test with Ollama.

## 1. Install TeenModo

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows, run these commands inside an Ubuntu WSL2 terminal. Native PowerShell execution is not supported.

## 2. Check the computer

```bash
teenmodo doctor
```

Read these fields first:

- `support.status`: whether the current host path is ready;
- `docker` and `compose`: both must be true;
- `accelerator`: detected execution device;
- `nvidia_host`: NVIDIA is visible to the host;
- `nvidia_container`: NVIDIA is visible inside Docker;
- `support.gpu_proof`: whether TeenModo can prove GPU use on this platform.

For Linux or WSL2 NVIDIA qualification, do not continue until `nvidia_host` and `nvidia_container` are true.

## 3. Inspect engines

```bash
teenmodo engine list
```

Install Ollama:

```bash
teenmodo engine install ollama
```

Check it:

```bash
teenmodo engine status ollama
```

## 4. Install a model

Use a bundled model profile:

```bash
teenmodo model available ollama
teenmodo model install ollama qwen2.5:3b
```

Or install a direct Ollama-compatible reference with a local alias:

```bash
teenmodo model install ollama ministral14b \
  hf.co/mistralai/Ministral-3-14B-Instruct-2512-GGUF:Q4_K_M
```

Verify and list installed models:

```bash
teenmodo model verify ollama ministral14b
teenmodo model list ollama
```

## 5. Choose a job

```bash
teenmodo job list --kind chat
teenmodo job show chat_short
```

Useful text jobs:

| Job | Purpose |
|---|---|
| `chat_smoke` | Installation and request-path check |
| `chat_short` | Short deterministic comparison |
| `chat_context` | Prompt ingestion and exact recall |
| `chat_json` | Structured-output check |
| `chat_big` | Long generation and throughput |
| `chat_sustained` | Sustained decode and thermal load |

## 6. Run the test

```bash
teenmodo run ollama ministral14b chat_big
```

TeenModo starts telemetry before inference, executes the job, validates simple expectations, writes artifacts, and stores the run in SQLite.

## 7. Collect a comparable sample

The current release runs one job per command. Run the same command three times:

```bash
teenmodo run ollama ministral14b chat_big
teenmodo run ollama ministral14b chat_big
teenmodo run ollama ministral14b chat_big
```

Do not change the model, job, context, output-token limit, or engine configuration between runs.

## 8. Read the results

```bash
teenmodo report list --engine ollama --model ministral14b
teenmodo report show RUN_ID
teenmodo report summary --engine ollama --model ministral14b
```

Continue with [RESULTS.md](RESULTS.md).

