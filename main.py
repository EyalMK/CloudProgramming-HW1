# Main
import os

from pyngrok import conf
from app.app import App
from config.constants import RuntimeEnvironments, DB_CONN_URL, runtime_environment


def setup_ngrok_auth():
    """
    Configures Ngrok authentication if the runtime environment is PROD or TEST.

    This function sets the Ngrok authentication token based on the environment variable
    if the application is running in a development or testing environment.
    """
    if runtime_environment in [RuntimeEnvironments.PROD.value, RuntimeEnvironments.TEST.value]:
        conf.get_default().auth_token = os.environ.get("NGROK_TOKEN")


def main():
    """
    Main entry point for the application.

    This function sets up Ngrok authentication if necessary, creates an instance of the
    App class with the database connection URL, and starts the application.
    """
    setup_ngrok_auth()

    # Create an instance of the App class with the database connection URL
    app_instance = App(DB_CONN_URL)

    # Run the application
    app_instance.run()


if __name__ == '__main__':
    main()
