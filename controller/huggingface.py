from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
import hashlib
from pathlib import Path, PurePosixPath
import re
import time
from typing import Any, Iterator

import httpx


class HuggingFaceError(RuntimeError):
    def __init__(self, message: str, *, manifest: bool = False, **context: Any) -> None:
        super().__init__(message)
        self.message = message
        self.manifest = manifest
        self.context = context


@dataclass(frozen=True)
class HuggingFaceFile:
    remote: str
    target: str
    size: int
    sha256: str | None = None


@dataclass(frozen=True)
class HuggingFacePlan:
    repository: str
    revision: str
    files: tuple[HuggingFaceFile, ...]

    @property
    def total_bytes(self) -> int:
        return sum(item.size for item in self.files)


@dataclass(frozen=True)
class DownloadProgress:
    message: str
    completed: int
    total: int
    file: str
    file_index: int
    file_count: int
    error: str | None = None


def _safe_relative_path(value: str, *, field: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise HuggingFaceError("Model profile contains an unsafe path", manifest=True, field=field, value=value)
    return path.as_posix()


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatchcase(path, pattern) or PurePosixPath(path).match(pattern) for pattern in patterns)


def _remote_size(sibling: Any) -> int:
    value = getattr(sibling, "size", None)
    if isinstance(value, int) and value >= 0:
        return value
    lfs = getattr(sibling, "lfs", None)
    value = lfs.get("size") if isinstance(lfs, dict) else getattr(lfs, "size", None)
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


def resolve_plan(source: dict[str, Any], *, model: str, token: str | None) -> HuggingFacePlan:
    if source.get("type") != "huggingface_snapshot":
        raise HuggingFaceError(
            "Unsupported Hugging Face source type",
            manifest=True,
            model=model,
            source_type=source.get("type"),
        )
    repository = str(source.get("repository") or "").strip()
    revision = str(source.get("revision") or "main").strip()
    if not repository:
        raise HuggingFaceError("Model repository is missing", manifest=True, model=model)
    try:
        from huggingface_hub import HfApi

        info = HfApi(token=token).model_info(repository, revision=revision, files_metadata=True)
    except Exception as exc:
        raise HuggingFaceError(
            "Could not read Hugging Face model file metadata",
            model=model,
            repository=repository,
            revision=revision,
            error=str(exc),
        ) from exc
    siblings = {str(item.rfilename): item for item in (info.siblings or [])}
    download = source.get("download") or {}
    selected: list[HuggingFaceFile] = []
    exact = download.get("files") or []
    if exact:
        for entry in exact:
            if isinstance(entry, str):
                remote = target = entry
            elif isinstance(entry, dict):
                remote = str(entry.get("remote") or "")
                target = str(entry.get("target") or remote)
            else:
                raise HuggingFaceError(
                    "Invalid file entry in model profile",
                    manifest=True,
                    model=model,
                    entry=repr(entry),
                )
            remote = _safe_relative_path(remote, field="remote")
            target = _safe_relative_path(target, field="target")
            sibling = siblings.get(remote)
            if sibling is None:
                raise HuggingFaceError(
                    "Required model file is absent from the Hugging Face repository",
                    model=model,
                    repository=repository,
                    file=remote,
                )
            selected.append(HuggingFaceFile(remote, target, _remote_size(sibling), _remote_sha256(sibling)))
    else:
        include = [str(value) for value in download.get("include") or []]
        exclude = [str(value) for value in download.get("exclude") or []]
        required = [str(value) for value in download.get("required") or []]
        if not include:
            raise HuggingFaceError(
                "Model profile must declare exact files or include patterns",
                manifest=True,
                model=model,
            )
        paths = [path for path in sorted(siblings) if _matches(path, include) and not _matches(path, exclude)]
        missing = [pattern for pattern in required if not any(_matches(path, [pattern]) for path in paths)]
        if missing:
            raise HuggingFaceError(
                "Required model file patterns did not match repository files",
                model=model,
                repository=repository,
                missing=missing,
            )
        for path in paths:
            sibling = siblings[path]
            selected.append(HuggingFaceFile(path, _safe_relative_path(path, field="target"), _remote_size(sibling), _remote_sha256(sibling)))
    if not selected:
        raise HuggingFaceError("Model profile selected no downloadable files", model=model)
    targets = [item.target for item in selected]
    if len(targets) != len(set(targets)):
        raise HuggingFaceError("Model profile maps multiple files to one target", manifest=True, model=model)
    total = sum(item.size for item in selected)
    if total <= 0:
        raise HuggingFaceError(
            "Hugging Face did not provide file sizes; refusing an unmeasurable model installation",
            model=model,
            repository=repository,
        )
    max_total = download.get("max_total_bytes")
    if isinstance(max_total, int) and max_total > 0 and total > max_total:
        raise HuggingFaceError(
            "Selected model files exceed the profile disk limit",
            model=model,
            selected_bytes=total,
            max_total_bytes=max_total,
        )
    return HuggingFacePlan(repository, revision, tuple(selected))


def stream_file(
    plan: HuggingFacePlan,
    item: HuggingFaceFile,
    *,
    destination: Path,
    token: str | None,
    completed_before: int,
    index: int,
) -> Iterator[DownloadProgress]:
    try:
        from huggingface_hub import hf_hub_url
    except Exception as exc:
        raise HuggingFaceError("huggingface-hub is unavailable", error=str(exc)) from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    url = hf_hub_url(plan.repository, item.remote, revision=plan.revision)
    last_error = ""
    for attempt in range(1, 4):
        offset = partial.stat().st_size if partial.exists() else 0
        if item.size and offset > item.size:
            partial.unlink(missing_ok=True)
            offset = 0
        if item.size and offset == item.size:
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
                with partial.open(mode) as handle:
                    for chunk in response.iter_bytes(chunk_size=8 * 1024 * 1024):
                        if not chunk:
                            continue
                        handle.write(chunk)
                        current += len(chunk)
                        yield DownloadProgress(
                            f"Downloading {index}/{len(plan.files)}: {item.remote}",
                            completed_before + current,
                            plan.total_bytes,
                            item.remote,
                            index,
                            len(plan.files),
                        )
            actual = partial.stat().st_size
            if item.size and actual != item.size:
                raise OSError(f"size mismatch: expected {item.size}, received {actual}")
            if item.sha256:
                digest = hashlib.sha256()
                with partial.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
                        digest.update(chunk)
                if digest.hexdigest() != item.sha256:
                    raise OSError("SHA-256 mismatch")
            partial.replace(destination)
            return
        except Exception as exc:
            last_error = str(exc)
            if attempt < 3:
                current = partial.stat().st_size if partial.exists() else 0
                yield DownloadProgress(
                    f"Retrying {item.remote} after download error ({attempt}/3)",
                    completed_before + current,
                    plan.total_bytes,
                    item.remote,
                    index,
                    len(plan.files),
                    last_error,
                )
                time.sleep(attempt * 2)
    raise HuggingFaceError(
        "Model file download failed",
        repository=plan.repository,
        file=item.remote,
        error=last_error,
    )


def stream_plan(
    plan: HuggingFacePlan,
    *,
    destination: Path,
    token: str | None,
) -> Iterator[DownloadProgress]:
    completed = 0
    for index, item in enumerate(plan.files, start=1):
        target = destination / item.target
        yield from stream_file(
            plan,
            item,
            destination=target,
            token=token,
            completed_before=completed,
            index=index,
        )
        completed += target.stat().st_size
