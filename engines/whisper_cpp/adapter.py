from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import time
import wave
from typing import Any, Iterator

import httpx

from controller.base import DriverError, EngineAdapter, final_result


class Adapter(EngineAdapter):
    id = "whisper_cpp"
    name = "whisper.cpp"
    version = "2.1.0"
    supported_job_kinds = ("audio_transcription",)

    def _binary(self) -> str:
        output = self.context.docker.exec(
            [
                "/bin/sh",
                "-lc",
                "command -v whisper-cli || find / -maxdepth 4 -type f -name whisper-cli -perm -111 2>/dev/null | head -n1",
            ]
        )
        return output.strip().splitlines()[-1] if output.strip() else ""

    def install_engine(self) -> Iterator[dict[str, Any]]:
        yield self.progress("Verifying whisper.cpp runtime", phase="start")
        binary = self._binary()
        if not binary:
            raise DriverError("whisper.cpp binary is unavailable", "ENGINE_VERIFICATION_ERROR")
        yield self.progress("whisper.cpp runtime verified", phase="finish", metadata={"binary": binary})

    def verify_engine(self) -> dict[str, Any]:
        binary = self._binary()
        return {
            "ok": bool(binary),
            "ready": bool(binary),
            "binary": binary,
            "execution_boundary": "controller-container",
        }

    def _profile_paths(self, model: str, profile: dict[str, Any]) -> tuple[Path, Path]:
        storage = profile.get("storage") or {}
        directory = str(storage.get("directory") or model).strip()
        filename = str(storage.get("filename") or f"ggml-{model}.bin").strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", directory):
            raise DriverError("Invalid whisper.cpp storage directory", "MODEL_MANIFEST_ERROR", model=model, directory=directory)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}", filename):
            raise DriverError("Invalid whisper.cpp model filename", "MODEL_MANIFEST_ERROR", model=model, filename=filename)
        root = self.context.models_root / directory
        return root, root / filename

    def _download(self, model: str, source: dict[str, Any], destination: Path) -> Iterator[dict[str, Any]]:
        url = str(source.get("url") or "").strip()
        if source.get("type") != "url" or not url.startswith(("https://", "http://")):
            raise DriverError("Whisper model profile requires an HTTP source URL", "MODEL_MANIFEST_ERROR", model=model)
        expected_sha = str(source.get("sha256") or "").lower().strip() or None
        if expected_sha and not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
            raise DriverError("Invalid whisper model SHA-256", "MODEL_MANIFEST_ERROR", model=model)
        expected_size = source.get("size_bytes")
        expected_size = int(expected_size) if isinstance(expected_size, int) and expected_size > 0 else None
        partial = destination.with_name(destination.name + ".part")
        destination.parent.mkdir(parents=True, exist_ok=True)
        last_error = ""
        for attempt in range(1, 4):
            offset = partial.stat().st_size if partial.exists() else 0
            headers = {"User-Agent": "teenmodo/0.4.0"}
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
                    total_header = response.headers.get("Content-Range") or response.headers.get("Content-Length")
                    total = expected_size
                    if total is None and total_header:
                        if "/" in total_header:
                            total = int(total_header.rsplit("/", 1)[1])
                        else:
                            total = offset + int(total_header)
                    mode = "ab" if offset and response.status_code == 206 else "wb"
                    if mode == "wb":
                        offset = 0
                    completed = offset
                    with partial.open(mode) as handle:
                        for chunk in response.iter_bytes(chunk_size=4 * 1024 * 1024):
                            if not chunk:
                                continue
                            handle.write(chunk)
                            completed += len(chunk)
                            yield self.progress(
                                f"Downloading whisper.cpp {model}",
                                completed=completed,
                                total=total,
                                metadata={"unit": "bytes", "file": destination.name},
                            )
                actual = partial.stat().st_size
                if expected_size and actual != expected_size:
                    raise OSError(f"size mismatch: expected {expected_size}, received {actual}")
                if expected_sha:
                    digest = hashlib.sha256()
                    with partial.open("rb") as handle:
                        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
                            digest.update(chunk)
                    if digest.hexdigest() != expected_sha:
                        raise OSError("SHA-256 mismatch")
                partial.replace(destination)
                return
            except Exception as exc:
                last_error = str(exc)
                if attempt < 3:
                    yield self.progress(
                        f"Retrying whisper.cpp {model} download ({attempt}/3)",
                        completed=partial.stat().st_size if partial.exists() else 0,
                        total=expected_size,
                        metadata={"unit": "bytes", "error": last_error},
                    )
                    time.sleep(attempt * 2)
        partial.unlink(missing_ok=True)
        raise DriverError("Whisper model download failed", "MODEL_INSTALL_ERROR", model=model, error=last_error)

    def install_model(self, model: str, source: str | None = None) -> Iterator[dict[str, Any]]:
        if source:
            raise DriverError("Direct model sources are not supported by this backend", "MODEL_SOURCE_UNSUPPORTED", engine=self.id, model=model, source=source)
        profile = self.model_profile(model)
        source = profile.get("source") or {}
        final_root, destination = self._profile_paths(model, profile)
        existing = self.verify_model(model)
        if existing.get("verified"):
            yield self.progress(f"whisper.cpp {model} is already installed and verified", phase="finish")
            return
        staging_root = self.context.models_root / ".staging"
        staging_root.mkdir(parents=True, exist_ok=True)
        for stale in staging_root.glob(f"{final_root.name}-*"):
            shutil.rmtree(stale, ignore_errors=True)
        staging = staging_root / f"{final_root.name}-{int(time.time_ns())}"
        staging_destination = staging / destination.name
        backup = self.context.models_root / ".backup" / f"{final_root.name}-{int(time.time_ns())}"
        committed = False
        try:
            yield self.progress(f"Downloading declared whisper.cpp model {model}", phase="start")
            yield from self._download(model, source, staging_destination)
            if not staging_destination.is_file() or staging_destination.stat().st_size == 0:
                raise DriverError("Whisper model file is empty", "MODEL_VERIFICATION_ERROR", model=model)
            backup.parent.mkdir(parents=True, exist_ok=True)
            if final_root.exists():
                final_root.replace(backup)
            staging.replace(final_root)
            committed = True
            destination = final_root / destination.name
            smoke_audio = self.context.state_root / "install-smoke.wav"
            with wave.open(str(smoke_audio), "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(16000)
                handle.writeframes(b"\x00\x00" * 16000)
            binary = self._binary()
            yield self.progress(f"Loading whisper.cpp {model} for installation verification")
            smoke_started = time.monotonic()
            try:
                self.context.docker.exec(
                    [binary, "-m", str(destination), "-f", str(smoke_audio), "-nt", "-np"],
                    timeout=self.context.readiness_timeout,
                )
            except DriverError as exc:
                raise DriverError(
                    "whisper.cpp downloaded the model but could not load it",
                    "MODEL_VERIFICATION_ERROR",
                    model=model,
                    error=str(exc),
                ) from exc
            finally:
                smoke_audio.unlink(missing_ok=True)
            smoke_ms = (time.monotonic() - smoke_started) * 1000
            self.write_manifest(
                model,
                {
                    "verified": True,
                    "weights_path": str(destination),
                    "runtime_reference": str(destination),
                    "profile_id": model,
                    "bytes": destination.stat().st_size,
                    "install_model_load_and_smoke_ms": round(smoke_ms, 3),
                },
            )
            shutil.rmtree(backup, ignore_errors=True)
            yield self.progress(
                f"Installed, loaded, and verified whisper.cpp {model}",
                phase="finish",
                metadata={"model_load_and_smoke_ms": round(smoke_ms, 3), "installed_bytes": destination.stat().st_size},
            )
        except BaseException:
            if committed:
                shutil.rmtree(final_root, ignore_errors=True)
            if backup.exists():
                backup.replace(final_root)
            raise
        finally:
            shutil.rmtree(staging, ignore_errors=True)
            if backup.exists() and final_root.exists():
                shutil.rmtree(backup, ignore_errors=True)

    def uninstall_model(self, model: str) -> dict[str, Any]:
        profile = self.model_profile(model)
        root, _ = self._profile_paths(model, profile)
        shutil.rmtree(root, ignore_errors=True)
        self.manifest_path(model).unlink(missing_ok=True)
        return {"model": model, "installed": False}

    def list_models(self) -> list[str]:
        result: list[str] = []
        for model in self.list_manifest_models():
            manifest = self.read_manifest(model) or {}
            path = Path(str(manifest.get("weights_path") or ""))
            if path.exists() and path.stat().st_size > 0:
                result.append(model)
        return sorted(result)

    def verify_model(self, model: str) -> dict[str, Any]:
        manifest = self.read_manifest(model)
        if not manifest or manifest.get("verified") is not True:
            return {"model": model, "verified": False, "reason": "verified manifest missing"}
        path = Path(str(manifest.get("weights_path") or ""))
        verified = path.exists() and path.stat().st_size > 0
        return {
            "model": model,
            "verified": verified,
            "runtime_reference": str(path),
            "weights_path": str(path),
            "manifest": manifest,
        }

    def run_job(self, model: str, job: dict[str, Any], artifact_dir: Path) -> Iterator[dict[str, Any]]:
        if job.get("kind") != "audio_transcription":
            raise DriverError("whisper.cpp received an unsupported job", "JOB_UNSUPPORTED", kind=job.get("kind"))
        relative = str((job.get("input") or {}).get("file", ""))
        source = (self.context.input_root / relative).resolve()
        if self.context.input_root.resolve() not in source.parents or not source.exists():
            raise DriverError("Audio input does not exist", "RUN_EXECUTION_ERROR", path=str(source))
        manifest = self.read_manifest(model) or {}
        weights = Path(str(manifest.get("weights_path") or ""))
        output_base = artifact_dir / "transcript"
        binary = self._binary()
        command = [
            binary,
            "-m",
            str(weights),
            "-f",
            f"/input/{source.relative_to(self.context.input_root).as_posix()}",
            "-ojf",
            "-of",
            f"/output/{output_base.relative_to(self.context.output_root).as_posix()}",
        ]
        yield self.progress(f"Transcribing with {model}", phase="start")
        started = time.monotonic()
        output = self.context.docker.exec(command)
        inference_ms = (time.monotonic() - started) * 1000
        result_path = output_base.with_suffix(".json")
        if not result_path.exists():
            raise DriverError("whisper.cpp did not produce JSON output", "RUN_EXECUTION_ERROR", output=output[-2000:])
        response = json.loads(result_path.read_text(encoding="utf-8"))
        result = {
            "request": {"model": model, "input": relative},
            "response": response,
            "usage_in": {"audio_bytes": source.stat().st_size},
            "usage_out": {"transcript_bytes": result_path.stat().st_size},
            "performance": {
                "duration_ms": round(inference_ms, 3),
                "inference_ms": round(inference_ms, 3),
                "model_load_ms": None,
                "warmup_ms": 0.0,
                "model_load_included_in_inference": True,
                "cold_start": False,
                "output_per_second": None,
                "unit": "audio",
            },
            "artifacts": [result_path.name],
        }
        yield self.progress(f"Completed {job.get('id')}", phase="finish")
        yield final_result(result)
