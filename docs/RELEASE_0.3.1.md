# TeenModo 0.3.1

- Reframed the Docker-side execution compartment as a per-backend controller rather than a product-level agent.
- Backend package contract now includes `backend.yaml`, `compose.yaml`, container-only `adapter.py`, and declarative `models/*.yaml`.
- The selected backend folder is mounted into the controller; the controller image no longer bundles every backend.
- Diffusers aliases moved from Python into YAML model profiles.
- Preserved the universal three-command lifecycle, progress events, one-operation lock, SQLite records, reports, raw metrics, and GPU proof.
- Kept backend state isolated under `volume/engines/<engine>` and allowed optional middleware services in each Compose package.

