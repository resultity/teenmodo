# Collecting and reading results

TeenModo keeps individual run evidence and an aggregate summary.

## Individual runs

List recent runs:

```bash
teenmodo report list --engine ollama --model ministral14b --limit 20
```

Show one full report:

```bash
teenmodo report show 5
```

The report contains five important groups.

### `run`

Identity and status:

- run ID;
- timestamps;
- engine;
- model;
- job;
- media type;
- passed or failed.

### `performance`

Common fields:

- `backend_start_ms`: Compose and readiness cost;
- `model_load_ms`: backend-reported model loading where available;
- `warmup_ms`: pre-run warmup;
- `inference_ms`: measured workload execution;
- `total_ms`: complete TeenModo operation;
- `input_per_second`: prompt/input throughput where exposed;
- `output_per_second`: generation throughput;
- `unit`: tokens/s, images/s, or workload-specific unit;
- `run_mode`: cold or warm.

For Ollama, TeenModo promotes both prompt processing speed and output generation speed when Ollama returns the required durations.

### `resources`

Important fields:

- `container_cpu_avg_percent` and `container_cpu_peak_percent`;
- `container_ram_avg_mb` and `container_ram_peak_mb`;
- `gpu_avg_percent` and `gpu_peak_percent`;
- `vram_avg_mb` and `vram_peak_mb`;
- `gpu_temperature_peak_c`;
- `gpu_power_avg_w` and `gpu_power_peak_w`;
- `container_gpu_pids`;
- `gpu_execution`.

### `gpu_proof`

`VERIFIED` means TeenModo matched a GPU compute PID to the vendor engine container process tree and observed GPU activity or process VRAM.

Other verdicts:

- `PARTIAL`: GPU process evidence exists but the configured activity threshold was not reached;
- `NOT_DETECTED`: GPU use was requested but not observed;
- `UNVERIFIABLE`: the platform or telemetry path cannot prove GPU use.

A GPU verdict proves execution placement. It does not prove that the whole model fit in VRAM. High system RAM and CPU use alongside full VRAM can indicate offload.

### `artifacts`

The report points to the run directory containing:

- `request.json`;
- `response.json`;
- `metrics.jsonl`;
- generated image, audio, transcript, or log artifacts.


## Resultity qualification use

The reports are local evidence for early hardware qualification. They can help estimate which model and workload classes the computer may later cover as a Resultity node candidate and the approximate capacity it may be able to contribute.

They do not register the machine with Resultity and do not guarantee future eligibility, uptime, RCP, rewards, or contribution level.

TeenModo stores raw telemetry as well as aggregate reports. Before publishing raw run folders, review prompts, responses, absolute paths, inputs, and generated artifacts for private information.

## Average and accumulated metrics

```bash
teenmodo report summary --engine ollama --model ministral14b
```

The summary contains:

- `averages`: mean timing, throughput, GPU, VRAM, and container RAM across passed runs;
- `accumulated`: total input/output tokens or bytes and total timing across passed runs;
- `peaks`: highest GPU, VRAM, RAM, temperature, and power values;
- `ranges`: minimum and maximum throughput and inference time;
- `gpu_verified`: number of passed runs with verified GPU execution;
- `gpu_verified_percent`: share of passed runs with verified GPU execution.

Old flat summary fields remain for compatibility.

## Is the average time decent?

There is no universal good inference time. Compare only runs with the same:

- engine and engine image;
- model and quantization;
- job;
- input/context;
- output-token limit;
- platform and power mode.

Use this order:

1. All runs should pass.
2. GPU proof should be `VERIFIED` on supported GPU platforms.
3. `output_per_second` should be stable across warm runs.
4. `inference_ms` should not vary sharply without a known cause.
5. VRAM should remain below the point where the engine fails or begins unwanted offload.
6. Temperature and power should stabilize during sustained tests.

A three-run sample is enough for a first check. More runs are useful when results vary, but the current release does not automate batches.

## Raw inspection

Show runtime folders:

```bash
teenmodo paths
```

Inspect the latest report files:

```bash
find volume/out -type f | sort
jq . volume/out/ollama/ministral14b/000005_*.json
head -n 5 volume/out/ollama/ministral14b/000005_*/metrics.jsonl
jq . volume/out/ollama/ministral14b/000005_*/response.json
```
