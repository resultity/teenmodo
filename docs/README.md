# TeenModo documentation

TeenModo tests one computer with one AI engine, one model, and one reusable job at a time. It collects host, container, and supported GPU telemetry throughout each run, then stores raw samples and portable reports for inspection and comparison.

## Start here

- [Resultity role](RESULTITY.md) — how TeenModo supports early hardware qualification.
- [Product definition](PRODUCT.md) — what TeenModo does and does not do.
- [Getting started](GETTING_STARTED.md) — complete first Ollama test.
- [Quick start](QUICKSTART.md) — minimal command sequence.

## Using TeenModo

- [Complete CLI commands](COMMANDS.md) — current command syntax and behavior.
- [CLI lifecycle](CLI.md) — compact lifecycle reference.
- [HTTP API](API.md) — endpoints and request examples.
- [Jobs](JOBS.md) — built-in jobs and editable custom jobs.
- [Models](MODELS.md) — catalog and direct-source installation.
- [Ollama direct models](OLLAMA_DIRECT_MODELS.md) — accepted Ollama source formats.
- [Collecting and reading results](RESULTS.md) — reports, telemetry, averages, accumulated totals, peaks, ranges, and GPU proof.
- [Filesystem navigation](FILES.md) — where models, jobs, reports, telemetry, and generated files live.
- [Platform status](PLATFORMS.md) — Linux, Windows/WSL2, and macOS support boundaries.
- [Troubleshooting](TROUBLESHOOTING.md) — common failures and first checks.
- [Error contract](ERRORS.md) — stable error codes and rollback behavior.
- [Upgrade notes](UPGRADE.md) — preserving or removing old runtime state.

## Extending TeenModo

- [Architecture](ARCHITECTURE.md) — host, controller, engine, telemetry, and storage boundaries.
- [Extension overview](EXTENDING.md) — engines, models, and jobs.
- [Adding an engine](ADDING_ENGINE.md) — backend package contract and validation.
- [Adding Piper TTS](ADDING_PIPER_TTS.md) — direct ONNX voice installation and vocalization jobs.
- [Adding stable-diffusion.cpp](ADDING_STABLE_DIFFUSION_CPP.md) — backend, model, and platform notes.
- [Testing](TESTING.md) — repository checks and live hardware acceptance.
- [Current features and limits](FEATURES.md) — implemented capabilities only.
- [Roadmap](ROADMAP.md) — planned engines, templates, batches, and model-candidate testing.

## Release history

- [0.4.1 Ollama direct-source patch](RELEASE_0.4.1_OLLAMA.md)
- [0.4.0](RELEASE_0.4.0.md)
- [0.3.3](RELEASE_0.3.3.md)
- [0.3.2](RELEASE_0.3.2.md)
- [0.3.1](RELEASE_0.3.1.md)
- [0.3.0](RELEASE_0.3.0.md)
- [0.2.3](RELEASE_0.2.3.md)
- [0.2.2](RELEASE_0.2.2.md)
- [0.2.1](RELEASE_0.2.1.md)

Release notes describe history. The user and developer guides above describe the current product.
