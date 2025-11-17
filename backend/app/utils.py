import os
import shutil
import hashlib
from pathlib import Path
from PIL import Image as PILImage
from datetime import datetime, timezone, timedelta
from .config import Config

def ensure_dirs():
    Config.ensure_dirs()

def make_timestamped_path(base_dir: Path, ts: datetime):
    # returns relative path like YYYY/MM/DD/HHMMSS.jpg and full path
    rel = Path(f"{ts.year:04d}") / f"{ts.month:02d}" / f"{ts.day:02d}" / f"{ts.strftime('%Y%m%d_%H%M%S')}.jpg"
    full = base_dir.joinpath(rel)
    full.parent.mkdir(parents=True, exist_ok=True)
    return str(rel).replace(os.sep, "/"), full

def generate_thumbnail(src_path: Path, dest_path: Path, size=(320, 180), quality=80):
    with PILImage.open(src_path) as im:
        im.thumbnail(size, PILImage.LANCZOS)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        im.save(dest_path, format="JPEG", quality=quality, optimize=True)

def file_checksum(path: Path, algo="sha256", chunk_size=8192):
    h = hashlib.new(algo)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

def prune_old_images(images_dir: Path, thumbs_dir: Path, keep_days: int = 7, max_bytes: int = None):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=keep_days)
    # Delete by timestamp (from filesystem mtime) first
    total_deleted = 0
    for root, dirs, files in os.walk(images_dir):
        for fname in files:
            fpath = Path(root) / fname
            try:
                mtime = datetime.fromtimestamp(fpath.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    rel = fpath.relative_to(images_dir)
                    thumb = thumbs_dir.joinpath(rel)
                    if fpath.exists():
                        fpath.unlink()
                        total_deleted += 1
                    if thumb.exists():
                        thumb.unlink()
            except Exception:
                continue

    # If max_bytes set, delete oldest until under limit
    if max_bytes is not None:
        def dir_size(p: Path):
            return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())

        while dir_size(images_dir) > max_bytes:
            # find oldest file
            files = [p for p in images_dir.rglob("*.jpg")]
            if not files:
                break
            oldest = min(files, key=lambda p: p.stat().st_mtime)
            rel = oldest.relative_to(images_dir)
            thumb = thumbs_dir.joinpath(rel)
            try:
                oldest.unlink()
                if thumb.exists():
                    thumb.unlink()
                total_deleted += 1
            except Exception:
                break

    return total_deleted
