# HTTP API

Start the API:

```bash
teenmodo serve --host 127.0.0.1 --port 8787
```

Interactive OpenAPI documentation is available at `/docs` while the server is running.

## System

```text
GET /healthz
GET /doctor
GET /paths
```

## Engines

```text
GET    /engines
GET    /engines/{engine}
POST   /engines/{engine}/install
POST   /engines/{engine}/start
POST   /engines/{engine}/stop
DELETE /engines/{engine}?remove_images=false&remove_volume=false
```

Start a model-at-start engine:

```json
{"model": "qwen2.5-3b"}
```

## Models

```text
GET    /engines/{engine}/models/available?query=TEXT
GET    /engines/{engine}/models
POST   /engines/{engine}/models/install
POST   /engines/{engine}/models/verify
DELETE /engines/{engine}/models/{model}
```

Install a catalog model:

```json
{"model": "qwen2.5:3b"}
```

Install a direct-source model:

```json
{
  "model": "ministral14b",
  "source": "hf.co/mistralai/Ministral-3-14B-Instruct-2512-GGUF:Q4_K_M"
}
```

Verify:

```json
{"model": "ministral14b"}
```

## Jobs

```text
GET  /jobs?kind=chat
GET  /jobs/{job}
POST /jobs
```

Create a custom job:

```json
{"base": "chat_big", "alias": "my_chat_big"}
```

## Runs and reports

```text
POST /runs
GET  /reports?engine=ollama&model=ministral14b&limit=20
GET  /reports/summary?engine=ollama&model=ministral14b
GET  /reports/{run_id}
```

Run request:

```json
{"engine": "ollama", "model": "ministral14b", "job": "chat_big"}
```

## Flush

```text
POST /flush
```

The body must explicitly confirm deletion:

```json
{"confirm": true}
```

The API and CLI now expose the same engine, model-source, job, run, report, path, and flush operations. Long API operations currently return after completion; CLI progress rendering is not an HTTP streaming contract.

