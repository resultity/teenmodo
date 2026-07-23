# Quick start

The current user-first quick start is [GETTING_STARTED.md](GETTING_STARTED.md).

Minimal Ollama flow:

```bash
teenmodo doctor
teenmodo engine install ollama
teenmodo model install ollama qwen2.5:3b
teenmodo run ollama qwen2.5:3b chat_short
teenmodo report summary --engine ollama --model qwen2.5:3b
```

