from datetime import datetime
from . import db

class Image(db.Model):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(260), nullable=False, unique=True)  # relative filename e.g., 2025/11/17/20251117_153000.jpg
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    filepath = db.Column(db.String(1024), nullable=False)       # absolute or path used by server
    thumbnail_path = db.Column(db.String(1024), nullable=False)
    filesize = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    checksum = db.Column(db.String(64), nullable=True)          # optional SHA256
    note = db.Column(db.String(256), nullable=True)

    def to_dict(self, base_url=""):
        base = (base_url or "/api").rstrip("/")
        return {
            "id": self.id,
            "filename": self.filename,
            "timestamp": self.timestamp.isoformat(),
            "image_url": f"{base}/images/{self.filename}",
            "thumbnail_url": f"{base}/thumbnails/{self.filename}",
            "filesize": self.filesize,
            "width": self.width,
            "height": self.height,
            "note": self.note,
        }
