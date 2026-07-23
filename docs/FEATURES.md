# Current features and limits

## Current product capabilities

- detect host platform and configured accelerator;
- verify Docker and Compose;
- verify NVIDIA access on the Linux/WSL2 host and inside Docker;
- discover engine packages without a host-side engine registry;
- install, start, stop, inspect, and uninstall engines;
- list, install, verify, and uninstall models;
- accept backend-specific direct model sources where implemented;
- list, show, and copy reusable YAML jobs;
- run one engine/model/job operation at a time;
- collect host and container CPU/RAM telemetry;
- collect NVIDIA GPU/VRAM/temperature/power telemetry;
- attribute GPU processes to the vendor engine container PID tree;
- validate simple output expectations;
- store run history in SQLite;
- write portable JSON reports and raw JSONL telemetry;
- store generated image, audio, transcription, and log artifacts;
- calculate report averages, accumulated totals, peaks, ranges, and GPU verification counts;
- expose the operational surface through both CLI and HTTP API;
- show active runtime filesystem paths.

## Included workload types

| Kind | Engines |
|---|---|
| Chat | Ollama, vLLM |
| Image generation | Diffusers/LocalAI, stable-diffusion.cpp |
| Audio transcription | whisper.cpp |
| Text to speech | Piper TTS |

## Current limits

- one run per command/API request;
- no batch suite or candidate-model runner;
- no automatic llmfit integration;
- no cross-machine leaderboard;
- no semantic model-quality benchmark framework;
- expectation checks are currently simple contains/JSON validations;
- NVIDIA has the strongest telemetry and GPU proof path;
- native Windows is unsupported;
- macOS Docker cannot provide Apple GPU proof;
- API long operations are synchronous and do not expose CLI-style progress streaming.

