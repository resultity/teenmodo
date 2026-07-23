# Ollama direct model installation

Ollama accepts a local alias plus a source reference. No model YAML is required.

```bash
teenmodo model install ollama ministral14b hf.co/mistralai/Ministral-3-14B-Instruct-2512-GGUF:Q4_K_M
```

Accepted source forms:

```text
ministral-3:14b
hf.co/OWNER/REPOSITORY:QUANTIZATION
```

Raw `https://...gguf` URLs are rejected with `MODEL_SOURCE_INVALID` because Ollama's pull API expects a registry or `hf.co` reference. Use the Hugging Face repository reference and quantization tag instead.

TeenModo stores the local alias in its manifest while Ollama retains the backend reference it actually pulled.

