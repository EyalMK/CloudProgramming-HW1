### Main
import os
import getpass
from pyngrok import conf
from app.app import App
from config.constants import RuntimeEnvironments, DB_CONN_URL, runtime_environment

if __name__ == '__main__':
    # ================ ngrok auth token: 2jBnTrvBD8DEzmYA1Bxx69uBXHH_84Fgk6CD5LHc9Cos4DdGh ================ #
    if runtime_environment in [RuntimeEnvironments.dev.value, RuntimeEnvironments.test.value]:
        NGROK_TOKEN = '2jBnTrvBD8DEzmYA1Bxx69uBXHH_84Fgk6CD5LHc9Cos4DdGh'
        conf.get_default().auth_token = NGROK_TOKEN
    else:
        print("Enter ngrok auth token:")
        conf.get_default().auth_token = getpass.getpass()

    app_instance = App(DB_CONN_URL)
    app_instance.run()
