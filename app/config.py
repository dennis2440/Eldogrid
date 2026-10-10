"""Central config. Everyone imports from here; nobody calls os.getenv elsewhere."""
import os
from dotenv import load_dotenv

load_dotenv()


def _bool(v):
    return str(v).lower() == "true"


APP_ENV = os.getenv("APP_ENV", "development")
DEMO_MODE = _bool(os.getenv("DEMO_MODE", "true"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eldogrid.db")
DATABASE_PATH = DATABASE_URL.replace("sqlite:///", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
AT_API_KEY = os.getenv("AT_API_KEY", "")
AT_SENDER_ID = os.getenv("AT_SENDER_ID", "")

ROBOFLOW_API_URL = os.getenv("ROBOFLOW_API_URL", "https://serverless.roboflow.com")
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
ROBOFLOW_MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID", "")

OPEN_METEO_URL = os.getenv("OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast")
ELDORET_LAT = float(os.getenv("ELDORET_LAT", "0.5143"))
ELDORET_LON = float(os.getenv("ELDORET_LON", "35.2698"))

MOCK_MPESA_AUTO_CONFIRM_SECONDS = int(os.getenv("MOCK_MPESA_AUTO_CONFIRM_SECONDS", "5"))
ALERT_RAIN_THRESHOLD_MM = float(os.getenv("ALERT_RAIN_THRESHOLD_MM", "50"))
