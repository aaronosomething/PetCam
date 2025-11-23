from flask import Blueprint, current_app, jsonify, request, url_for, send_from_directory, abort
from sqlalchemy import desc
from . import db
from .models import Image
from .config import Config
from .capture import capture_single
from pathlib import Path
from datetime import datetime
import subprocess

api_bp = Blueprint("api", __name__)

def _base_url():
    # Build absolute base (scheme + host) so image URLs work when frontend is on another origin.
    return request.host_url.rstrip("/") + "/api"

@api_bp.route("/latest", methods=["GET"])
def get_latest():
    img = Image.query.order_by(desc(Image.timestamp)).first()
    if not img:
        return jsonify({"message": "no_images"}), 404
    return jsonify(img.to_dict(base_url=_base_url()))

@api_bp.route("/list", methods=["GET"])
def list_images():
    # params: date=YYYY-MM-DD optional, page, per_page
    date_str = request.args.get("date")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    q = Image.query.order_by(desc(Image.timestamp))
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str)
            start = datetime(dt.year, dt.month, dt.day)
            end = datetime(dt.year, dt.month, dt.day, 23, 59, 59)
            q = q.filter(Image.timestamp >= start, Image.timestamp <= end)
        except Exception:
            return jsonify({"error": "invalid date format, use YYYY-MM-DD"}), 400

    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    items = [i.to_dict(base_url=_base_url()) for i in pagination.items]
    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": pagination.total,
        "items": items,
    })

@api_bp.route("/capture", methods=["POST"])
def capture_now():
    try:
        img = capture_single()
    except subprocess.CalledProcessError as exc:
        current_app.logger.exception("fswebcam failed during manual capture")
        return jsonify({"error": "capture_failed", "detail": str(exc)}), 500
    except Exception as exc:
        current_app.logger.exception("Unexpected capture failure")
        return jsonify({"error": "capture_failed", "detail": str(exc)}), 500
    return jsonify(img.to_dict(base_url=_base_url()))

@api_bp.route("/image/<int:image_id>", methods=["GET"])
def get_image_meta(image_id):
    img = Image.query.get(image_id)
    if not img:
        return jsonify({"error": "not_found"}), 404
    return jsonify(img.to_dict(base_url=_base_url()))

# These endpoints serve files for convenience; in production serve via nginx directly
@api_bp.route("/images/<path:filename>", methods=["GET"])
def serve_image(filename):
    images_root = Path(Config.IMAGES_DIR)
    target = images_root.joinpath(filename)
    if not target.exists():
        abort(404)
    # send_from_directory expects directory and filename separately
    return send_from_directory(str(images_root), filename, as_attachment=False)

@api_bp.route("/thumbnails/<path:filename>", methods=["GET"])
def serve_thumbnail(filename):
    thumbs_root = Path(Config.THUMBS_DIR)
    target = thumbs_root.joinpath(filename)
    if not target.exists():
        abort(404)
    return send_from_directory(str(thumbs_root), filename, as_attachment=False)

@api_bp.route("/settings", methods=["GET", "POST"])
def settings():
    # Simple read-only GET and token-protected POST to change runtime config if desired.
    if request.method == "GET":
        cfg = {
            "capture_interval_seconds": current_app.config.get("CAPTURE_INTERVAL_SECONDS", Config.CAPTURE_INTERVAL_SECONDS),
            "image_resolution": current_app.config.get("IMAGE_RESOLUTION", Config.IMAGE_RESOLUTION),
            "jpeg_quality": current_app.config.get("JPEG_QUALITY", Config.JPEG_QUALITY),
            "retention_days": current_app.config.get("RETENTION_DAYS", Config.RETENTION_DAYS),
            "max_storage_bytes": current_app.config.get("MAX_STORAGE_BYTES", Config.MAX_STORAGE_BYTES),
        }
        return jsonify(cfg)

    # POST => update settings (protected by simple token)
    token = request.headers.get("X-API-KEY") or request.args.get("api_key")
    expected = current_app.config.get("ADMIN_API_KEY") or None
    if not expected or token != expected:
        return jsonify({"error": "unauthorized"}), 401

    data = request.json or {}
    # Only allow certain keys to be updated
    allowed = {
        "capture_interval_seconds": "CAPTURE_INTERVAL_SECONDS",
        "image_resolution": "IMAGE_RESOLUTION",
        "jpeg_quality": "JPEG_QUALITY",
        "retention_days": "RETENTION_DAYS",
        "max_storage_bytes": "MAX_STORAGE_BYTES",
    }
    for k, cfg_key in allowed.items():
        if k in data:
            current_app.config[cfg_key] = data[k]
    return jsonify({"status": "ok"})
