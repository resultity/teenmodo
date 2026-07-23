# Filesystem navigation

Run:

```bash
teenmodo paths
```

This is the source of truth for active paths. With the default repository configuration:

```text
config/runtime.yaml          Runtime paths and operational settings
engines/                     Built-in engine packages
jobs/                        Built-in immutable job examples
volume/engines.d/            User-added engine packages
volume/jobs/                 User-created editable jobs
volume/in/                   Input files such as audio
volume/engines/              Downloaded models and engine state
volume/generated/            Generated Compose overrides and environment files
volume/out/                  Reports, raw samples, responses, and artifacts
volume/teenmodo.sqlite3      Indexed engine/model/run history
```

## Common navigation commands

```bash
# Show current runtime locations
teenmodo paths

# List custom jobs
find volume/jobs -maxdepth 1 -type f -name '*.yaml' -print

# List installed model manifests
find volume/engines -path '*/model-manifests/*.json' -print

# List report files
find volume/out -type f -name '*.json' | sort

# List raw telemetry files
find volume/out -type f -name metrics.jsonl | sort

# Show recent run folders
find volume/out -mindepth 3 -maxdepth 3 -type d | sort

# Read one final report
jq . volume/out/ENGINE/MODEL/RUN.json

# Read one request and response
jq . volume/out/ENGINE/MODEL/RUN_DIRECTORY/request.json
jq . volume/out/ENGINE/MODEL/RUN_DIRECTORY/response.json

# Inspect raw telemetry
head -n 10 volume/out/ENGINE/MODEL/RUN_DIRECTORY/metrics.jsonl
tail -n 10 volume/out/ENGINE/MODEL/RUN_DIRECTORY/metrics.jsonl

# Query run history directly
sqlite3 volume/teenmodo.sqlite3 \
  'select id, engine, model, job, status, started_at from runs order by id desc;'
```

## What users should edit

Normal users edit only copied jobs under `volume/jobs/`.

Engine developers edit engine packages under `engines/` or add user packages under `volume/engines.d/`.

Do not edit generated manifests, downloaded model data, generated Compose overrides, SQLite rows, or completed report files by hand.

