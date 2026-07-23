# TeenModo 0.2.2

## Fixes

- Diffusers engine no longer asks LocalAI to download the Diffusers backend during boot. TeenModo first starts the LocalAI control service, then installs the already pulled backend OCI image from the local Docker cache.
- Readiness failures now include container logs and stop early if the container exits.
- CLI error rendering no longer passes an unsupported `stderr` argument to Rich.
- Existing Docker images and persistent engine volumes remain reusable.

