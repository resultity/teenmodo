# Adding a backend

Create `engines/<id>/` or `volume/engines.d/<id>/` with:

```text
backend.yaml
compose.yaml
adapter.py
models/*.yaml
```

`backend.yaml` declares the package. `compose.yaml` contains the vendor engine, the backend controller, and any backend-specific middleware. Every service is attached to the same Compose network by default.

Required Compose roles:

- `engine`, labeled `io.teenmodo.role: engine`;
- `controller`, labeled `io.teenmodo.role: controller`.

Both services carry `io.teenmodo.engine: <id>`. The controller mounts only this backend folder at `/app/backend`; `adapter.py` executes inside that controller container. Host TeenModo does not import it.

The adapter implements the generic lifecycle from `controller/base.py`. The base class also loads model profiles from the backend's `models/` directory, so adding a model does not require host changes:

```text
install_engine
verify_engine
install_model
verify_model
list_models
uninstall_model
run_job
```

That keeps the user workflow identical:

```bash
teenmodo engine install BACKEND
teenmodo model install BACKEND MODEL
teenmodo run BACKEND MODEL JOB
```

## Adding a model

Add one YAML file under `engines/<backend>/models/`. The adapter reads model declarations; the host does not contain model aliases.

For a Hugging Face component model, declare exact files when disk use matters:

```yaml
version: 1
id: example
storage:
  directory: example
source:
  type: huggingface_snapshot
  repository: owner/repository
  revision: main
  download:
    max_total_bytes: 4000000000
    files:
      - model_index.json
      - remote: unet/model.fp16.safetensors
        target: unet/model.safetensors
runtime:
  backend: diffusers
  precision: fp16
verification:
  job: image_smoke
```

Use `include`, `exclude`, and `required` patterns instead of `files` only when the repository layout is stable and every selected file is needed. Do not use an unfiltered repository snapshot for benchmark models.

## Persistent ownership

Backend data lives under `volume/engines/<backend>/`. The controller runs with the host UID/GID on Linux and macOS so models, manifests, and outputs remain removable by the host user. Vendor containers may still require root internally.

Validation:

```bash
python -m compileall -q teenmodo controller engines tests
pytest -q
```

## Model-at-start engines

When a backend such as vLLM must start its vendor container with a selected model, `verify_model` returns a generic `runtime_reference`. TeenModo stores that proof and passes the reference plus the public model ID into Compose as `TEENMODO_MODEL` and `TEENMODO_MODEL_ID`. The host does not interpret the path or repository.

Direct downloads should stage under `volume/engines/<backend>/models/.staging`, verify, and atomically move into the configured storage directory. Interrupted staging data must not be registered as an installed model.

## 0.4.0 user-facing contract

Adding a backend is the only normal reason to add or edit project files. A backend package must implement the three public operations without requiring host changes:

```text
teenmodo engine install ENGINE
teenmodo model install ENGINE ALIAS [SOURCE]
teenmodo run ENGINE ALIAS JOB
```

Do not add a host-side model registry. A backend may support direct sources, named upstream references, or both. It must validate the source, stage downloads, verify a real load, write a generated manifest, and roll back on failure.

Reuse the canonical job library whenever the payload shape already exists. Users create editable jobs with:

```text
teenmodo job create BASE ALIAS
```

For a genuinely new payload shape, add one minimal canonical base job under `jobs/<media>/`, document the supported base aliases here, and add tests proving the backend accepts the matching job kind.

