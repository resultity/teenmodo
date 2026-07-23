# TeenModo

**TE**ster of **EN**gines and **MO**dels in **DO**cker.

TeenModo is an open-source Resultity Pre-Node tool for testing one computer with different local AI engines, models, and reusable workloads.

It measures performance, continuously samples host and container telemetry during each run, verifies whether the engine process actually used the GPU, and writes portable reports for later inspection and comparison.

It is intended for questions such as:

- Can this computer run the selected engine and model?
- Did inference really use the GPU?
- Does the model fit, or is it heavily offloaded to CPU and system RAM?
- What are the average latency and throughput across repeated identical runs?
- What CPU, RAM, GPU, VRAM, temperature, and power behavior was observed?
- Where are the request, response, raw telemetry, summary, and generated artifacts?

## Resultity Pre-Node

TeenModo is an early hardware qualification tool from [Resultity](https://resultity.com).

It allows early adopters to test local hardware before running future Resultity Node software. The collected reports can help estimate:

- hardware and engine compatibility;
- which model and workload classes a computer can execute;
- whether GPU acceleration is materially available;
- practical throughput, latency, memory pressure, and sustained behavior;
- the range of network workloads the hardware may later be able to cover;
- the approximate compute capacity the machine may be able to contribute.

TeenModo is not Resultity Node software and does not connect the computer to the Resultity network. A TeenModo result is local qualification evidence, not a guarantee of future network eligibility, uptime, rewards, or contribution level.

Users are encouraged to publish hardware notes and non-sensitive result summaries to help build a practical compatibility record for early Resultity participants.

Resultity:

- Website: [resultity.com](https://resultity.com)
- Documentation: [docs.resultity.com](https://docs.resultity.com)
- GitHub: [github.com/resultity](https://github.com/resultity)
- X: [@resultity_ai](https://x.com/resultity_ai)
- Telegram: [@resultity](https://t.me/resultity)

## Current status

- Primary verified path: Linux with Docker and NVIDIA Container Toolkit.
- Windows path: TeenModo runs inside WSL2 using Linux containers. Native Windows execution is not supported.
- macOS path: Docker CPU workloads may run, but Docker does not expose the Apple GPU to TeenModo engine containers. GPU proof on macOS is currently unsupported.
- Runs are single operations. Batch qualification and automatic model-candidate testing are roadmap items, not current features.

## Five-minute Ollama test

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

teenmodo doctor
teenmodo engine install ollama
teenmodo model install ollama qwen2.5:3b
teenmodo job show chat_short
teenmodo run ollama qwen2.5:3b chat_short
teenmodo report list --engine ollama --model qwen2.5:3b
teenmodo report summary --engine ollama --model qwen2.5:3b
```

For a direct Ollama or Hugging Face registry reference:

```bash
teenmodo model install ollama ministral14b \
  hf.co/mistralai/Ministral-3-14B-Instruct-2512-GGUF:Q4_K_M
```

## What a run stores

Every run writes:

```text
volume/out/ENGINE/MODEL/
├── 000001_TIMESTAMP.json
└── 000001_TIMESTAMP/
    ├── request.json
    ├── response.json
    ├── metrics.jsonl
    └── generated artifacts
```

TeenModo samples telemetry throughout the run and stores both raw measurements and an aggregated report.

The report includes:

- input and output usage;
- model load, warmup, inference, and total duration;
- input and output throughput where the backend exposes it;
- CPU and RAM averages and peaks;
- GPU utilization, VRAM, temperature, and power where available;
- container PID to GPU-process matching;
- GPU execution verdict;
- engine, model, job, platform, and artifact identity;
- averages, accumulated totals, peaks, and ranges across matching passed runs.

Use `teenmodo paths` to show the active runtime folders.

## Included engines

| Engine | Workload | Current acceleration path |
|---|---|---|
| Ollama | Chat | NVIDIA Docker, CPU fallback where supported |
| vLLM | Chat | NVIDIA Docker |
| whisper.cpp | Transcription | NVIDIA Docker or CPU, engine-dependent |
| Diffusers/LocalAI | Image generation | NVIDIA Docker |
| stable-diffusion.cpp | Image generation | NVIDIA Docker; CPU image/configuration required for CPU-only hosts |
| Piper TTS | Text to speech | CPU |

## Documentation

Start with [docs/README.md](docs/README.md).

The important pages are:

- [Resultity Pre-Node role](docs/RESULTITY.md)
- [Getting started](docs/GETTING_STARTED.md)
- [Collecting and reading results](docs/RESULTS.md)
- [Complete CLI reference](docs/COMMANDS.md)
- [HTTP API](docs/API.md)
- [Filesystem navigation](docs/FILES.md)
- [Platform status](docs/PLATFORMS.md)
- [Testing TeenModo](docs/TESTING.md)
- [Extending engines, models, and jobs](docs/EXTENDING.md)
- [Current features and limits](docs/FEATURES.md)
- [Roadmap](docs/ROADMAP.md)

## Development verification

```bash
python -m compileall -q teenmodo controller engines tests
pytest -q
```

TeenModo mounts the Docker socket into the local backend controller. This is a privileged local-machine testing boundary. Run only trusted TeenModo engine packages.

## License

TeenModo source code is released under the [MIT License](LICENSE).

Third-party engines, container images, models, weights, and datasets keep their own licenses and usage terms.
