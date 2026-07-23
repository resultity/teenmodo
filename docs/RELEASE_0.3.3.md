# TeenModo 0.3.3

This release corrects model installation without changing the three-command workflow.

- Every bundled backend now resolves installable models from `engines/<engine>/models/*.yaml`; Python contains no bundled model catalog.
- Ollama resolves its registry reference from YAML and reports pull bytes.
- vLLM downloads only declared Hugging Face files into a human-readable model folder, keeps no duplicate snapshot cache, smoke-loads the local path, and exposes the configured model ID at runtime.
- whisper.cpp resolves its URL, storage directory, and filename from YAML and streams resumable byte progress.
- Diffusers accepts capability-specific backend folders such as `cuda12-diffusers` and downloads only declared files.
- Hugging Face and direct-file installations use staging, retry/resume, measurable byte progress, atomic activation, rollback, and no cache inside the final model directory.
- Controller containers use the host UID/GID for writable state, so a clean installation does not create root-owned model files.
- The host remains generic: it launches Compose, records SQLite state, captures telemetry, renders progress, and passes a controller-verified runtime reference for engines that load a model at container start.
- Metrics, raw samples, GPU proof, reports, and the fixed CLI sequence remain intact.

Live Docker execution still has to be verified on each target laptop and accelerator.

