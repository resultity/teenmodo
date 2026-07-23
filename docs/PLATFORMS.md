# Platform status

This page describes the current code, not planned support.

| Platform | Current status | GPU proof |
|---|---|---|
| Linux + NVIDIA | Primary supported path | Supported through `nvidia-smi` and container PID attribution |
| Windows + WSL2 + NVIDIA | Supported execution design; requires live validation on target hardware | Supported when WSL2, Linux containers, and NVIDIA container access work |
| Native Windows | Unsupported | Unsupported |
| macOS Apple Silicon | Docker CPU-only path; Apple GPU is not exposed to these containers | Unsupported |
| Intel macOS | Docker CPU-only where the selected engine image supports it | Unsupported |
| Linux AMD/Intel | Device mapping exists, but bundled engine support and telemetry are not fully verified | Not equivalent to NVIDIA proof |

## Linux NVIDIA

Requirements:

- Docker Engine or Docker Desktop using Linux containers;
- Docker Compose;
- NVIDIA driver;
- NVIDIA Container Toolkit;
- working `nvidia-smi` on the host and in a test container.

Validate:

```bash
teenmodo doctor
```

Expected core fields:

```text
docker: true
compose: true
nvidia_host: true
nvidia_container: true
support.status: ready
support.gpu_proof: supported
```

## Windows

Run TeenModo inside WSL2, not native PowerShell or CMD.

Requirements:

- Windows with WSL2;
- Ubuntu or another supported Linux distribution;
- Docker Desktop WSL2 backend or Docker Engine inside WSL2;
- WSL integration enabled for the distribution;
- current NVIDIA Windows driver with WSL GPU support;
- Linux containers.

Keep the repository inside the WSL filesystem, such as `~/src/teenmodo`, rather than `/mnt/c/...`, to avoid slow bind mounts and permission differences.

Validate inside WSL2:

```bash
uname -a
nvidia-smi
docker version
docker compose version
teenmodo doctor
```

## macOS

TeenModo remains Docker-first. Docker Desktop on macOS does not expose Apple Metal GPU execution to these engine containers, so TeenModo cannot prove Apple GPU use.

Current honest uses on macOS:

- CLI, API, catalog, job, report, and filesystem workflows;
- CPU-only engines where their Docker images support the Mac architecture;
- code and documentation testing.

Do not interpret a macOS Docker CPU result as Apple GPU performance.

## Compatibility verification status

The repository includes cross-platform unit/contract CI for Linux, Windows, and macOS. That checks Python imports, APIs, paths, platform detection, jobs, and persistence.

Live Docker/GPU acceptance still requires physical target hardware. Follow [TESTING.md](TESTING.md) before claiming a platform/engine combination as live verified.

