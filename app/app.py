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
    def __init__(self, db_conn_url):
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
            self._initialize_server()  # NGROK tunnel outsourcing from Colab, to simulate debugging with teammates via Colab. :)
            self._setup_routes()
        except Exception as e:
            self.utils.logger.error(f"Error initializing the app: {str(e)}")

    def _initialize_database(self):
        self.db_handler.set_logger(self.utils.logger)
        self.db_handler.connect_to_firebase(self.db_uri)

    def _initialize_server(self):
        try:
            public_url = self._get_ngrok_tunnel()
            print(f'Public URL: {public_url}')
            os.environ["BASE_URL"] = public_url
        except Exception as e:
            self.utils.logger.warn(f"NGROK Tunnel error: {e}. Skipping ngrok setup.")
            os.environ["BASE_URL"] = f"http://127.0.0.1:{PORT}"

    def _setup_routes(self):
        @self.server.route('/')
        def index():
            self.dash_app.title = "ShapeFlow Monitor"
            return self.dash_app.index()

        @self.server.route("/dash/<path>")
        def index_per_route(path):
            self.dash_app.title = "Title: %s" % (path)
            return self.dash_app.index()

        @self.server.route('/static/<path:filename>')
        def static_files(filename):
            return send_from_directory(self.server.static_folder, filename)

    def _get_ngrok_tunnel(self):
        api_url = "http://localhost:4040/api/tunnels"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                tunnels = response.json().get("tunnels", [])
                if tunnels:
                    return tunnels[0]['public_url']
        except requests.exceptions.RequestException as e:
            self.utils.logger.warn(f"Ngrok tunnel not found")

        try:
            ngrok.set_auth_token(os.environ["NGROK_TOKEN"])
            return ngrok.connect(PORT).public_url
        except Exception as e:
            self.utils.logger.error(f"Failed to start ngrok tunnel: {e}")
            raise

    def run(self):
        debug = os.environ["RUNTIME_ENVIRONMENT"] in [RuntimeEnvironments.DEV.value, RuntimeEnvironments.TEST.value]
        self.utils.logger.info(f"=============== {PROJECT_NAME} is Running ===============")
        self.dash_app.run_server(debug=debug, use_reloader=False, port=PORT, dev_tools_props_check=False)
