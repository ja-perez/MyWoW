import dash # type: ignore
from dash import dcc
from dash import html
from dash.dependencies import Input, Output # type: ignore
import pandas as pd # type: ignore
import plotly.graph_objs as go # type: ignore
import plotly.express as px # type: ignore
import analysis_service as analysis

from database import Database, DatabaseSetupService
import services.coinbase_services as cb

analysis_history = analysis.get_analysis_history()
dropdown_history_options = [
    {'label': label, 'value': label} for label in analysis_history
]

app = dash.Dash(__name__)
app.title = 'MyWoW Dashboard'

app.layout = html.Div([
    html.H1(
        'MyWoW Analysis Dashboard',
        style={'textAlign':'center', 'fontSize':46}),

    html.Div(
        [
            html.Label('Analysis History'),
            dcc.Dropdown(
                id='dropdown-history',
                options=dropdown_history_options,
                value='Select Analysis',
                placeholder='Select a previous analysis'
                )
        ],
        style={'width':'50%'}),

    html.Div(
        [
            html.Div(
                id='plot-output-container',
                style={'display':'flex', 'width': '100vw', 'flexWrap': 'wrap'},
            )
        ]),
])

@app.callback(
        Output(component_id='plot-output-container', component_property='children'),
        Input(component_id='dropdown-history', component_property='value'))
def update_plot_output(target_label: str):
    if target_label not in analysis_history:
        return []
    target = [analysis_history[label] for label in analysis_history if label==target_label][0]

    client = cb.get_client()
    db = Database('mywow.db')
    DatabaseSetupService(db)

    if not analysis.analysis_exists(analysis_target=target):
        analysis.fetch_and_upload_data(db, client, analysis_target=target)

    market_trade_charts = analysis.get_trade_analysis_charts(db, analysis_target=target)

    candlestick_plot = dcc.Graph(figure=market_trade_charts['candlestick'])
    trade_counts_plot = dcc.Graph(figure=market_trade_charts['trade_counts'])
    trade_totals_plot = dcc.Graph(figure=market_trade_charts['trade_totals'])

    return [
        html.Div(children=[html.Div(children=candlestick_plot)], style={'display':'flex'}),
        html.Div(children=[html.Div(children=trade_counts_plot)], style={'display':'flex'}),
        html.Div(children=[html.Div(children=trade_totals_plot)], style={'display':'flex'}),
    ]

if __name__=='__main__':
    app.run_server(debug=True)