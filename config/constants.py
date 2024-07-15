### Constants and Enums
import os
from datetime import datetime, date
from enum import Enum

PROJECT_NAME = "ShapeFlow Monitor"
PORT = 8050
FONT_AWESOME_CDN = "https://use.fontawesome.com/releases/v6.0.0/css/all.css"
DB_CONN_URL = "https://shapeflow-monitor-default-rtdb.europe-west1.firebasedatabase.app/"
ONSHAPE_LOGS_PATH = "/onShapeLogs"
UPLOADED_LOGS_PATH = "/uploaded-jsons"
START_DATE = date(2024, 4, 21).strftime('%d-%m-%Y')
END_DATE = datetime.now().strftime('%d-%m-%Y')
class RuntimeEnvironments(Enum):
  dev = "dev"
  prod = "prod"
  test = "test"

runtime_environment = os.environ["RUNTIME_ENVIRONMENT"] = RuntimeEnvironments.dev.value