"""Local file adapter: one durable journal writer and immutable data publications."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import tempfile
from abc import ABC, abstractmethod
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.parquet as pq

from .contracts import AssetClass, Bar, FeatureSnapshot, LedgerEvent, iso, parse_utc


class StorageError(RuntimeError):
    pass


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sync_dir(path: Path) -> None:
    if os.name == "nt":
        return
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_bytes(path: Path, content: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        _sync_dir(path.parent)
        return _hash(content)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _ohlcv(bar: Bar) -> tuple[float, float, float, float, float]:
    return bar.open, bar.high, bar.low, bar.close, bar.volume


def _fsync_path(path: str) -> None:
    # Windows rejects fsync on a read-only handle (EBADF), so open read-write.
    with open(path, "r+b") as stream:
        os.fsync(stream.fileno())


def _safe_name(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", value)
    if not safe or safe.startswith("."):
        raise ValueError("invalid path component")
    return safe


class StorageAdapter(ABC):
    @abstractmethod
    def append_event(self, event: LedgerEvent) -> str: ...

    @abstractmethod
    def read_events(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def save_bars(self, bars: Iterable[Bar], *, dataset: str = "bars") -> Path: ...

    @abstractmethod
    def load_bars(self, asset_id: str, asset_class: AssetClass, *, as_of: datetime | None = None,
                  all_revisions: bool = False, dataset: str = "bars") -> list[Bar]: ...

    @abstractmethod
    def save_features(self, snapshots: Iterable[FeatureSnapshot]) -> Path: ...

    @abstractmethod
    def load_features(self, asset_id: str, asset_class: AssetClass) -> list[FeatureSnapshot]: ...

    @abstractmethod
    def publish_json(self, name: str, document: dict[str, Any]) -> str: ...

    @abstractmethod
    def load_json(self, name: str) -> dict[str, Any]: ...

    @abstractmethod
    def export_csv(self, name: str, rows: list[dict[str, Any]]) -> Path: ...

    @abstractmethod
    def save_information(self, record_id: str, raw: dict[str, Any], feature: dict[str, Any]) -> Path: ...


class LocalStorage(StorageAdapter):
    """Only the lock holder may append. Open the reader with writer=False."""

    def __init__(self, home: Path, *, writer: bool = True, allow_inside_repo: bool = False):
        self.home = home.expanduser().resolve()
        repo_root = Path(__file__).resolve().parents[2]
        if not allow_inside_repo and (self.home == repo_root or repo_root in self.home.parents):
            raise StorageError("JARVIS_HOME must be outside the Git checkout")
        self.home.mkdir(parents=True, exist_ok=True)
        self.journal = self.home / "journal" / "operational.jsonl"
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        self._lock_file = None
        self._writer = writer
        if writer:
            self._acquire_lock()
        self._seq, self._prev_hash, self._event_ids, self._events = self._verify_and_recover()

    def _acquire_lock(self) -> None:
        lock_path = self.home / "journal" / "writer.lock"
        self._lock_file = open(lock_path, "a+b")
        try:
            if os.name == "nt":
                import msvcrt

                # Lock before any read: reading a byte another process has locked raises
                # PermissionError on Windows. Locking past the end of the file is permitted.
                self._lock_file.seek(0)
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self._lock_file.close()
            self._lock_file = None
            raise StorageError("another journal writer is active") from exc

    def close(self) -> None:
        if self._lock_file is not None:
            if os.name == "nt":
                import msvcrt

                self._lock_file.seek(0)
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
            self._lock_file.close()
            self._lock_file = None

    def __enter__(self) -> "LocalStorage":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _verify_and_recover(self) -> tuple[int, str, set[str], list[dict[str, Any]]]:
        if not self.journal.exists():
            return 0, "0" * 64, set(), []
        raw = self.journal.read_bytes()
        if raw and not raw.endswith(b"\n"):
            if not self._writer:
                raise StorageError("incomplete final journal line")
            cut = raw.rfind(b"\n") + 1
            quarantine = self.home / "quarantine" / f"tail-{_hash(raw[cut:])[:16]}.bin"
            atomic_bytes(quarantine, raw[cut:])
            with open(self.journal, "r+b") as stream:
                stream.truncate(cut)
                stream.flush()
                os.fsync(stream.fileno())
            raw = raw[:cut]
        seq, prev = 0, "0" * 64
        ids: set[str] = set()
        events: list[dict[str, Any]] = []
        for line in raw.splitlines():
            try:
                item = json.loads(line)
                digest = item.pop("hash")
                if item["seq"] != seq + 1 or item["prev_hash"] != prev:
                    raise ValueError("sequence/hash chain gap")
                if digest != _hash(prev.encode() + _canonical(item)):
                    raise ValueError("journal hash mismatch")
                if item["event"]["event_id"] in ids:
                    raise ValueError("duplicate event id")
                ids.add(item["event"]["event_id"])
            except (ValueError, KeyError, TypeError) as exc:
                raise StorageError("journal corruption; SAFE required") from exc
            seq, prev = item["seq"], digest
            events.append({**item, "hash": digest})
        return seq, prev, ids, events

    def _require_writer(self) -> None:
        if not self._writer or self._lock_file is None:
            raise StorageError("mutation requires single-writer lock")

    def append_event(self, event: LedgerEvent) -> str:
        self._require_writer()
        if event.event_id in self._event_ids:
            raise StorageError("duplicate event id")
        item = {"schema_version": 1, "seq": self._seq + 1, "prev_hash": self._prev_hash, "event": event.to_dict()}
        digest = _hash(self._prev_hash.encode() + _canonical(item))
        line = _canonical({**item, "hash": digest}) + b"\n"
        with open(self.journal, "ab") as stream:
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())
        self._seq += 1
        self._prev_hash = digest
        self._event_ids.add(event.event_id)
        self._events.append(json.loads(line))
        return event.event_id

    def read_events(self) -> list[dict[str, Any]]:
        """Verified journal records in order.

        The lock-holding writer serves an in-memory copy kept in step with every append, instead of re-parsing
        the whole file on each call; a reader re-verifies the file each time.
        """
        if self._writer:
            return list(self._events)
        return self._verify_and_recover()[3]

    def publish_json(self, name: str, document: dict[str, Any]) -> str:
        self._require_writer()
        content = _canonical({"schema_version": 1, **document}) + b"\n"
        return atomic_bytes(self.home / "config" / f"{_safe_name(name)}.json", content)

    def load_json(self, name: str) -> dict[str, Any]:
        return json.loads((self.home / "config" / f"{_safe_name(name)}.json").read_text())

    @staticmethod
    def _bar_row(bar: Bar) -> dict[str, Any]:
        row = vars(bar).copy()
        row["asset_class"] = bar.asset_class.value
        for key in ("start_at", "end_at", "available_at"):
            row[key] = iso(row[key])
        return row

    def save_bars(self, bars: Iterable[Bar], *, dataset: str = "bars") -> Path:
        """Merge bars into the asset partition.

        An identical re-delivery keeps the first observed availability time. A vendor amendment of an
        already-stored bar (for example late prints changing volume) is kept as a new revision with its own,
        later availability time, so earlier decisions stay reproducible and the desk does not halt.
        """
        self._require_writer()
        values = sorted(list(bars), key=lambda b: b.end_at)
        if not values:
            raise ValueError("no bars to save")
        first = values[0]
        if any(b.asset_id != first.asset_id or b.asset_class != first.asset_class for b in values):
            raise ValueError("partition may contain one asset only")
        path = self._bars_path(first.asset_id, first.asset_class, dataset)
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = self.load_bars(first.asset_id, first.asset_class, all_revisions=True,
                                  dataset=dataset) if path.exists() else []
        stored = {(b.end_at, b.source_id, b.revision): b for b in existing}
        latest: dict[tuple[datetime, str], Bar] = {}
        for bar in existing:
            key = (bar.end_at, bar.source_id)
            if key not in latest or bar.revision > latest[key].revision:
                latest[key] = bar
        for bar in values:
            key = (bar.end_at, bar.source_id)
            previous = latest.get(key)
            if previous is None:
                stored[(bar.end_at, bar.source_id, bar.revision)] = bar
                latest[key] = bar
            elif _ohlcv(previous) != _ohlcv(bar):
                revised = replace(bar, revision=previous.revision + 1,
                                  available_at=max(bar.available_at, previous.available_at))
                stored[(revised.end_at, revised.source_id, revised.revision)] = revised
                latest[key] = revised
        rows = [self._bar_row(b) for b in sorted(stored.values(), key=lambda b: (b.end_at, b.revision))]
        fd, tmp = tempfile.mkstemp(prefix=".bars.", suffix=".parquet", dir=path.parent)
        os.close(fd)
        try:
            pq.write_table(pa.Table.from_pylist(rows), tmp, compression="zstd")
            _fsync_path(tmp)
            os.replace(tmp, path)
            _sync_dir(path.parent)
            digest = _hash(path.read_bytes())
            atomic_bytes(path.with_suffix(".manifest.json"), _canonical({"schema_version": 1, "sha256": digest, "rows": len(rows)}) + b"\n")
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return path

    def _bars_path(self, asset_id: str, asset_class: AssetClass, dataset: str) -> Path:
        """One Parquet file per asset and dataset, e.g. ``bars`` (live hourly) or ``1Day-adjusted`` (history)."""
        return self.home / "market" / asset_class.value.lower() / _safe_name(asset_id) / f"{_safe_name(dataset)}.parquet"

    def load_bars(self, asset_id: str, asset_class: AssetClass, *, as_of: datetime | None = None,
                  all_revisions: bool = False, dataset: str = "bars") -> list[Bar]:
        """Latest revision of each bar (as known at ``as_of`` when given), or every stored revision."""
        path = self._bars_path(asset_id, asset_class, dataset)
        if not path.exists():
            return []
        manifest = json.loads(path.with_suffix(".manifest.json").read_text())
        if _hash(path.read_bytes()) != manifest["sha256"]:
            raise StorageError("Parquet hash mismatch")
        bars = []
        for row in pq.read_table(path).to_pylist():
            row["asset_class"] = AssetClass(row["asset_class"])
            for key in ("start_at", "end_at", "available_at"):
                row[key] = parse_utc(row[key])
            bars.append(Bar(**row))
        if all_revisions:
            return bars
        chosen: dict[tuple[datetime, str], Bar] = {}
        for bar in bars:
            if as_of is not None and bar.available_at > as_of:
                continue
            key = (bar.end_at, bar.source_id)
            if key not in chosen or bar.revision > chosen[key].revision:
                chosen[key] = bar
        return sorted(chosen.values(), key=lambda b: b.end_at)

    def export_csv(self, name: str, rows: list[dict[str, Any]]) -> Path:
        self._require_writer()
        path = self.home / "reports" / f"{_safe_name(name)}.csv"
        keys = sorted({key for row in rows for key in row})
        from io import StringIO

        out = StringIO()
        writer = csv.DictWriter(out, fieldnames=keys, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        digest = atomic_bytes(path, out.getvalue().encode("utf-8"))
        atomic_bytes(path.with_suffix(".manifest.json"), _canonical({"schema_version": 1, "sha256": digest, "rows": len(rows)}) + b"\n")
        return path

    def save_information(self, record_id: str, raw: dict[str, Any], feature: dict[str, Any]) -> Path:
        self._require_writer()
        identifier = _safe_name(record_id)
        raw_path = self.home / "information" / "raw" / f"{identifier}.json"
        feature_path = self.home / "information" / "features" / f"{identifier}.json"
        atomic_bytes(raw_path, _canonical(raw) + b"\n")
        atomic_bytes(feature_path, _canonical(feature) + b"\n")
        return feature_path

    def save_features(self, snapshots: Iterable[FeatureSnapshot]) -> Path:
        self._require_writer()
        values = list(snapshots)
        if not values:
            raise ValueError("no feature snapshots")
        first = values[0]
        if any(s.asset_id != first.asset_id or s.asset_class != first.asset_class for s in values):
            raise ValueError("feature partition may contain one asset only")
        path = self.home / "features" / first.asset_class.value.lower() / _safe_name(first.asset_id) / "snapshots.parquet"
        old = self.load_features(first.asset_id, first.asset_class) if path.exists() else []
        unique = {s.snapshot_id: s for s in old}
        unique.update({s.snapshot_id: s for s in values})
        rows = []
        for snapshot in sorted(unique.values(), key=lambda s: s.as_of):
            for name, value in sorted(snapshot.values.items()):
                rows.append({"snapshot_id": snapshot.snapshot_id, "asset_id": snapshot.asset_id,
                             "asset_class": snapshot.asset_class.value, "as_of": iso(snapshot.as_of),
                             "available_at": iso(snapshot.available_at), "expires_at": iso(snapshot.expires_at),
                             "source_ids": json.dumps(snapshot.source_ids), "feature_name": name,
                             "feature_value": value, "feature_version": snapshot.feature_version,
                             "quality": snapshot.quality})
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".features.", suffix=".parquet", dir=path.parent)
        os.close(fd)
        try:
            pq.write_table(pa.Table.from_pylist(rows), tmp, compression="zstd")
            _fsync_path(tmp)
            os.replace(tmp, path)
            _sync_dir(path.parent)
            atomic_bytes(path.with_suffix(".manifest.json"), _canonical({"schema_version": 1,
                          "sha256": _hash(path.read_bytes()), "rows": len(rows)}) + b"\n")
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return path

    def load_features(self, asset_id: str, asset_class: AssetClass) -> list[FeatureSnapshot]:
        path = self.home / "features" / asset_class.value.lower() / _safe_name(asset_id) / "snapshots.parquet"
        if not path.exists():
            return []
        manifest = json.loads(path.with_suffix(".manifest.json").read_text())
        if _hash(path.read_bytes()) != manifest["sha256"]:
            raise StorageError("feature Parquet hash mismatch")
        grouped: dict[str, dict[str, Any]] = {}
        for row in pq.read_table(path).to_pylist():
            key = row["snapshot_id"]
            if key not in grouped:
                grouped[key] = {"snapshot_id": key, "asset_id": row["asset_id"],
                                "asset_class": AssetClass(row["asset_class"]),
                                "as_of": parse_utc(row["as_of"]),
                                "available_at": parse_utc(row["available_at"]),
                                "expires_at": parse_utc(row["expires_at"]),
                                "source_ids": tuple(json.loads(row["source_ids"])),
                                "feature_version": row["feature_version"],
                                "quality": row["quality"], "values": {}}
            grouped[key]["values"][row["feature_name"]] = row["feature_value"]
        return sorted((FeatureSnapshot(**row) for row in grouped.values()), key=lambda s: s.as_of)

    def _table_path(self, *parts: str) -> Path:
        if not parts:
            raise ValueError("table path required")
        names = [_safe_name(p) for p in parts]
        return self.home.joinpath(*names[:-1]) / f"{names[-1]}.parquet"

    def write_table(self, *parts: str, rows: list[dict[str, Any]]) -> Path:
        """Atomically replace a generic Parquet table (with SHA-256 manifest) under JARVIS_HOME."""
        self._require_writer()
        if not rows:
            raise ValueError("refusing to write an empty table")
        path = self._table_path(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=f".{path.stem}.", suffix=".parquet", dir=path.parent)
        os.close(fd)
        try:
            pq.write_table(pa.Table.from_pylist(rows), tmp, compression="zstd")
            _fsync_path(tmp)
            os.replace(tmp, path)
            _sync_dir(path.parent)
            atomic_bytes(path.with_suffix(".manifest.json"), _canonical({"schema_version": 1,
                         "sha256": _hash(path.read_bytes()), "rows": len(rows)}) + b"\n")
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return path

    def read_table(self, *parts: str) -> list[dict[str, Any]]:
        path = self._table_path(*parts)
        if not path.exists():
            return []
        manifest = json.loads(path.with_suffix(".manifest.json").read_text())
        if _hash(path.read_bytes()) != manifest["sha256"]:
            raise StorageError(f"{'/'.join(parts)} Parquet hash mismatch")
        return pq.read_table(path).to_pylist()

    def backup(self, destination: Path) -> Path:
        self._require_writer()
        import shutil

        destination = destination.expanduser().resolve()
        if destination == self.home or self.home in destination.parents:
            raise StorageError("backup destination must be outside JARVIS_HOME")
        if destination.exists():
            raise StorageError("backup destination already exists")
        shutil.copytree(self.home, destination, ignore=shutil.ignore_patterns("writer.lock"))
        manifest = {str(p.relative_to(destination)): _hash(p.read_bytes()) for p in destination.rglob("*") if p.is_file()}
        atomic_bytes(destination / "backup-manifest.json", _canonical(manifest) + b"\n")
        return destination

    @staticmethod
    def verify_backup(destination: Path) -> bool:
        manifest = json.loads((destination / "backup-manifest.json").read_text())
        return all(_hash((destination / name).read_bytes()) == digest for name, digest in manifest.items())
