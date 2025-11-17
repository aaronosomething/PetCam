from app import create_app
from app.config import Config
Config.ensure_dirs()
app = create_app()
