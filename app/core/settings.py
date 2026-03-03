import os
from pathlib import Path

SESSION_SECRET = os.getenv("OHMYGREEN_SESSION_SECRET", "dev-secret-change-in-production")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
