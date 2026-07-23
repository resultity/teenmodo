# Resultity Pre-Node role

TeenModo is an open-source hardware qualification tool developed for the earliest Resultity adopters.

Its current role is simple: test one computer locally, collect evidence, and help the user understand what that computer can actually run.

## What it qualifies

TeenModo tests combinations of:

```text
computer
engine
model
job
```

For each run it checks:

- whether the engine starts;
- whether the model installs, loads, and executes;
- whether GPU execution can be materially verified;
- latency and throughput;
- CPU and RAM behavior;
- GPU utilization and VRAM behavior;
- temperature and power where the platform exposes them;
- output validity and generated artifacts.

## Telemetry and reports

TeenModo starts host-side telemetry before the workload runs. It samples host, container, and supported GPU measurements during execution.

Each run preserves:

```text
final JSON report
raw metrics.jsonl telemetry
request
response
generated artifacts
SQLite history record
```

Matching passed runs can be summarized into:

- average timings and throughput;
- accumulated input/output usage and runtime;
- minimum and maximum ranges;
- resource peaks;
- GPU verification counts.

This allows a result to be inspected instead of relying on a claim that a model merely started.

## Relationship to future Resultity participation

TeenModo reports may help estimate:

- which engines and model sizes are practical on the computer;
- which workload classes the hardware may be able to cover;
- whether the machine can sustain useful inference;
- the approximate compute capacity it may later contribute.

TeenModo is not Resultity Node software. It does not register the machine, schedule network work, measure uptime, assign reputation, issue RCP, or guarantee future eligibility or rewards.

Its output is local compatibility and performance evidence that can inform later Resultity Node qualification.

## Sharing results

Users may publish non-sensitive summaries and hardware notes to help build a practical compatibility record.

Before sharing raw files, review `request.json`, `response.json`, paths, prompts, inputs, and generated artifacts. They may contain private information.

## Resultity

- Website: [resultity.com](https://resultity.com)
- Documentation: [docs.resultity.com](https://docs.resultity.com)
- GitHub: [github.com/resultity](https://github.com/resultity)
- X: [@resultity_ai](https://x.com/resultity_ai)
- Telegram: [@resultity](https://t.me/resultity)

TeenModo source code is released under the MIT License. Third-party engines and models retain their own licenses.
