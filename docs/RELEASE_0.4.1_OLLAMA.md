# Ollama direct-source patch

- Adds `teenmodo model install ollama ALIAS SOURCE`.
- Preserves catalog installation when SOURCE is omitted.
- Supports Ollama registry references and `hf.co/...:QUANTIZATION` references.
- Rejects raw HTTP URLs with an actionable stable error.
- Persists source and source kind in the generated model manifest.

