# Architecture

```text
Host TeenModo
  CLI/API | operation lock | Compose control | SQLite | reports | telemetry
                              |
                       Docker Compose network
                    backend controller + vendor engine
                    + optional backend middleware
```

The host discovers only backend package files and Compose metadata. It never imports `engines/*/adapter.py`. The selected backend directory is mounted read-only at `/app/backend`; the controller loads `/app/backend/adapter.py` inside Docker.

The backend controller is not a remote enterprise agent. It is a small execution compartment belonging to one local backend package. The vendor engine and any required middleware remain sibling Compose services.

One backend package is active at a time. One engine/model/job operation is allowed globally. Persistent state is namespaced under `volume/engines/<engine>`.

The current local benchmark controller mounts the Docker socket because several vendor images expose installation and native-binary operations only through container execution/restart. This is a local-machine testing boundary, not a production security design. Backend HTTP/network operations should be preferred where available.

