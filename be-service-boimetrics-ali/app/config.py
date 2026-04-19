import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://2003scott:Argos12345654321@clusterdev.tptd9.mongodb.net/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "biometrics")
MONGODB_COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME", "face_subjects")
DEFAULT_THRESHOLD = 0.86
