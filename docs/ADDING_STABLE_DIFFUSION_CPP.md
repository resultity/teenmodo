# Add stable-diffusion.cpp to TeenModo 0.3.3

This package is a drop-in backend. It adds no host-side backend branch and keeps the standard lifecycle:

```bash
teenmodo engine install stable_diffusion_cpp
teenmodo model install stable_diffusion_cpp sd15
teenmodo run stable_diffusion_cpp sd15 image_smoke
```

## Install the package

Run from the TeenModo project root:

```bash
unzip -o /path/to/teenmodo-stable-diffusion-cpp-addon-0.1.0.zip
python -m pip install -e .
```

TeenModo discovers `engines/stable_diffusion_cpp` automatically. No registry edit is required.

## NVIDIA Linux or Windows WSL2

The bundled Compose file uses the official CUDA image:

```text
ghcr.io/leejet/stable-diffusion.cpp:master-cuda@sha256:924662c3467d8921de950f6bad6405ac5052c52e2c239cb655bb4df4cf907cf7
```

Use the three standard commands above.

## macOS Docker Desktop

Docker Desktop does not expose Apple Metal to Linux containers. To run a CPU-only capacity test, change this one default in `engines/stable_diffusion_cpp/compose.yaml`:

```yaml
image: ${TEENMODO_ENGINE_IMAGE:-ghcr.io/leejet/stable-diffusion.cpp:master}
```

The TeenModo command sequence remains unchanged. This measures Docker CPU performance, not Apple GPU performance.

## Add another model

Copy `engines/stable_diffusion_cpp/models/sd15.yaml` to a new YAML file and change:

- `id`
- `source.url`
- optional `source.sha256` and `source.size_bytes`
- `storage.directory`
- `storage.filename`
- model-specific runtime arguments under `runtime`

No Python registry or host-code edit is required.

## Storage and execution

- Model file: `volume/engines/stable_diffusion_cpp/models/<declared-directory>/`
- Temporary downloads: `volume/engines/stable_diffusion_cpp/models/.staging/`
- Manifests: `volume/engines/stable_diffusion_cpp/model-manifests/`
- Reports and images: `volume/out/stable_diffusion_cpp/...`
- Model download, verification, and adapter logic execute in the controller container.
- Image inference executes in the official stable-diffusion.cpp engine container.
- Host TeenModo handles Compose, locking, telemetry, SQLite, reports, and CLI progress.

