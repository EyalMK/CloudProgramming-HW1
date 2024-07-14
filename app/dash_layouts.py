from datetime import datetime

from app.dash_callbacks import DashCallbacks
from dataframes.dataframe_handler import DataFrameHandler
from config.constants import START_DATE, END_DATE, PROJECT_NAME
import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px


class DashPageLayouts:
    def __init__(self, dash_app: dash.Dash, db_handler: 'DatabaseHandler', utils):
        self.dash_app = dash_app
        self.db_handler = db_handler
        self.df_handler = DataFrameHandler(db_handler)
        self.uploaded_json = None
        self.utils = utils
        self.define_layout()
        self.create_callbacks()
        self.utils.logger.info("Dash app pages loaded, and dataframes processed.")

    def create_callbacks(self):
        DashCallbacks(self.dash_app, self.df_handler, self.db_handler, self, self.utils)

    # Define individual page layouts with graphs and filters
    def dashboard_layout(self):
        return self._create_layout("Dashboard", [
            self._create_card("Activity Over Time", dcc.Graph(figure=self._create_line_chart(self.df_handler.activity_over_time, 'Date', 'ActivityCount', 'Activity Over Time')), 12),
            self._create_card("Document Usage Frequency", dcc.Graph(figure=self._create_bar_chart(self.df_handler.document_usage, 'Document', 'UsageCount', 'Document Usage Frequency')), 6),
            self._create_card("User Activity Distribution", dcc.Graph(figure=self._create_pie_chart(self.df_handler.user_activity, 'User', 'ActivityCount', 'User Activity Distribution')), 6)
        ])

    def graphs_layout(self):
        return self._create_layout("Interactive Graphs", [
            self._create_card("Filters", self._create_filters(), 12),
            self._create_card("Activity Over Time", dcc.Graph(figure=self._create_line_chart(self.df_handler.activity_over_time, 'Date', 'ActivityCount', 'Activity Over Time')), 12),
            self._create_card("Document Usage Frequency", dcc.Graph(figure=self._create_bar_chart(self.df_handler.document_usage, 'Document', 'UsageCount', 'Document Usage Frequency')), 6),
            self._create_card("User Activity Distribution", dcc.Graph(figure=self._create_pie_chart(self.df_handler.user_activity, 'User', 'ActivityCount', 'User Activity Distribution')), 6)
        ])

    def alerts_layout(self):
        return self._create_layout("Real-time Alerts", [
            self._create_card("Recent Alerts", self._create_alerts_list(), 12),
            self._create_card("Acknowledge All", dbc.Button("Acknowledge All", color="success", className="w-100"), 12)
        ])

    def activity_log_layout(self):
        return self._create_layout("Activity Log", [html.Div("Activity Log Content")])

    def settings_layout(self):
        return self._create_layout("Settings", [html.Div("Settings Content")])

    def upload_log_layout(self):
        return self._create_layout("Upload Log", [
            self._create_card("Upload JSON", self._create_upload_component(), 12)
        ])


    def create_header(self):
        current_date = datetime.now().strftime('%d-%m-%Y')
        logo_path = "/static/SFM-logo.png"
        return dbc.Navbar(
            dbc.Container([
                dbc.Row([
                    dbc.Col(html.Img(src=logo_path, height="40px"), width="auto"),
                    dbc.Col(html.H1(PROJECT_NAME, className="text-white"), width="auto"),
                    dbc.Col(
                    html.H2(
                          current_date,
                          className="text-white mt-2",
                          style={"fontSize": "1.2rem", "color": "lightgrey"}
                        ),
                        width="auto"
                    ),
                    dbc.Col(dbc.NavItem(dbc.NavLink("User Icon", href="#", className="text-white")), width="auto")
                ], align="center", justify="start"),
            ], fluid=True),
            color="primary",
            dark=True,
            style={"width": "100%"}
        )

    def create_side_menu(self):
        return dbc.Col([
            dbc.Nav(
                [
                    self._create_nav_link("fas fa-tachometer-alt", " Dashboard", "/"),
                    self._create_nav_link("fas fa-chart-line", " Graphs", "/graphs"),
                    self._create_nav_link("fas fa-cloud", " Upload Logs", "/upload-log"),
                    self._create_nav_link("fas fa-bell", " Alerts", "/alerts", "3", "danger"),
                    self._create_nav_link("fas fa-list", " Activity Log", "/activity-log"),
                    self._create_nav_link("fas fa-cog", " Settings", "/settings")
                ],
                vertical=True,
                pills=True,
                className="bg-dark h-100 p-3",
                style={"height": "100%"}
            ),
        ], width=2, className="bg-dark", style={"height": "100%", "overflow": "hidden"})


    def create_footer(self):
        return dbc.Navbar(
            dbc.Container([
                dbc.Row([
                    dbc.Col(html.P(f"© 2024 {PROJECT_NAME}, Inc.", className="text-white text-center mb-0"), width="auto"),
                    dbc.Col(html.P("Privacy Policy", className="text-white text-center mb-0"), width="auto"),
                    dbc.Col(html.P("Terms of Service", className="text-white text-center mb-0"), width="auto")
                ], align="center", justify="center", className="w-100")
            ]),
            color="primary",
            dark=True,
            style={"width": "100%"}
        )

    def define_layout(self):
        self.dash_app.layout = html.Div([
            self.create_header(),
            dbc.Container([
                dbc.Row([
                    self.create_side_menu(),
                    dcc.Location(id='url'),
                    dbc.Col(html.Div(id="page-content"), width=10, style={"height": "100%", "overflow": "auto"})
                ], style={"flex": "1", "overflow": "hidden", "height": "calc(100vh - 56px)"})
            ], fluid=True, style={"display": "flex", "flexDirection": "row", "flexGrow": "1", "height": "calc(100vh - 56px)"}),
            self.create_footer()
        ], style={"display": "flex", "flexDirection": "column", "height": "100vh"})

    def _create_layout(self, title: str, children: list) -> dbc.Container:
        return dbc.Container([
            dbc.Row([
                dbc.Col(
                    html.H2(title, style={"fontSize": "2.5rem", "textAlign": "left", "margin": "20px 0"}),
                    width=12
                )
            ]),
            dbc.Row(children)
        ], style={"padding": "20px"})

    def _create_card(self, title: str, content: html.Div, width: int) -> dbc.Col:
        return dbc.Col(dbc.Card([
            dbc.CardHeader(title),
            dbc.CardBody([content])
        ]), width=width, className="mb-3")

    def _create_filters(self) -> html.Div:
        return html.Div([
            dbc.Row([
                dbc.Col(dcc.Dropdown(id='document-dropdown', options=self.df_handler.filters_data['documents'], placeholder='Select Document'), width=4),
                dbc.Col(dcc.Dropdown(id='user-dropdown', options=self.df_handler.filters_data['users'], placeholder='Select User'), width=4),
                dbc.Col(dcc.Dropdown(id='description-dropdown', options=self.df_handler.filters_data['descriptions'], placeholder='Select Description'), width=4)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(dcc.DatePickerRange(id='date-picker-range', start_date=datetime.strptime(START_DATE, '%d-%m-%Y').date(), end_date=datetime.strptime(END_DATE, '%d-%m-%Y').date(), display_format='DD-MM-YYYY'), width=12)
            ], className="mb-3"),
            dbc.Button("Apply Filters", id='apply-filters', color="primary", className="w-100")
        ])

    def _create_alerts_list(self) -> html.Ul:
        return html.Ul([
            html.Li(
                f"{row['Time']} - {row['User']} - {row['Description']} - {row['Document']}",
                style={"color": "grey" if row['Status'] == "read" else "black",
                       "fontWeight": "bold" if row['Status'] == "unread" else "normal"}
            ) for index, row in self.df_handler.alerts_df.iterrows()
        ], className="list-unstyled")

    def _create_nav_link(self, icon_class: str, text: str, href: str, badge_text: str = "", badge_color: str = "") -> dbc.NavLink:
        children = [html.I(className=icon_class), html.Span(text, className="ml-2")]
        if badge_text:
            children.append(dbc.Badge(badge_text, color=badge_color, className="ml-2"))
        return dbc.NavLink(children, href=href, active="exact", className="text-white")

    def _create_line_chart(self, df: pd.DataFrame, x: str, y: str, title: str) -> px.line:
        return px.line(df, x=x, y=y, title=title)

    def _create_bar_chart(self, df: pd.DataFrame, x: str, y: str, title: str) -> px.bar:
        return px.bar(df, x=x, y=y, title=title)

    def _create_pie_chart(self, df: pd.DataFrame, names: str, values: str, title: str) -> px.pie:
        return px.pie(df, names=names, values=values, title=title)

    def _create_upload_component(self) -> html.Div:
        return html.Div([
            dcc.Upload(
                id='upload-json',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px 0'
                },
                multiple=False,  # Single file upload
                accept='.json'   # Accept only JSON files
            ),
            html.Div(id='output-json-upload', style={'margin': '10px 0'}),
            dbc.Button("Submit", id='submit-button', color="primary", className="w-100", disabled=True),
            html.Div(id='submit-status', style={'margin': '10px 0'})
        ])

