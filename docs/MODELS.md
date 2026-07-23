# Model installation

## User contract

```text
teenmodo model install ENGINE ALIAS SOURCE
```

No YAML is required. The backend owns file-format rules and verification. TeenModo owns orchestration, locking, progress, persistence, and reports.

A two-argument command remains valid for a backend-bundled catalog alias:

```text
teenmodo model install ENGINE MODEL
```

## Direct source rules

The current `stable_diffusion_cpp` backend accepts direct `.gguf`, `.safetensors`, and `.ckpt` HTTP(S) files. It derives the filename, stores the file under `volume/engines/stable_diffusion_cpp/models/ALIAS/`, performs a one-step load/decode verification, and writes a generated manifest.

Other backends return `MODEL_SOURCE_UNSUPPORTED` until their adapter implements a safe direct-source contract. This is deliberate: the host never guesses backend-specific installation semantics.

## Installed truth

Installed models are discovered from verified generated manifests and real files, not from a hardcoded global model count.

## Ollama

Ollama accepts a direct registry reference without a model YAML:

```bash
teenmodo model install ollama ministral14b hf.co/mistralai/Ministral-3-14B-Instruct-2512-GGUF:Q4_K_M
```

