import os
import requests
from app.dash_layouts import DashPageLayouts
from config.constants import FONT_AWESOME_CDN, RuntimeEnvironments, PORT
from database.db_handler import DatabaseHandler
from utils.utilities import Utilities
import dash
import dash_bootstrap_components as dbc
from flask import Flask, send_from_directory
from pyngrok import ngrok

class App:
    def __init__(self, db_conn_url):
        try:
            self.db_uri = db_conn_url
            self.db_handler = DatabaseHandler()
            self.utils = Utilities(self.db_handler)
            self._initialize_database()
            self.server = Flask(__name__, static_folder="static")
            self.dash_app = dash.Dash(__name__, server=self.server, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME_CDN])
            self.dash_app.config.suppress_callback_exceptions = True
            self.dash_page_layouts = DashPageLayouts(self.dash_app, self.db_handler, self.utils)
            # self._initialize_server() # NGROK tunnel outsourcing from Colab, to simulate debugging with teammates via Colab. :)
            self._setup_routes()
        except Exception as e:
            self.utils.logger.error(f"Error initializing the app: {str(e)}")

    def _initialize_database(self):
        self.db_handler.set_logger(self.utils.logger)
        self.db_handler.connect_to_firebase(self.db_uri)

    def _initialize_server(self):
        public_url = self._get_ngrok_tunnel()
        print(f'Public URL: {public_url}')
        os.environ["BASE_URL"] = public_url

    def _setup_routes(self):
        @self.server.route('/')
        def index():
            return self.dash_app.index()

        @self.server.route('/static/<path:path>')
        def serve_static(path):
            return send_from_directory('static', path)

    def _get_ngrok_tunnel(self):
        api_url = "http://localhost:4040/api/tunnels"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                tunnels = response.json().get("tunnels", [])
                if tunnels:
                    return tunnels[0]['public_url']
        except requests.exceptions.RequestException:
            pass
        return ngrok.connect(PORT).public_url

    def run(self):
        debug = os.environ["RUNTIME_ENVIRONMENT"] in [RuntimeEnvironments.dev.value, RuntimeEnvironments.test.value]
        self.utils.logger.info("=============== ShapeFlow Monitor is Running ===============")
        self.dash_app.run_server(debug=debug, use_reloader=False, port=PORT)
