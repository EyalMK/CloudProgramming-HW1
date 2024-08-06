import os
import dash
import dash_bootstrap_components as dbc
import requests

from flask import Flask, send_from_directory
from pyngrok import ngrok
from app.dash_layouts import DashPageLayouts
from config.constants import FONT_AWESOME_CDN, RuntimeEnvironments, PORT, PROJECT_NAME
from database.db_handler import DatabaseHandler
from utils.utilities import Utilities


class App:
    """
    A class to initialize and run a Dash web application with Flask server.

    Attributes:
        db_uri (str): The URI for connecting to the Firebase database.
        db_handler (DatabaseHandler): An instance for interacting with the database.
        utils (Utilities): An instance providing utility functions such as logging.
        server (Flask): The Flask server instance.
        dash_app (dash.Dash): The Dash application instance.
        dash_page_layouts (DashPageLayouts): An instance managing Dash page layouts.

    Methods:
        _initialize_database(): Sets up the database connection.
        _initialize_server(): Configures the server, including ngrok setup if required.
        _setup_routes(): Defines the server routes for serving the Dash app and static files.
        _get_ngrok_tunnel(): Retrieves or establishes a ngrok tunnel for public URL access.
        run(): Starts the Dash application server.
    """
    def __init__(self, db_conn_url):
        """
        Initializes the App with the provided database connection URL.

        Parameters:
            db_conn_url (str): The URL for connecting to the Firebase database.
        """
        try:
            self.db_uri = db_conn_url
            self.db_handler = DatabaseHandler()
            self.utils = Utilities(self.db_handler)
            self._initialize_database()
            self.server = Flask(__name__, static_folder="static")
            self.dash_app = dash.Dash(__name__, server=self.server,
                                      external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME_CDN])
            self.dash_app.config.suppress_callback_exceptions = True
            self.dash_page_layouts = DashPageLayouts(self.dash_app, self.db_handler, self.utils)
            # NGROK tunnel outsourcing from Colab.
            self._initialize_server()
            self._setup_routes()
        except Exception as e:
            self.utils.logger.error(f"Error initializing the app: {str(e)}")

    def _initialize_database(self):
        """
        Sets up the database connection by configuring the database handler.
        """
        self.db_handler.set_logger(self.utils.logger)
        self.db_handler.connect_to_firebase(self.db_uri)

    def _initialize_server(self):
        """
        Configures the server and sets up ngrok tunneling if required.

        Sets the environment variable `BASE_URL` to the public URL provided by ngrok or
        to a local URL if ngrok setup fails.
        """
        try:
            public_url = self._get_ngrok_tunnel()
            print(f'Public URL: {public_url}')
            os.environ["BASE_URL"] = public_url
        except Exception as e:
            self.utils.logger.warn(f"NGROK Tunnel error: {e}. Skipping ngrok setup.")
            os.environ["BASE_URL"] = f"http://127.0.0.1:{PORT}"

    def _setup_routes(self):
        """
        Defines the server routes for serving the Dash app and static files.

        Routes:
            - '/': Serves the main Dash app.
            - '/dash/<path>': Serves the Dash app with a dynamic title based on the path.
            - '/static/<path:filename>': Serves static files from the 'static' directory.
        """
        @self.server.route('/')
        def index():
            self.dash_app.title = {PROJECT_NAME}
            return self.dash_app.index()

        @self.server.route("/dash/<path>")
        def index_per_route(path):
            self.dash_app.title = "Title: %s" % path
            return self.dash_app.index()

        @self.server.route('/static/<path:filename>')
        def static_files(filename):
            return send_from_directory(self.server.static_folder, filename)

    def _get_ngrok_tunnel(self):
        """
        Retrieves or establishes a ngrok tunnel for public URL access.

        Returns:
            str: The public URL provided by ngrok.

        Raises:
            Exception: If ngrok tunnel setup fails.
        """
        api_url = "http://localhost:4040/api/tunnels"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                tunnels = response.json().get("tunnels", [])
                if tunnels:
                    return tunnels[0]['public_url']
        except requests.exceptions.RequestException:
            self.utils.logger.warn(f"Ngrok tunnel not found")

        try:
            ngrok.set_auth_token(os.environ["NGROK_TOKEN"])
            return ngrok.connect(PORT).public_url
        except Exception as e:
            self.utils.logger.error(f"Failed to start ngrok tunnel: {e}")
            raise

    def run(self):
        """
        Starts the Dash application server.

        The server runs in debug mode if the runtime environment is development or test.
        """
        debug_mode = (os.environ["RUNTIME_ENVIRONMENT"] in
                      [RuntimeEnvironments.DEV.value, RuntimeEnvironments.TEST.value])
        self.utils.logger.info(f"=============== {PROJECT_NAME} is Running ===============")
        self.dash_app.run_server(debug=debug_mode, use_reloader=debug_mode, port=PORT, dev_tools_props_check=False)
