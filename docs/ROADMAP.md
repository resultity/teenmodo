# Roadmap

This page contains planned work. It is not a current feature list.

## More engines and templates

- add and live-verify more text, image, audio, and video engines;
- add reusable jobs that test distinct performance and correctness characteristics;
- publish a hardware/engine/model acceptance matrix based on real runs.

## Full computer test batches

- execute a declared sequence of engine/model/job runs;
- repeat workloads automatically;
- preserve one batch identity and aggregate report;
- stop safely on hardware, model-load, or thermal failures;
- export a concise computer qualification result.

## Recommended model candidates

- import candidate recommendations from llmfit or other model-fit sources;
- map recommendations to engine-installable references;
- test candidates from smaller to larger models;
- distinguish full-GPU fit, partial offload, CPU fallback, failure, and unstable performance;
- produce a final recommended model range for the tested computer.

The roadmap must reuse current engine, model, job, telemetry, and report contracts rather than creating a second benchmarking system.

