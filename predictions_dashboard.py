from dash import Dash, dcc, html, ctx # type: ignore
from dash.dependencies import Input, Output # type: ignore
import plotly.graph_objs as go # type: ignore
import plotly.express as px # type: ignore

import pandas as pd # type: ignore
from requests.exceptions import HTTPError # type: ignore
import datetime
from timeit import default_timer as timer

import services.coinbase_services as cb
import services.prediction_service as ps
from database import Database, DatabaseSetupService
from models import Prediction
from prediction_views import create_prediction_view, read_prediction_view, update_prediction_view, delete_prediction_view, register_callbacks
import utils.utils as utils

app = Dash(__name__)
app.title = 'MyWoW'

title = html.H1('Predictions Dashboard')

button_style: dict[str, str] = {}
options = {
    'create-prediction': 'New Prediction',
    'read-prediction': 'View Predictions',
    'update-prediction': 'Edit Predictions',
    'delete-prediction': 'Delete Predictions',
}
options_container = html.Div(
    id='options-container',
    style={},
    children=[
        html.Button(
            option_title,
            id=f'{option_type}-button',
            style=button_style,
            n_clicks=0
        )
        for option_type, option_title in options.items()
    ]
)
view_container_style: dict[str, str] = {}
view_container = html.Div(
    id='view-container',
    style={},
    children=[
        create_prediction_view,
        read_prediction_view,
        update_prediction_view,
        delete_prediction_view,
    ]
)

@app.callback(Output('create-prediction-view', 'hidden'),
              Output('read-prediction-view', 'hidden'),
              Output('update-prediction-view', 'hidden'),
              Output('delete-prediction-view', 'hidden'),
              Input('create-prediction-button', 'n_clicks'), 
              Input('read-prediction-button', 'n_clicks'),
              Input('update-prediction-button', 'n_clicks'),
              Input('delete-prediction-button', 'n_clicks'))
def update_view(create_button, read_button, update_button, delete_button):
    return ['create-prediction-button' != ctx.triggered_id,
            'read-prediction-button' != ctx.triggered_id,
            'update-prediction-button' != ctx.triggered_id,
            'delete-prediction-button' != ctx.triggered_id]

app.layout = html.Div(
    id='app_layout',
    children=[
        title,
        options_container,
        view_container
    ]
)

register_callbacks(app)

if __name__=='__main__':
    app.run_server(debug=True)