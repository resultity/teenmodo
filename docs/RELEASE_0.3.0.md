# TeenModo 0.3.0

## Delivered

- Host core contains no engine-specific adapter imports or registry.
- Every engine package launches one vendor engine and one containerized agent.
- Stable host-to-agent HTTP/NDJSON protocol with progress and structured errors.
- One active engine package and one global operation lock.
- Honest three-command lifecycle: engine install, model install, run.
- Diffusers backend installation checks concrete `/backends/diffusers` runtime files.
- Diffusers model installation downloads weights into an isolated folder, writes LocalAI config, restarts LocalAI, and runs a smoke image before registration.
- `sd15` curated alias plus `image_smoke` and `image_square` jobs.
- Ollama pull followed by actual model load/smoke.
- vLLM snapshot download followed by a temporary real server load and completion smoke.
- whisper.cpp download followed by a real model-load transcription smoke.
- Run reports split backend startup, model load where observable, warmup, inference, and total wall time.
- Host GPU proof remains attributed to the vendor engine container PID tree.
- Fresh source archive excludes virtual environments, generated state, model weights, reports, caches, and credentials.

## Known boundary

The agent currently uses the Docker socket for vendor-container control. This is intentional for the local benchmark and future replaceable-agent model, but it is a privileged boundary and requires a trusted agent image.

