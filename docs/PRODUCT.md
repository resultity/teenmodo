# Product definition

TeenModo is an open-source Resultity Pre-Node tool that tests a particular computer with different local AI engines, models, and reusable workloads.

It answers:

- Can the engine start on this computer?
- Can the model be installed, loaded, and executed?
- Did the vendor engine container actually use the GPU?
- What were latency, throughput, CPU, RAM, GPU, VRAM, temperature, and power?
- What are the averages, accumulated totals, peaks, and ranges across repeated identical runs?
- Where is the evidence needed to inspect or compare the result later?

TeenModo collects host and container telemetry throughout each run. It stores raw JSONL samples, requests, responses, generated artifacts, SQLite history, and a portable final JSON report.

For Resultity early adopters, these results can help estimate hardware compatibility, practical workload coverage, and the approximate compute capacity a machine may later contribute.

TeenModo is not Resultity Node software. It does not connect to the network, schedule remote work, or guarantee future participation, reputation, RCP, rewards, or contribution level.

TeenModo is local and single-operation. It is not a remote node manager, distributed scheduler, model leaderboard, or automatic batch runner in the current release.
