# Constants and Enums
import os

from datetime import datetime, date
from enum import Enum

# General Constants
PROJECT_NAME = "ShapeFlow Monitor"
PORT = 8050
FONT_AWESOME_CDN = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css"
DB_CONN_URL = "https://shapeflow-monitor-final-default-rtdb.europe-west1.firebasedatabase.app/"
ONSHAPE_GLOSSARY_URL = "https://cad.onshape.com/help/Content/Glossary/glossary.htm?tocpath=_____19"
DEFAULT_MIN_DATE = date(2022, 4, 21).strftime('%d-%m-%Y')
DEFAULT_MAX_DATE = datetime.now().strftime('%d-%m-%Y')


# Enums
class RuntimeEnvironments(Enum):
    DEV = "DEV"
    PROD = "PROD"
    TEST = "TEST"


class DatabaseCollections(Enum):
    ONSHAPE_LOGS = "/onShapeLogs"
    UPLOADED_LOGS = "/uploaded-jsons"
    GLOSSARY_WORDS = "/base-glossary-words"
    INDICES_WORDS = "/indices-words"
    BOT_PROMPTS = "/chatbot-patterns"


# Action Map
ACTION_MAP = {
    'undo': 'Undo',
    'redo': 'Redo',
    'insert': 'Insert',
    'export': 'Export',
    'edit': 'Edit',
    'commit': 'Commit',
    'add': 'Add',
    'close': 'Close',
    'move': 'Move',
    'open': 'Open'
}


# Todo: refactor and import from .env.development/.env.testing
# Environment Configuration
def load_environment_config():
    """
    Loads and sets environment-specific configurations.
    """
    os.environ["NGROK_TOKEN"] = "2jBnTrvBD8DEzmYA1Bxx69uBXHH_84Fgk6CD5LHc9Cos4DdGh"
    os.environ["ALERT_TIMEWINDOW"] = "1h"
    os.environ["UNDO_REDO_THRESHOLD"] = "15"

    runtime_env = os.environ.get("RUNTIME_ENVIRONMENT", RuntimeEnvironments.DEV.value)
    os.environ["RUNTIME_ENVIRONMENT"] = runtime_env

    return RuntimeEnvironments(runtime_env)


runtime_environment = load_environment_config()
