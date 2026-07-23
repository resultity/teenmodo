# Testing TeenModo

Testing has two levels: repository checks and live computer qualification.

## Repository checks

```bash
python -m compileall -q teenmodo controller engines tests
pytest -q
```

The GitHub Actions workflow runs cross-platform contract tests on Linux, Windows, and macOS and the full test suite on Linux.

## Live acceptance test

Run this on every platform/hardware combination before calling it verified.

### 1. Doctor

```bash
teenmodo doctor
```

Save the output. On Linux/WSL2 NVIDIA, require host and container NVIDIA checks to pass.

### 2. Engine lifecycle

```bash
teenmodo engine install ollama
teenmodo engine status ollama
teenmodo engine stop ollama
teenmodo engine start ollama
```

### 3. Model lifecycle

```bash
teenmodo model install ollama qwen2.5:3b
teenmodo model verify ollama qwen2.5:3b
teenmodo model list ollama
```

### 4. Smoke run

```bash
teenmodo run ollama qwen2.5:3b chat_smoke
```

Require a passed run and expected response.

### 5. Comparable performance sample

```bash
teenmodo run ollama qwen2.5:3b chat_short
teenmodo run ollama qwen2.5:3b chat_short
teenmodo run ollama qwen2.5:3b chat_short
teenmodo report summary --engine ollama --model qwen2.5:3b
```

Check:

- three passed runs;
- GPU proof on supported GPU platforms;
- stable output throughput;
- sensible inference range;
- VRAM, RAM, temperature, and power values;
- accumulated token and timing totals.

### 6. Sustained test

```bash
teenmodo run ollama qwen2.5:3b chat_sustained
```

Check for thermal throttling, speed collapse, memory growth, and failed GPU attribution.

### 7. Artifact inspection

```bash
teenmodo paths
find volume/out/ollama/qwen2.5_3b -type f | sort
```

Confirm the final report, request, response, and raw samples exist.

## Platform acceptance record

For each live test, record:

```text
OS and version
CPU
RAM
GPU and VRAM
GPU driver
Docker and Compose versions
TeenModo commit/version
engine image
model and quantization
job
run IDs
result summary
known limitations
```

Static CI does not prove live GPU compatibility. Only this acceptance sequence does.

