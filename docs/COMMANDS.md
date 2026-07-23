# CLI command reference

## Computer and paths

```text
teenmodo doctor
teenmodo paths
```

`doctor` checks Docker, Compose, host accelerator detection, container NVIDIA access, and current platform support status.

`paths` shows the active config, database, engine definitions, job definitions, state, generated Compose files, inputs, outputs, and normal report-file locations.

## Engines

```text
teenmodo engine list
teenmodo engine status ENGINE
teenmodo engine install ENGINE
teenmodo engine start ENGINE [--model MODEL]
teenmodo engine stop ENGINE
teenmodo engine uninstall ENGINE [--remove-images] [--remove-volume]
```

An engine is one replaceable backend package containing Compose metadata and a container-side adapter.

## Models

```text
teenmodo model available ENGINE [--query TEXT]
teenmodo model list ENGINE
teenmodo model install ENGINE MODEL [SOURCE]
teenmodo model verify ENGINE MODEL
teenmodo model uninstall ENGINE MODEL
```

`MODEL` is the local TeenModo model ID. `SOURCE` is optional and backend-specific. Ollama accepts registry or `hf.co` references. Piper accepts a direct ONNX URL. stable-diffusion.cpp accepts supported direct model files.

## Jobs

```text
teenmodo job list [--kind KIND]
teenmodo job show JOB
teenmodo job create BASE ALIAS
```

`job create` copies a built-in job to `volume/jobs/ALIAS.yaml` and changes its ID. The built-in job remains unchanged.

## Runs

```text
teenmodo run ENGINE MODEL JOB
```

One command performs one run. It writes a report even when execution fails.

## Reports

```text
teenmodo report list [--engine ENGINE] [--model MODEL] [--limit NUMBER]
teenmodo report show RUN_ID
teenmodo report summary [--engine ENGINE] [--model MODEL]
```

`summary` returns averages, accumulated totals, peaks, ranges, and GPU verification counts.

## Cleanup and API

```text
teenmodo flush [--yes]
teenmodo serve [--host HOST] [--port PORT]
```

`flush` deletes run history, samples, and generated outputs. It preserves engine/model installation records, engine state, and job definitions.

`serve` exposes the same service layer through HTTP.

