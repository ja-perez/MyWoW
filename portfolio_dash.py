import dash # type: ignore
from dash import dcc, html
from dash.dependencies import Input, Output # type: ignore
import plotly.express as px # type: ignore
import plotly.graph_objects as go # type: ignore
from plotly.subplots import make_subplots # type: ignore

import pandas as pd # type: ignore
import datetime
import os
from requests.exceptions import HTTPError # type: ignore
from timeit import default_timer as timer

import services.coinbase_services as cb
from models.portfolio import Portfolio

client = cb.get_client()

portfolio = Portfolio(cb.get_default_portfolio(client))

app = dash.Dash(__name__)
app.title = 'MyWoW Dashboard'


""" (F) Balance Summary """
balance_container_style = {
    'backgroundColor':'lightgray',
    'padding':'5px', 'paddingInline':'15px', 'margin':'5px', 'marginInline':'5px',
    'border':'2.5px solid black', 'borderRadius':'10px',
    'display':'flex', 'flexDirection':'column', 'justifyContent':'start'}
balances = html.Div(
    id='account_balances',
    style={'display':'flex', 'flexDirection':'row', 'alignItems':'center'},
    children=[
        html.Div(
            id=balance_type,
            style=balance_container_style,
            children=[
                html.H3(balance_type.capitalize(), style={'margin':0}),
                html.Div(html.Hr()),
                html.Div(portfolio.display_balance(balance_type), style={'fontWeight':'bold'}),
            ]
        )
        for balance_type in portfolio.balances
    ]
)
balance_summary = html.Div(
    id='balance_summary',
    children=[
        html.H2('Balances'),
        balances,
    ]
)
""" (B) Balance Summary """
######################################
""" (F) Positions Summary """
positions_container_style = {
    'backgroundColor':'lightgray',
}
positions_header = html.Div(
    id='positions_header',
    style=positions_container_style,
    children=[
        html.H3('Asset'),
        html.H3('Value'),
        html.H3('Quantity'),
        html.H3('Unrealized Return'),
        html.H3('Current Price'),
    ]
)
positions = html.Div(
    id='account_positions',
    style={},
    children=[
        html.Div(
            id=position.asset_uuid,
            style=positions_container_style,
            children=[
                html.H3(position.symbol),
                html.Div(position.value),
                html.Div(position.quantity),
                html.Div(position.unrealized_pnl),
                html.Div(position.curr_price),
            ],
        )
        for position in portfolio.held_positions
    ]
)

positions_summary = html.Div(
    id='positions_summary',
    children=[
        html.H2('Positions'),
        positions_header,
        positions,
    ]
)
""" (B) Positions Summary """

title = html.H1('Portfolio Dashboard', style={'textAlign':'left', 'fontSize':46, 'marginBottom':'10px'})
app.layout = html.Div(
    id='app_layout',
    style={'backgroundColor':'lightgreen'},
    children=[
        title,
        balance_summary,
    ]
)

if __name__=='__main__':
    app.run_server(debug=True)