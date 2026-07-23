from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

import yaml

from teenmodo.exceptions import ConfigurationError


@dataclass(frozen=True)
class RuntimeConfig:
    project_root: Path
    source: Path
    engine_roots: tuple[Path, ...]
    job_roots: tuple[Path, ...]
    input_root: Path
    output_root: Path
    state_root: Path
    generated_root: Path
    database_path: Path
    lock_path: Path
    docker_command: str
    compose_command: tuple[str, ...]
    sample_interval_seconds: float
    command_timeout_seconds: float
    operation_stall_timeout_seconds: float
    readiness_timeout_seconds: float
    allow_cpu_fallback: bool
    stop_other_engines_before_start: bool
    bind_host: str
    controller_port: int
    controller_image: str
    build_controller: bool
    accelerator: str
    nvidia_gpu_selector: str
    prefer_cdi: bool
    gpu_min_utilization_percent: float
    gpu_min_vram_delta_mb: float
    retain_raw_samples: bool

    @property
    def controller_base_url(self) -> str:
        return f"http://{self.bind_host}:{self.controller_port}"

    def ensure_directories(self) -> None:
        for path in (
            *self.engine_roots,
            *self.job_roots,
            self.input_root,
            self.output_root,
            self.state_root,
            self.generated_root,
            self.database_path.parent,
            self.lock_path.parent,
        ):
            path.mkdir(parents=True, exist_ok=True)


def _resolve(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (root / path).resolve()


def load_runtime(path: Path | None = None) -> RuntimeConfig:
    if path is not None:
        source = path.expanduser().resolve()
        project_root = source.parent.parent
    else:
        project_root = Path(os.getenv("TEENMODO_ROOT", Path.cwd())).expanduser().resolve()
        source = (project_root / "config" / "runtime.yaml").resolve()
    if not source.exists():
        raise ConfigurationError("Runtime configuration file does not exist", path=str(source))
    raw = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    if raw.get("version") != 1:
        raise ConfigurationError("Unsupported runtime configuration version", version=raw.get("version"))
    paths = raw.get("paths", {})
    runtime = raw.get("runtime", {})
    controller = raw.get("controller", raw.get("agent", {}))
    platform = raw.get("platform", {})
    report = raw.get("report", {})
    required_paths = ["engines", "jobs", "input", "output", "state", "generated", "database", "lock"]
    missing = [name for name in required_paths if name not in paths]
    if missing:
        raise ConfigurationError("Runtime paths are incomplete", missing=missing)
    engine_roots = (_resolve(project_root, paths["engines"]),)
    if paths.get("user_engines"):
        engine_roots += (_resolve(project_root, paths["user_engines"]),)
    job_roots: tuple[Path, ...] = ()
    if paths.get("user_jobs"):
        job_roots += (_resolve(project_root, paths["user_jobs"]),)
    job_roots += (_resolve(project_root, paths["jobs"]),)
    config = RuntimeConfig(
        project_root=project_root,
        source=source,
        engine_roots=engine_roots,
        job_roots=job_roots,
        input_root=_resolve(project_root, paths["input"]),
        output_root=_resolve(project_root, paths["output"]),
        state_root=_resolve(project_root, paths["state"]),
        generated_root=_resolve(project_root, paths["generated"]),
        database_path=_resolve(project_root, paths["database"]),
        lock_path=_resolve(project_root, paths["lock"]),
        docker_command=str(runtime.get("docker_command", "docker")),
        compose_command=tuple(runtime.get("compose_command", ["docker", "compose"])),
        sample_interval_seconds=float(runtime.get("sample_interval_seconds", 0.5)),
        command_timeout_seconds=float(runtime.get("command_timeout_seconds", 7200)),
        operation_stall_timeout_seconds=float(runtime.get("operation_stall_timeout_seconds", 300)),
        readiness_timeout_seconds=float(runtime.get("readiness_timeout_seconds", 600)),
        allow_cpu_fallback=bool(runtime.get("allow_cpu_fallback", False)),
        stop_other_engines_before_start=bool(runtime.get("stop_other_engines_before_start", True)),
        bind_host=str(runtime.get("bind_host", "127.0.0.1")),
        controller_port=int(controller.get("port", 18787)),
        controller_image=str(controller.get("image", "teenmodo/controller:0.4.0")),
        build_controller=bool(controller.get("build_local", True)),
        accelerator=str(platform.get("accelerator", "auto")),
        nvidia_gpu_selector=str(platform.get("nvidia_gpu_selector", "all")),
        prefer_cdi=bool(platform.get("prefer_cdi", False)),
        gpu_min_utilization_percent=float(report.get("gpu_min_utilization_percent", 5)),
        gpu_min_vram_delta_mb=float(report.get("gpu_min_vram_delta_mb", 64)),
        retain_raw_samples=bool(report.get("retain_raw_samples", True)),
    )
    config.ensure_directories()
    return config
