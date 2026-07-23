# TeenModo 0.3.2

Corrective release for the container-controller architecture.

- fixes all bundled Docker Compose volume declarations;
- keeps the same three-command lifecycle for every backend;
- packages the controller runtime for source installs and tests;
- aligns CLI, controller image, and runtime versions;
- replaces stale agent naming with backend-controller naming;
- keeps backend-specific execution inside Docker;
- keeps model definitions declarative under each backend folder;
- preserves host telemetry, raw samples, GPU proof, reports, artifacts, and progress events.

The Docker socket is intentionally mounted only into the local controller compartment because current backend packages use Docker exec/restart for vendor containers. This is a local hardware-testing boundary, not a remote or enterprise deployment model.

