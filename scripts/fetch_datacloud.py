#!/usr/bin/env python3
"""Download IIS directory listings: resume, unzip archives, skip finished work."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

USER_AGENT = "GeoAICubes-fetch/0.2"
LINK_RE = re.compile(r'<A HREF="([^"]+)">([^<]*)</A>', re.IGNORECASE)
CHUNK_BYTES = 8 * 1024 * 1024
EXTRACT_MARKER = ".extracted"


class Phase(str, Enum):
    READY = "ready"
    DOWNLOAD_PARTIAL = "download_partial"
    DOWNLOAD_NEEDED = "download_needed"
    EXTRACT_NEEDED = "extract_needed"
    EXTRACT_PARTIAL = "extract_partial"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class RemoteEntry:
    url: str
    rel: Path
    size: int | None
    reachable: bool = True


def normalize_url(href: str, page_url: str) -> str:
    return urllib.parse.urljoin(page_url, href)


def is_parent_link(label: str) -> bool:
    return "parent directory" in label.lower()


def parse_iis_listing(html: str, page_url: str) -> tuple[list[str], list[str]]:
    dirs: list[str] = []
    files: list[str] = []
    for href, label in LINK_RE.findall(html):
        if is_parent_link(label):
            continue
        url = normalize_url(href, page_url)
        if href.endswith("/"):
            dirs.append(url)
        else:
            files.append(url)
    return dirs, files


def http_request(url: str, timeout: float, method: str = "GET", headers: dict[str, str] | None = None) -> urllib.request.Request:
    base = {"User-Agent": USER_AGENT}
    if headers:
        base.update(headers)
    return urllib.request.Request(url, headers=base, method=method)


def fetch_text(url: str, timeout: float) -> str:
    with urllib.request.urlopen(http_request(url, timeout), timeout=timeout) as resp:
        return resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="replace")


def remote_metadata(url: str, timeout: float) -> tuple[int | None, bool]:
    """Return (content-length if known, reachable via HEAD). 404/410 => not reachable."""
    try:
        with urllib.request.urlopen(http_request(url, timeout, method="HEAD"), timeout=timeout) as resp:
            length = resp.headers.get("Content-Length")
            size = int(length) if length else None
            return size, True
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 410):
            return None, False
        return None, True
    except urllib.error.URLError:
        return None, True


def crawl(base_url: str, timeout: float) -> list[RemoteEntry]:
    base_url = base_url if base_url.endswith("/") else f"{base_url}/"
    base_path = urllib.parse.urlparse(base_url).path.rstrip("/")
    found: list[tuple[str, Path]] = []
    stack = [base_url]

    while stack:
        page_url = stack.pop()
        html = fetch_text(page_url, timeout)
        dirs, files = parse_iis_listing(html, page_url)
        stack.extend(d for d in dirs if d not in stack)
        for file_url in files:
            file_path = urllib.parse.urlparse(file_url).path
            if not file_path.startswith(base_path):
                continue
            rel = file_path[len(base_path) :].lstrip("/")
            if rel:
                found.append((file_url, Path(rel)))

    found.sort(key=lambda x: x[1].as_posix())
    entries: list[RemoteEntry] = []
    for url, rel in found:
        size, reachable = remote_metadata(url, timeout)
        entries.append(RemoteEntry(url=url, rel=rel, size=size, reachable=reachable))
    return entries


def format_bytes(n: int) -> str:
    size = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{int(size)} B" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
    return f"{n} B"


def is_zip(rel: Path) -> bool:
    return rel.suffix.lower() == ".zip"


def extract_dir_for(out_dir: Path, rel: Path) -> Path:
    return out_dir / rel.with_suffix("")


def marker_path(extract_dir: Path) -> Path:
    return extract_dir / EXTRACT_MARKER


def read_marker(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_marker(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def local_file_complete(path: Path, expected: int | None) -> bool:
    if not path.is_file():
        return False
    if expected is None:
        return path.stat().st_size > 0
    return path.stat().st_size == expected


def extract_looks_complete(extract_dir: Path, zip_path: Path | None, expected_members: int | None) -> bool:
    marker = read_marker(marker_path(extract_dir))
    if marker is None:
        return False
    if not extract_dir.is_dir():
        return False
    if expected_members is not None and marker.get("member_count") != expected_members:
        return False
    if zip_path is not None:
        if marker.get("zip_size") != zip_path.stat().st_size:
            return False
    return any(extract_dir.iterdir())


def zip_member_count(zip_path: Path) -> int | None:
    try:
        with zipfile.ZipFile(zip_path) as zf:
            return len(zf.infolist())
    except (zipfile.BadZipFile, OSError):
        return None


def assess_entry(entry: RemoteEntry, out_dir: Path) -> tuple[Phase, Path]:
    dest = out_dir / entry.rel
    if is_zip(entry.rel):
        ext_dir = extract_dir_for(out_dir, entry.rel)
        member_count: int | None = None
        if dest.is_file():
            member_count = zip_member_count(dest)
        if extract_looks_complete(ext_dir, dest if dest.is_file() else None, member_count):
            return Phase.READY, dest
        if dest.is_file() and local_file_complete(dest, entry.size):
            if ext_dir.exists() and not extract_looks_complete(ext_dir, dest, member_count):
                return Phase.EXTRACT_PARTIAL if any(ext_dir.rglob("*")) else Phase.EXTRACT_NEEDED, dest
            return Phase.EXTRACT_NEEDED, dest
        if dest.is_file() and dest.stat().st_size > 0:
            return Phase.DOWNLOAD_PARTIAL, dest
        if ext_dir.exists() and any(ext_dir.rglob("*")):
            return Phase.EXTRACT_PARTIAL, dest
        if not entry.reachable:
            return Phase.UNAVAILABLE, dest
        return Phase.DOWNLOAD_NEEDED, dest
    if local_file_complete(dest, entry.size):
        return Phase.READY, dest
    if dest.is_file() and dest.stat().st_size > 0:
        return Phase.DOWNLOAD_PARTIAL, dest
    if not entry.reachable:
        return Phase.UNAVAILABLE, dest
    return Phase.DOWNLOAD_NEEDED, dest


def download_file(url: str, dest: Path, timeout: float, expected: int | None, resume: bool) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    existing = dest.stat().st_size if dest.exists() else 0

    if local_file_complete(dest, expected):
        print("  download: already complete")
        return

    headers: dict[str, str] = {}
    mode = "wb"
    start = 0
    if resume and existing > 0:
        if expected is not None and existing > expected:
            dest.unlink()
            existing = 0
        elif expected is not None and existing == expected:
            print("  download: already complete")
            return
        else:
            headers["Range"] = f"bytes={existing}-"
            mode = "ab"
            start = existing

    req = http_request(url, timeout, headers=headers)
    try:
        resp_ctx = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 410):
            raise FileNotFoundError(f"remote file missing ({exc.code})") from exc
        raise
    with resp_ctx as resp:
        if resume and start > 0 and resp.status not in (206, 200):
            dest.unlink(missing_ok=True)
            start = 0
            mode = "wb"
            resp = urllib.request.urlopen(http_request(url, timeout), timeout=timeout)

        total = expected
        content_range = resp.headers.get("Content-Range")
        if content_range and "/" in content_range:
            total = int(content_range.split("/")[-1])
        elif total is None:
            cl = resp.headers.get("Content-Length")
            total = (start + int(cl)) if cl else None

        downloaded = start
        last_print = 0.0
        with dest.open(mode) as handle:
            while True:
                chunk = resp.read(CHUNK_BYTES)
                if not chunk:
                    break
                handle.write(chunk)
                downloaded += len(chunk)
                now = time.monotonic()
                if now - last_print >= 1.0 or (total and downloaded >= total):
                    if total:
                        pct = 100.0 * downloaded / total
                        print(
                            f"\r  download {dest.name}: {format_bytes(downloaded)} / "
                            f"{format_bytes(total)} ({pct:.1f}%)",
                            end="",
                            flush=True,
                        )
                    else:
                        print(f"\r  download {dest.name}: {format_bytes(downloaded)}", end="", flush=True)
                    last_print = now
        print()


def extract_zip(zip_path: Path, extract_dir: Path) -> None:
    unpack_root = extract_dir.parent
    unpack_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        members = zf.infolist()
        total = sum(m.file_size for m in members) or 1
        done = 0
        last_print = 0.0
        for member in members:
            zf.extract(member, path=unpack_root)
            done += member.file_size
            now = time.monotonic()
            if now - last_print >= 1.0 or done >= total:
                pct = 100.0 * done / total
                print(
                    f"\r  extract {zip_path.name}: {format_bytes(done)} / "
                    f"{format_bytes(total)} ({pct:.1f}%)",
                    end="",
                    flush=True,
                )
                last_print = now
        print()
        write_marker(
            marker_path(extract_dir),
            {
                "zip_name": zip_path.name,
                "zip_size": zip_path.stat().st_size,
                "member_count": len(members),
            },
        )


def sync_entry(entry: RemoteEntry, out_dir: Path, timeout: float, resume: bool) -> None:
    phase, dest = assess_entry(entry, out_dir)

    if phase is Phase.UNAVAILABLE:
        print("  skip: remote file missing (404; stale directory listing)")
        return

    if phase is Phase.READY:
        if is_zip(entry.rel):
            zip_path = out_dir / entry.rel
            if zip_path.is_file():
                print("  cleanup: removing leftover archive")
                zip_path.unlink()
        print("  skip: already ready")
        return

    if is_zip(entry.rel):
        zip_path = out_dir / entry.rel
        ext_dir = extract_dir_for(out_dir, entry.rel)

        needs_download = phase in (Phase.DOWNLOAD_NEEDED, Phase.DOWNLOAD_PARTIAL) or (
            phase is Phase.EXTRACT_PARTIAL and not local_file_complete(zip_path, entry.size)
        )
        if needs_download:
            download_file(entry.url, zip_path, timeout, entry.size, resume)
        elif phase in (Phase.EXTRACT_NEEDED, Phase.EXTRACT_PARTIAL):
            print("  download: zip already on disk")

        if not local_file_complete(zip_path, entry.size):
            raise RuntimeError(f"incomplete archive: {zip_path}")

        print(f"  extract -> {ext_dir}")
        extract_zip(zip_path, ext_dir)
        zip_path.unlink()
        print("  removed archive")
        return

    if phase is Phase.DOWNLOAD_NEEDED or phase is Phase.DOWNLOAD_PARTIAL:
        download_file(entry.url, dest, timeout, entry.size, resume)


def cmd_list(entries: list[RemoteEntry], out_dir: Path) -> int:
    rows: list[tuple[str, str, str, str]] = []
    total_remote = 0
    for entry in entries:
        phase, _ = assess_entry(entry, out_dir)
        size = entry.size or 0
        total_remote += size
        rows.append(
            (
                entry.rel.as_posix(),
                format_bytes(size) if entry.size else "?",
                phase.value,
                "zip" if is_zip(entry.rel) else "file",
            )
        )

    name_w = max(len(r[0]) for r in rows)
    print(f"Destination: {out_dir.resolve()}")
    print(f"Items: {len(rows)}  Remote total: {format_bytes(total_remote)}\n")
    print(f"{'PATH'.ljust(name_w)}  {'SIZE'.rjust(12)}  {'KIND'.ljust(6)}  STATUS")
    print(f"{'-' * name_w}  {'-' * 12}  {'-' * 6}  {'-' * 15}")
    for path, size, status, kind in rows:
        print(f"{path.ljust(name_w)}  {size.rjust(12)}  {kind.ljust(6)}  {status}")
    return 0


def cmd_sync(entries: list[RemoteEntry], out_dir: Path, timeout: float, resume: bool) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    for index, entry in enumerate(entries, start=1):
        phase, _ = assess_entry(entry, out_dir)
        print(f"[{index}/{len(entries)}] {entry.rel} ({phase.value})")
        try:
            sync_entry(entry, out_dir, timeout, resume)
        except (urllib.error.URLError, OSError, zipfile.BadZipFile, RuntimeError, FileNotFoundError) as exc:
            print(f"  failed: {exc}", file=sys.stderr)
            failures.append(entry.rel.as_posix())
    print(f"Done. Data under {out_dir.resolve()}")
    if failures:
        print(f"{len(failures)} item(s) failed:", ", ".join(failures), file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("list", "Show remote files and local status (no downloads)"),
        ("sync", "Download and extract; resume if interrupted"),
    ):
        child = sub.add_parser(name, help=help_text)
        child.add_argument("url", help="Root URL of an IIS directory listing")
        child.add_argument(
            "--dest",
            type=Path,
            default=Path("data"),
            help="Local folder for mirrored files (default: ./data)",
        )
        child.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout (seconds)")
        if name == "sync":
            child.add_argument("--no-resume", action="store_true", help="Restart partial downloads from scratch")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        entries = crawl(args.url, args.timeout)
    except urllib.error.URLError as exc:
        print(f"Failed to list {args.url}: {exc}", file=sys.stderr)
        return 1

    if not entries:
        print("No files found.", file=sys.stderr)
        return 1

    if args.command == "list":
        return cmd_list(entries, args.dest)
    return cmd_sync(entries, args.dest, args.timeout, resume=not args.no_resume)


if __name__ == "__main__":
    raise SystemExit(main())