# TeenModo 0.2.3

- Adds `teenmodo model available <engine> --query <text>`.
- Diffusers validates exact LocalAI gallery IDs before installation.
- Diffusers installs through LocalAI `/models/apply` and polls `/models/jobs/<uuid>` for real progress.
- Displays LocalAI progress, message, downloaded size, file size, and elapsed time.
- Adds configurable operation stall detection and a two-hour default install timeout.
- Unknown or stalled models fail without creating SQLite installation records.
- Keeps engine-specific logic inside `engines/diffusers/adapter.py`; the core contains no Diffusers model IDs.

