# Constants and Enums
import os

from datetime import datetime, date
from enum import Enum

# General Constants
PROJECT_NAME = "ShapeFlow Monitor"
PORT = 8050
FONT_AWESOME_CDN = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css"

# Should be in a .env file
DB_CONN_URL = "https://shapeflow-monitor-final-default-rtdb.europe-west1.firebasedatabase.app/"

ONSHAPE_GLOSSARY_URL = "https://cad.onshape.com/help/Content/Glossary/glossary.htm?tocpath=_____19"
DEFAULT_MIN_DATE = date(2021, 4, 21).strftime('%d-%m-%Y')
DEFAULT_MAX_DATE = datetime.now().strftime('%d-%m-%Y')


# Enums
class RuntimeEnvironments(Enum):
    """
    Enum for runtime environments.

    Attributes:
        DEV: Development environment.
        PROD: Production environment.
        TEST: Testing environment.
    """
    DEV = "DEV"
    PROD = "PROD"
    TEST = "TEST"


class DatabaseCollections(Enum):
    """
    Enum for database collections.

    Attributes:
        ONSHAPE_LOGS: Collection path for Onshape logs.
        UPLOADED_LOGS: Collection path for uploaded logs.
        GLOSSARY_WORDS: Collection path for glossary words.
        INDICES_WORDS: Collection path for index words.
        BOT_PROMPTS: Collection path for chatbot patterns.
    """
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
    # Map actions to their respective categories
}


# Environment Configuration
def load_environment_config():
    """
    Loads and sets environment-specific configurations.

    This function sets environment variables for the application based on
    the runtime environment. It defaults to production if not specified.

    Returns:
        RuntimeEnvironments: The current runtime environment.
    """
    os.environ["NGROK_TOKEN"] = "2jBnTrvBD8DEzmYA1Bxx69uBXHH_84Fgk6CD5LHc9Cos4DdGh"

    os.environ["ALERT_TIMEWINDOW"] = "1h"  # 1 hour
    os.environ["UNDO_REDO_THRESHOLD"] = "15"
    os.environ["CONTEXT_SWITCH_TIMEWINDOW"] = "30"  # In minutes
    os.environ["CONTEXT_SWITCH_THRESHOLD"] = "10"
    os.environ["CANCELLATION_TIMEWINDOW"] = "0.2h"  # 12 minutes
    os.environ["CANCELLATION_THRESHOLD"] = "4"

    runtime_env = os.environ.get("RUNTIME_ENVIRONMENT", RuntimeEnvironments.PROD.value)
    os.environ["RUNTIME_ENVIRONMENT"] = runtime_env

    return RuntimeEnvironments(runtime_env)


runtime_environment = load_environment_config()
