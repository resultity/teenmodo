# Extending TeenModo

TeenModo has three normal extension points: engines, models, and jobs.

## Add an engine

Create:

```text
engines/ENGINE/
├── backend.yaml
├── compose.yaml
├── adapter.py
└── models/
```

The host discovers the package. Do not add a central engine registry or host-side engine branch.

The package must support:

```text
install_engine
verify_engine
install_model
verify_model
list_models
uninstall_model
run_job
```

The controller loads `adapter.py` inside Docker. The adapter may call the vendor engine over HTTP or use the local Docker execution boundary where required.

Required proof:

- Compose validates;
- engine starts and verifies materially;
- model installation stages and rolls back safely;
- model verification performs a real load or smoke operation;
- one compatible job produces a report;
- failures return stable error codes;
- tests prove the host core remains engine-neutral.

See `templates/engine/` and `docs/ADDING_ENGINE.md`.

## Add a model

Prefer the public command when the backend supports direct sources:

```bash
teenmodo model install ENGINE ALIAS SOURCE
```

Use a declarative YAML profile under `engines/ENGINE/models/` only for a curated bundled model or when the backend needs a multi-file installation plan.

A model installer must:

- validate source and filenames;
- expose measurable download progress;
- stage incomplete files separately;
- verify size/hash when declared;
- activate atomically;
- run a real load/smoke check;
- write a generated manifest only after verification;
- restore the previous verified installation on failure.

## Add a job

First inspect existing jobs:

```bash
teenmodo job list
teenmodo job show chat_short
```

For a custom workload, copy one:

```bash
teenmodo job create chat_short my_test
nano volume/jobs/my_test.yaml
```

Add a built-in job under `jobs/` only when it represents a reusable test or a new payload shape.

A job defines:

- `id`;
- `kind`;
- `media_type`;
- input;
- parameters;
- optional expectations.

Add tests showing that compatible engines accept the job kind and incompatible engines reject it clearly.

