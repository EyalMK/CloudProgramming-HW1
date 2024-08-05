### Main
import getpass
import os

from pyngrok import conf
from app.app import App
from config.constants import RuntimeEnvironments, DB_CONN_URL, runtime_environment

if __name__ == '__main__':
    if runtime_environment in [RuntimeEnvironments.DEV.value, RuntimeEnvironments.TEST.value]:
        conf.get_default().auth_token = os.environ["NGROK_TOKEN"]

    app_instance = App(DB_CONN_URL)
    app_instance.run()
