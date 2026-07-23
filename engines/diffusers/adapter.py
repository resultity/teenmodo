from __future__ import annotations

import base64
from dataclasses import dataclass
from fnmatch import fnmatchcase
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import time
from typing import Any, Iterator
from uuid import uuid4

import httpx
import yaml

from controller.base import DriverError, EngineAdapter, final_result


@dataclass(frozen=True)
class DownloadFile:
    remote: str
    target: str
    size: int
    sha256: str | None = None


def _safe_relative_path(value: str, *, field: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise DriverError("Model manifest contains an unsafe path", "MODEL_MANIFEST_ERROR", field=field, value=value)
    return path.as_posix()


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatchcase(path, pattern) or PurePosixPath(path).match(pattern) for pattern in patterns)


def _remote_size(sibling: Any) -> int:
    value = getattr(sibling, "size", None)
    if isinstance(value, int) and value >= 0:
        return value
    lfs = getattr(sibling, "lfs", None)
    if isinstance(lfs, dict):
        value = lfs.get("size")
    else:
        value = getattr(lfs, "size", None)
    return int(value) if isinstance(value, int) and value >= 0 else 0


def _remote_sha256(sibling: Any) -> str | None:
    lfs = getattr(sibling, "lfs", None)
    if isinstance(lfs, dict):
        value = lfs.get("sha256") or lfs.get("oid")
    else:
        value = getattr(lfs, "sha256", None) or getattr(lfs, "oid", None)
    if isinstance(value, str):
        value = value.removeprefix("sha256:")
        if re.fullmatch(r"[0-9a-fA-F]{64}", value):
            return value.lower()
    return None


class Adapter(EngineAdapter):
    id = "diffusers"
    name = "LocalAI Diffusers"
    version = "2.1.0"
    supported_job_kinds = ("image_generation",)

    @property
    def configs_root(self) -> Path:
        path = self.context.state_root / "localai-models"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _backend_path(self) -> str | None:
        command = [
            "/bin/sh",
            "-lc",
            'for d in /backends/*diffusers*; do [ -f "$d/backend.py" ] && [ -f "$d/run.sh" ] && { printf "%s" "$d"; exit 0; }; done; exit 1',
        ]
        try:
            value = self.context.docker.exec(command).strip()
        except DriverError:
            return None
        return value or None

    def _backend_installed(self) -> bool:
        return self._backend_path() is not None

    def _chown_backend_state(self) -> None:
        uid = os.getuid() if hasattr(os, "getuid") else 0
        gid = os.getgid() if hasattr(os, "getgid") else 0
        try:
            self.context.docker.exec(
                ["/bin/sh", "-lc", f"chown -R {uid}:{gid} /backends 2>/dev/null || true"],
                timeout=120,
            )
        except DriverError:
            return

    def install_engine(self) -> Iterator[dict[str, Any]]:
        yield self.progress("Waiting for LocalAI", phase="start", total=self.context.readiness_timeout)
        yield from self.wait_http("/readyz")
        if not self._backend_installed():
            yield self.progress("Installing the CUDA Diffusers backend inside LocalAI", completed=0, total=100)
            try:
                for line in self.context.docker.exec_lines(["/local-ai", "backends", "install", "diffusers"]):
                    match = re.search(r"\b(\d{1,3})%", line)
                    completed = min(100, int(match.group(1))) if match else None
                    yield self.progress(line, completed=completed, total=100)
            except DriverError:
                if not self._backend_installed():
                    raise
                yield self.progress("Backend installer returned non-zero after materializing verified files")
            backend_path = self._backend_path()
            if not backend_path:
                raise DriverError(
                    "Diffusers backend files were not installed",
                    "ENGINE_VERIFICATION_ERROR",
                    expected="/backends/*diffusers*/backend.py",
                )
            self._chown_backend_state()
            yield self.progress("Restarting LocalAI to activate Diffusers")
            self.context.docker.restart_engine()
            yield from self.wait_http("/readyz")
        verification = self.verify_engine()
        yield self.progress("Diffusers backend installed and active", phase="finish", completed=100, total=100)
        return verification

    def verify_engine(self) -> dict[str, Any]:
        try:
            response = httpx.get(f"{self.context.engine_url}/readyz", timeout=10)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise DriverError("LocalAI readiness verification failed", "ENGINE_VERIFICATION_ERROR", error=str(exc)) from exc
        backend_path = self._backend_path()
        if not backend_path:
            raise DriverError(
                "Diffusers backend is not materially installed",
                "ENGINE_VERIFICATION_ERROR",
                expected="/backends/*diffusers*/backend.py",
            )
        return {
            "ok": True,
            "ready": True,
            "backend": "diffusers",
            "backend_path": backend_path,
            "backend_files_verified": True,
            "execution_boundary": "controller-container",
        }

    def available_models(self, query: str | None = None) -> list[dict[str, Any]]:
        values = []
        for key, value in self.model_profiles().items():
            source = value.get("source") or {}
            values.append(
                {
                    "id": key,
                    "source": source.get("repository"),
                    "description": str(value.get("description") or "Declarative Diffusers profile"),
                }
            )
        if query:
            needle = query.lower()
            values = [item for item in values if needle in json.dumps(item).lower()]
        return values

    def _profile(self, model: str) -> dict[str, Any]:
        profile = self.model_profiles().get(model)
        if profile is None:
            raise DriverError(
                "Unknown Diffusers model; add a declarative YAML profile under engines/diffusers/models",
                "MODEL_UNAVAILABLE",
                model=model,
                available=sorted(self.model_profiles()),
            )
        return profile

    def _storage_key(self, model: str, profile: dict[str, Any] | None = None) -> str:
        profile = profile or self._profile(model)
        storage = profile.get("storage") or {}
        value = str(storage.get("directory") or model).strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value):
            raise DriverError("Invalid model storage directory", "MODEL_MANIFEST_ERROR", model=model, directory=value)
        return value

    def _model_path(self, model: str, profile: dict[str, Any] | None = None) -> Path:
        return self.context.models_root / self._storage_key(model, profile)

    def _backend_name(self, model: str, profile: dict[str, Any] | None = None) -> str:
        profile = profile or self._profile(model)
        runtime = profile.get("runtime") or {}
        value = str(runtime.get("name") or self._storage_key(model, profile)).strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value):
            raise DriverError("Invalid LocalAI model name", "MODEL_MANIFEST_ERROR", model=model, name=value)
        return value

    def _config_path(self, model: str, profile: dict[str, Any] | None = None) -> Path:
        return self.configs_root / f"{self._backend_name(model, profile)}.yaml"

    def _download_plan(self, model: str, profile: dict[str, Any], token: str | None) -> tuple[str, str, list[DownloadFile]]:
        source = profile.get("source") or {}
        if source.get("type") != "huggingface_snapshot":
            raise DriverError("Unsupported Diffusers source type", "MODEL_MANIFEST_ERROR", model=model, source_type=source.get("type"))
        repository = str(source.get("repository") or "").strip()
        revision = str(source.get("revision") or "main").strip()
        if not repository:
            raise DriverError("Diffusers model repository is missing", "MODEL_MANIFEST_ERROR", model=model)
        download = source.get("download") or {}
        try:
            from huggingface_hub import HfApi

            info = HfApi(token=token).model_info(repository, revision=revision, files_metadata=True)
        except Exception as exc:
            raise DriverError(
                "Could not read Hugging Face model file metadata",
                "MODEL_INSTALL_ERROR",
                model=model,
                repository=repository,
                revision=revision,
                error=str(exc),
            ) from exc
        siblings = {str(item.rfilename): item for item in (info.siblings or [])}
        plan: list[DownloadFile] = []
        exact = download.get("files") or []
        if exact:
            for entry in exact:
                if isinstance(entry, str):
                    remote = target = entry
                elif isinstance(entry, dict):
                    remote = str(entry.get("remote") or "")
                    target = str(entry.get("target") or remote)
                else:
                    raise DriverError("Invalid file entry in model manifest", "MODEL_MANIFEST_ERROR", model=model, entry=repr(entry))
                remote = _safe_relative_path(remote, field="remote")
                target = _safe_relative_path(target, field="target")
                sibling = siblings.get(remote)
                if sibling is None:
                    raise DriverError(
                        "Required model file is absent from the Hugging Face repository",
                        "MODEL_INSTALL_ERROR",
                        model=model,
                        repository=repository,
                        file=remote,
                    )
                plan.append(DownloadFile(remote, target, _remote_size(sibling), _remote_sha256(sibling)))
        else:
            include = [str(value) for value in download.get("include") or []]
            exclude = [str(value) for value in download.get("exclude") or []]
            required = [str(value) for value in download.get("required") or []]
            if not include:
                raise DriverError(
                    "Diffusers model manifest must declare exact files or include patterns",
                    "MODEL_MANIFEST_ERROR",
                    model=model,
                )
            selected = [
                path
                for path in sorted(siblings)
                if _matches(path, include) and not _matches(path, exclude)
            ]
            missing = [pattern for pattern in required if not any(_matches(path, [pattern]) for path in selected)]
            if missing:
                raise DriverError(
                    "Required model file patterns did not match repository files",
                    "MODEL_INSTALL_ERROR",
                    model=model,
                    repository=repository,
                    missing=missing,
                )
            for path in selected:
                target = _safe_relative_path(path, field="target")
                sibling = siblings[path]
                plan.append(DownloadFile(path, target, _remote_size(sibling), _remote_sha256(sibling)))
        if not plan:
            raise DriverError("Model manifest selected no downloadable files", "MODEL_INSTALL_ERROR", model=model)
        targets = [item.target for item in plan]
        if len(targets) != len(set(targets)):
            raise DriverError("Model manifest maps multiple files to one target", "MODEL_MANIFEST_ERROR", model=model)
        total = sum(item.size for item in plan)
        max_total = download.get("max_total_bytes")
        if isinstance(max_total, int) and max_total > 0 and total > max_total:
            raise DriverError(
                "Selected model files exceed the manifest disk limit",
                "MODEL_INSTALL_ERROR",
                model=model,
                selected_bytes=total,
                max_total_bytes=max_total,
            )
        return repository, revision, plan

    def _download_file(
        self,
        *,
        repository: str,
        revision: str,
        item: DownloadFile,
        destination: Path,
        token: str | None,
        completed_before: int,
        total_bytes: int,
        index: int,
        file_count: int,
    ) -> Iterator[dict[str, Any]]:
        try:
            from huggingface_hub import hf_hub_url
        except Exception as exc:
            raise DriverError("huggingface-hub is unavailable in the controller", "MODEL_INSTALL_ERROR", error=str(exc)) from exc
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_name(destination.name + ".part")
        expected = item.size
        url = hf_hub_url(repository, item.remote, revision=revision)
        last_error = ""
        for attempt in range(1, 4):
            offset = partial.stat().st_size if partial.exists() else 0
            if expected and offset > expected:
                partial.unlink(missing_ok=True)
                offset = 0
            if expected and offset == expected:
                partial.replace(destination)
                return
            headers = {"User-Agent": "teenmodo/0.4.0"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            if offset:
                headers["Range"] = f"bytes={offset}-"
            try:
                timeout = httpx.Timeout(connect=30, read=180, write=180, pool=30)
                with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=timeout) as response:
                    if offset and response.status_code == 200:
                        partial.unlink(missing_ok=True)
                        offset = 0
                    elif offset and response.status_code != 206:
                        response.raise_for_status()
                    else:
                        response.raise_for_status()
                    mode = "ab" if offset and response.status_code == 206 else "wb"
                    if mode == "wb":
                        offset = 0
                    current = offset
                    with partial.open(mode) as stream:
                        for chunk in response.iter_bytes(chunk_size=8 * 1024 * 1024):
                            if not chunk:
                                continue
                            stream.write(chunk)
                            current += len(chunk)
                            yield self.progress(
                                f"Downloading {index}/{file_count}: {item.remote}",
                                completed=completed_before + current,
                                total=total_bytes,
                                metadata={
                                    "unit": "bytes",
                                    "file": item.remote,
                                    "file_index": index,
                                    "file_count": file_count,
                                },
                            )
                actual = partial.stat().st_size
                if expected and actual != expected:
                    raise OSError(f"size mismatch: expected {expected}, received {actual}")
                if item.sha256:
                    digest = hashlib.sha256()
                    with partial.open("rb") as stream:
                        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                            digest.update(chunk)
                    if digest.hexdigest() != item.sha256:
                        raise OSError("SHA-256 mismatch")
                partial.replace(destination)
                return
            except Exception as exc:
                last_error = str(exc)
                if attempt < 3:
                    yield self.progress(
                        f"Retrying {item.remote} after download error ({attempt}/3)",
                        completed=completed_before + (partial.stat().st_size if partial.exists() else 0),
                        total=total_bytes,
                        metadata={"unit": "bytes", "error": last_error},
                    )
                    time.sleep(attempt * 2)
        raise DriverError(
            "Diffusers model file download failed",
            "MODEL_INSTALL_ERROR",
            repository=repository,
            file=item.remote,
            error=last_error,
        )

    def _download_selected_files(
        self,
        model: str,
        profile: dict[str, Any],
        destination: Path,
    ) -> Iterator[dict[str, Any]]:
        token = os.getenv("HF_TOKEN") or None
        yield self.progress(f"Resolving declared files for {model}", phase="start")
        repository, revision, plan = self._download_plan(model, profile, token)
        total_bytes = sum(item.size for item in plan)
        if total_bytes <= 0:
            raise DriverError(
                "Hugging Face did not provide file sizes; refusing an unmeasurable model installation",
                "MODEL_INSTALL_ERROR",
                model=model,
                repository=repository,
            )
        yield self.progress(
            f"Downloading {model} ({len(plan)} declared files)",
            phase="update",
            completed=0,
            total=total_bytes,
            metadata={"unit": "bytes", "file_count": len(plan)},
        )
        completed = 0
        for index, item in enumerate(plan, start=1):
            target = destination / item.target
            yield from self._download_file(
                repository=repository,
                revision=revision,
                item=item,
                destination=target,
                token=token,
                completed_before=completed,
                total_bytes=total_bytes,
                index=index,
                file_count=len(plan),
            )
            completed += target.stat().st_size
        manifest = {
            "repository": repository,
            "revision": revision,
            "total_bytes": completed,
            "files": [
                {"remote": item.remote, "target": item.target, "size": (destination / item.target).stat().st_size}
                for item in plan
            ],
        }
        (destination.parent / "download-manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        yield self.progress(
            f"Downloaded {model} without a duplicate model cache",
            phase="update",
            completed=completed,
            total=total_bytes,
            metadata={"unit": "bytes", "file_count": len(plan)},
        )
        return manifest

    def _generate(self, backend_name: str, prompt: str, width: int, height: int, steps: int, count: int) -> tuple[dict[str, Any], float]:
        payload = {
            "model": backend_name,
            "prompt": prompt,
            "size": f"{width}x{height}",
            "n": count,
            "response_format": "b64_json",
            "steps": steps,
        }
        started = time.monotonic()
        response = httpx.post(f"{self.context.engine_url}/v1/images/generations", json=payload, timeout=None)
        duration_ms = (time.monotonic() - started) * 1000
        if response.status_code >= 400:
            raise DriverError("LocalAI image generation failed", "RUN_EXECUTION_ERROR", status=response.status_code, body=response.text[-4000:])
        try:
            body = response.json()
        except ValueError as exc:
            raise DriverError("LocalAI returned invalid image JSON", "RUN_EXECUTION_ERROR", error=str(exc)) from exc
        return body, duration_ms

    def _runtime_config(self, model: str, profile: dict[str, Any], weights_dir: Path) -> dict[str, Any]:
        runtime = profile.get("runtime") or {}
        precision = str(runtime.get("precision") or "fp16").lower()
        scheduler = str(runtime.get("scheduler") or "euler_a")
        return {
            "name": self._backend_name(model, profile),
            "backend": str(runtime.get("backend") or "diffusers"),
            "parameters": {"model": str(weights_dir)},
            "cuda": self.context.accelerator == "nvidia",
            "f16": precision in {"fp16", "float16", "half"},
            "diffusers": {"scheduler_type": scheduler},
        }

    def install_model(self, model: str, source: str | None = None) -> Iterator[dict[str, Any]]:
        if source:
            raise DriverError("Direct model sources are not supported by this backend", "MODEL_SOURCE_UNSUPPORTED", engine=self.id, model=model, source=source)
        profile = self._profile(model)
        final_dir = self._model_path(model, profile)
        weights_dir = final_dir / "weights"
        config_path = self._config_path(model, profile)
        existing = self.verify_model(model)
        if existing.get("verified"):
            self._loaded_models.add(model)
            yield self.progress(f"{model} is already installed and verified", phase="finish")
            return

        staging_root = self.context.models_root / ".staging"
        backup_root = self.context.models_root / ".backup"
        staging_root.mkdir(parents=True, exist_ok=True)
        backup_root.mkdir(parents=True, exist_ok=True)
        storage_key = self._storage_key(model, profile)
        # One global operation is allowed, so leftovers with this model key are
        # necessarily from an interrupted earlier installation.
        for stale in staging_root.glob(f"{storage_key}-*"):
            shutil.rmtree(stale, ignore_errors=True)
        staging_dir = staging_root / f"{storage_key}-{uuid4().hex}"
        staging_weights = staging_dir / "weights"
        staging_weights.mkdir(parents=True, exist_ok=False)
        backup_dir = backup_root / f"{self._storage_key(model, profile)}-{uuid4().hex}"
        old_config = config_path.read_bytes() if config_path.exists() else None
        committed = False
        download_manifest: dict[str, Any] | None = None
        try:
            download_manifest = yield from self._download_selected_files(model, profile, staging_weights)
            if not any(path.is_file() for path in staging_weights.rglob("*")):
                raise DriverError("Diffusers model staging folder is empty", "MODEL_INSTALL_ERROR", model=model)
            if final_dir.exists():
                final_dir.replace(backup_dir)
            staging_dir.replace(final_dir)
            committed = True
            weights_dir = final_dir / "weights"
            config = self._runtime_config(model, profile, weights_dir)
            config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
            self.context.docker.restart_engine()
            yield from self.wait_http("/readyz")
            yield self.progress("Loading the model and running an installation smoke image (one-step 256x256)")
            body, warmup_ms = self._generate(self._backend_name(model, profile), "plain gray square", 256, 256, 1, 1)
            if not (body.get("data") or []):
                raise DriverError("Diffusers smoke generation returned no image", "MODEL_VERIFICATION_ERROR", model=model)
            installed_bytes = sum(path.stat().st_size for path in weights_dir.rglob("*") if path.is_file())
            self.write_manifest(
                model,
                {
                    "verified": True,
                    "source": (profile.get("source") or {}).get("repository"),
                    "source_revision": (profile.get("source") or {}).get("revision", "main"),
                    "backend_name": self._backend_name(model, profile),
                    "storage_directory": self._storage_key(model, profile),
                    "weights_path": str(weights_dir),
                    "config_path": str(config_path),
                    "installed_bytes": installed_bytes,
                    "file_count": len((download_manifest or {}).get("files") or []),
                    "install_warmup_ms": round(warmup_ms, 3),
                },
            )
            self._loaded_models.add(model)
            shutil.rmtree(backup_dir, ignore_errors=True)
            yield self.progress(
                f"Installed, loaded, and verified {model}",
                phase="finish",
                metadata={"warmup_ms": round(warmup_ms, 3), "installed_bytes": installed_bytes},
            )
        except BaseException:
            # Roll back on normal errors and client interruption/stream closure.
            config_path.unlink(missing_ok=True)
            if old_config is not None:
                config_path.write_bytes(old_config)
            if committed:
                shutil.rmtree(final_dir, ignore_errors=True)
            if backup_dir.exists():
                backup_dir.replace(final_dir)
            try:
                self.context.docker.restart_engine()
            except Exception:
                pass
            raise
        finally:
            shutil.rmtree(staging_dir, ignore_errors=True)
            if backup_dir.exists() and final_dir.exists():
                shutil.rmtree(backup_dir, ignore_errors=True)

    def uninstall_model(self, model: str) -> dict[str, Any]:
        profile = self._profile(model)
        manifest = self.read_manifest(model) or {}
        storage = str(manifest.get("storage_directory") or self._storage_key(model, profile))
        shutil.rmtree(self.context.models_root / storage, ignore_errors=True)
        self._config_path(model, profile).unlink(missing_ok=True)
        self.manifest_path(model).unlink(missing_ok=True)
        self._loaded_models.discard(model)
        self.context.docker.restart_engine()
        return {"model": model, "installed": False}

    def list_models(self) -> list[str]:
        result: list[str] = []
        for model in self.list_manifest_models():
            manifest = self.read_manifest(model) or {}
            weights = Path(str(manifest.get("weights_path") or ""))
            config = Path(str(manifest.get("config_path") or ""))
            if weights.exists() and config.exists():
                result.append(model)
        return sorted(result)

    def verify_model(self, model: str) -> dict[str, Any]:
        manifest = self.read_manifest(model)
        if not manifest or manifest.get("verified") is not True:
            return {"model": model, "verified": False, "reason": "verified manifest missing"}
        weights = Path(str(manifest.get("weights_path") or ""))
        config = Path(str(manifest.get("config_path") or ""))
        required = [weights / "model_index.json", weights / "unet" / "config.json", weights / "vae" / "config.json"]
        verified = all(path.is_file() for path in required) and config.exists() and self._backend_installed()
        return {
            "model": model,
            "verified": verified,
            "backend_name": manifest.get("backend_name"),
            "runtime_reference": manifest.get("backend_name"),
            "manifest": manifest,
        }

    def run_job(self, model: str, job: dict[str, Any], artifact_dir: Path) -> Iterator[dict[str, Any]]:
        if job.get("kind") != "image_generation":
            raise DriverError("Diffusers received an unsupported job", "JOB_UNSUPPORTED", kind=job.get("kind"))
        manifest = self.read_manifest(model) or {}
        profile = self._profile(model)
        backend_name = str(manifest.get("backend_name") or self._backend_name(model, profile))
        cold_start = model not in self._loaded_models
        warmup_ms = 0.0
        if cold_start:
            yield self.progress(f"Cold-loading and warming {model}", phase="start")
            _, warmup_ms = self._generate(backend_name, "plain gray square", 256, 256, 1, 1)
            self._loaded_models.add(model)
            yield self.progress(f"Model {model} is warm", phase="finish", metadata={"warmup_ms": round(warmup_ms, 3)})
        input_value = dict(job.get("input") or {})
        parameters = dict(job.get("parameters") or {})
        width = int(parameters.get("width", 768))
        height = int(parameters.get("height", 768))
        steps = int(parameters.get("steps", 24))
        count = int(parameters.get("count", 1))
        prompt = str(input_value.get("prompt", ""))
        yield self.progress(f"Generating {width}x{height} image with {model}", phase="start", completed=0, total=steps)
        body, inference_ms = self._generate(backend_name, prompt, width, height, steps, count)
        files: list[str] = []
        for index, item in enumerate(body.get("data") or [], start=1):
            encoded = item.get("b64_json")
            if encoded:
                path = artifact_dir / f"image_{index:02d}.png"
                path.write_bytes(base64.b64decode(encoded))
                files.append(path.name)
        if not files:
            raise DriverError("LocalAI returned no image artifact", "RUN_EXECUTION_ERROR", response=body)
        payload = {"model": backend_name, "prompt": prompt, "size": f"{width}x{height}", "n": count, "response_format": "b64_json", "steps": steps}
        result = {
            "request": payload,
            "response": {"data": [{"file": name} for name in files]},
            "usage_in": {"prompt_bytes": len(prompt.encode()), "images": 0},
            "usage_out": {"images": len(files), "width": width, "height": height},
            "performance": {
                "duration_ms": round(inference_ms, 3),
                "inference_ms": round(inference_ms, 3),
                "model_load_ms": None,
                "warmup_ms": round(warmup_ms, 3),
                "model_load_included_in_warmup": cold_start,
                "cold_start": cold_start,
                "output_per_second": round(len(files) / (inference_ms / 1000), 6) if inference_ms else None,
                "unit": "images/s",
            },
            "artifacts": files,
        }
        yield self.progress(f"Completed {job.get('id')}", phase="finish", completed=steps, total=steps)
        yield final_result(result)
