#!/usr/bin/env python3
import os
import shlex
import subprocess
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from . import db
from .config import Config
from .models import Image as ImageModel
from .utils import (
    ensure_dirs,
    make_timestamped_path,
    generate_thumbnail,
    file_checksum,
    prune_old_images,
)

# Graceful shutdown flag
_RUNNING = True

def _handle_sigterm(signum, frame):
    global _RUNNING
    _RUNNING = False

signal.signal(signal.SIGINT, _handle_sigterm)
signal.signal(signal.SIGTERM, _handle_sigterm)

def _run_fswebcam(outfile: Path, resolution: str):
    cmd = Config.FSWEBCAM_CMD.format(resolution=resolution, outfile=shlex.quote(str(outfile)))
    # split safely for subprocess
    args = shlex.split(cmd)
    subprocess.run(args, check=True)

def _insert_db_record(session, rel_path: str, full_path: Path, thumb_rel: str, thumb_full: Path):
    filesize = full_path.stat().st_size
    checksum = file_checksum(full_path)
    # optional: compute width/height
    try:
        from PIL import Image as PILImage
        with PILImage.open(full_path) as im:
            width, height = im.size
    except Exception:
        width = height = None

    img = ImageModel(
        filename=rel_path,
        timestamp=datetime.now(Config.LOCAL_TIMEZONE),
        filepath=str(full_path),
        thumbnail_path=str(thumb_full),
        filesize=filesize,
        width=width,
        height=height,
        checksum=checksum,
    )
    session.add(img)
    session.commit()
    return img

def capture_single(session=None):
    """Capture a single image and persist metadata."""
    ensure_dirs()
    ts = datetime.now(Config.LOCAL_TIMEZONE)
    rel, full_path = make_timestamped_path(Config.IMAGES_DIR, ts)
    thumb_rel, thumb_full = make_timestamped_path(Config.THUMBS_DIR, ts)
    resolution = Config.IMAGE_RESOLUTION
    jpeg_quality = Config.JPEG_QUALITY

    _run_fswebcam(full_path, resolution)
    generate_thumbnail(full_path, thumb_full, size=(320, 180), quality=int(int(jpeg_quality) * 0.9))

    session = session or db.session
    return _insert_db_record(session, rel, full_path, thumb_rel, thumb_full)

def capture_loop(interval_seconds: int = None):
    ensure_dirs()
    interval = interval_seconds or Config.CAPTURE_INTERVAL_SECONDS
    images_dir = Config.IMAGES_DIR
    thumbs_dir = Config.THUMBS_DIR

    # Bind to app context for DB access
    from flask import current_app
    app = current_app._get_current_object()

    # Run until stopped
    while _RUNNING:
        try:
            with app.app_context():
                capture_single()

            # Prune if needed (run pruning occasionally, e.g., every 10 captures)
            capture_loop._counter = getattr(capture_loop, "_counter", 0) + 1
            if capture_loop._counter % 10 == 0:
                prune_old_images(images_dir, thumbs_dir, keep_days=Config.RETENTION_DAYS, max_bytes=Config.MAX_STORAGE_BYTES)

        except subprocess.CalledProcessError as e:
            # log and continue
            print(f"fswebcam failed: {e}", file=sys.stderr)
        except Exception as e:
            print(f"capture error: {e}", file=sys.stderr)

        # Sleep with interruption support
        sleep_left = interval
        while sleep_left > 0 and _RUNNING:
            time.sleep(min(1, sleep_left))
            sleep_left -= 1

def main():
    # Entrypoint for running as module: python -m app.capture
    from . import create_app
    app = create_app()
    with app.app_context():
        capture_loop()

if __name__ == "__main__":
    main()
