import dash # type: ignore
from dash import dcc
from dash import html
from dash.dependencies import Input, Output # type: ignore
import plotly.graph_objs as go # type: ignore
import plotly.express as px # type: ignore

import pandas as pd # type: ignore
import datetime
from requests.exceptions import HTTPError # type: ignore
from timeit import default_timer as timer

import analysis_service as analysis
from database import Database, DatabaseSetupService
import services.coinbase_services as cb


analysis_history = analysis.get_analysis_history()
dropdown_history_options = [
    {'label': label, 'value': label} for label in analysis_history
]

hours = [f"{i:0{2}}" for i in range(24)]
minutes = [f"{i:0{2}}" for i in range(60)]
seconds = [f"{i:0{2}}" for i in range(60)]
time_picker_style = {'border':'none', 'display':'flex', 'justifyContent':'space-between', 'alignItems':'center', 'minWidth':'60px'}

hour_picker = dcc.Dropdown(id='time-hour', value=0, options=hours, placeholder='HH', style=time_picker_style)
minute_picker = dcc.Dropdown(id='time-minute', value=0, options=minutes, placeholder='MM', style=time_picker_style)
seconds_picker = dcc.Dropdown(id='time-seconds', value=0, options=seconds, placeholder='SS', style=time_picker_style)
time_picker = html.Div(
    className='time-picker',
    style={'display':'flex', 'alignItems':'center'},
    children=[
        hour_picker,
        html.Span(':', style={'fontWeight':'bold', 'paddingInline':'2.5px'}),
        minute_picker,
        html.Span(':', style={'fontWeight':'bold', 'paddingInline':'2.5px'}),
        seconds_picker
    ]
)


app = dash.Dash(__name__)
app.title = 'MyWoW Dashboard'

app.layout = html.Div(
    id='app_layout',
    children=[
        html.H1(
            'MyWoW Analysis Dashboard',
            style={'textAlign':'left', 'fontSize':46, 'marginBottom':'10px'}),
        
        html.Div(
            id='content-body',
            style={'padding':'5px'},
            children=[
                html.Div(
                    id='target-options',
                    style={'display':'grid', 'gridTemplate':'100% / 50% 50%'},
                    children=[
                        html.Div(
                            id='analysis-history-container',
                            style={'display':'flex', 'flexDirection':'column', 'marginInline':'5px'},
                            children=[
                                html.H3('Analysis History'),
                                html.Label('Previous Analysis Targets'),
                                dcc.Dropdown(
                                    id='dropdown-history',
                                    options=dropdown_history_options,
                                    value='analysis-target',
                                    placeholder='Select a previous analysis'
                                    ),
                            ]
                        ),
                        html.Div(
                            id='new-analysis-container',
                            style={'display':'flex', 'flexDirection':'column', 'marginInline':'5px'},
                            children=[
                                html.H3('New Analysis Target'),
                                html.Label('Trading Pair'),
                                dcc.Input(
                                    id='trading-pair',
                                    type='text',
                                    placeholder='ex. BTC-USD, ETH-USD',
                                    debounce=True
                                ),
                                dcc.RadioItems(
                                    id='datetime-option',
                                    options=[{'label':'Multiple Days', 'value':'date'}, {'label':'Same Day', 'value':'time'}], 
                                    value='date', 
                                    inline=True),
                                html.Div(
                                    id='date-container',
                                    hidden=False,
                                    children=[
                                        dcc.DatePickerRange(
                                            id='target-date',
                                            min_date_allowed=datetime.date(2020, 1, 1),
                                            max_date_allowed=datetime.date.today(),
                                            initial_visible_month=datetime.date.today(),
                                            end_date=datetime.date.today(),
                                        ),
                                    ]
                                ),
                                html.Div(
                                    id='time-container',
                                    hidden=True,
                                    children=[
                                        html.Div(
                                            style={'display':'flex', 'alignItems':'center', 'justifyContent':'space-around'},
                                            children=[
                                                dcc.DatePickerSingle(
                                                    id='target-date-single',
                                                    min_date_allowed=datetime.date(2020, 1, 1),
                                                    max_date_allowed=datetime.date.today(),
                                                    initial_visible_month=datetime.date.today(),
                                                    ),
                                                html.Div(
                                                    style={'display':'flex', 'flexDirection':'column', 'alignItems':'left', 'paddingInline':'25px'},
                                                    children=[
                                                        html.Label('Start Time'),
                                                        html.Div(
                                                            className='time-picker',
                                                            style={'display':'flex', 'alignItems':'center'},
                                                            children=[
                                                                dcc.Dropdown(id='start-hour', value=0, options=hours, placeholder='HH', style=time_picker_style),
                                                                html.Span(':', style={'fontWeight':'bold', 'paddingInline':'2.5px'}),
                                                                dcc.Dropdown(id='start-minute', value=0, options=minutes, placeholder='MM', style=time_picker_style),
                                                                html.Span(':', style={'fontWeight':'bold', 'paddingInline':'2.5px'}),
                                                                dcc.Dropdown(id='start-seconds', value=0, options=seconds, placeholder='SS', style=time_picker_style),
                                                            ]
                                                        ),
                                                    ]
                                                ),
                                                html.Div(
                                                    style={'display':'flex', 'flexDirection':'column', 'alignItems':'left', 'paddingInline':'25px'},
                                                    children=[
                                                        html.Label('End Time'),
                                                        html.Div(
                                                            className='time-picker',
                                                            style={'display':'flex', 'alignItems':'center'},
                                                            children=[
                                                                dcc.Dropdown(id='end-hour', value=0, options=hours, placeholder='HH', style=time_picker_style),
                                                                html.Span(':', style={'fontWeight':'bold', 'paddingInline':'2.5px'}),
                                                                dcc.Dropdown(id='end-minute', value=0, options=minutes, placeholder='MM', style=time_picker_style),
                                                                html.Span(':', style={'fontWeight':'bold', 'paddingInline':'2.5px'}),
                                                                dcc.Dropdown(id='end-seconds', value=0, options=seconds, placeholder='SS', style=time_picker_style),
                                                            ]
                                                        ),
                                                    ]
                                                ),
                                            ],
                                        )
                                    ]
                                ),
                                html.Button(
                                    'Submit',
                                    id='target-submit-button',
                                    n_clicks=0
                                )
                            ]
                        )
                    ],
                ),

                html.Hr(),

                html.Div(
                    style={'minHeight':'100px', 'padding':'5px', 'border':'2.5px solid lightgray', 'borderRadius':'10px'
                    },
                    children=[
                        dcc.Loading(
                            id='load-data',
                            children=[
                                html.Div(
                                    id='plots-container',
                                    style={'display':'flex', 'width': '100vw', 'flexWrap': 'wrap'},
                                ),
                            ],
                            type='circle',
                            style={'display':'flex', 'width': '100vw', 'height':'100%'},
                        )
                    ],
                ),

            ]
        ),
])

@app.callback(Output('trading-pair', 'value'), Input('trading-pair', 'value'))
def validate_trading_pair(trading_pair):
    try:
        assert(trading_pair is not None)
        client = cb.get_client()
        client.get_product(trading_pair.upper())
        return trading_pair.upper()
    except AssertionError:
        return None
    except HTTPError:
        return None

@app.callback(Output('date-container', 'hidden'), Input('datetime-option', 'value'))
def update_date_container(selected_range):
    return selected_range != 'date'

@app.callback(Output('time-container', 'hidden'), Input('datetime-option', 'value'))
def update_time_container(selected_range):
    return selected_range != 'time'

@app.callback(
        Output('target-submit-button', 'disabled'), 
        [
            Input('trading-pair', 'value'), 
            Input('datetime-option', 'value'),
            Input('target-date', 'start_date'),
            Input('target-date', 'end_date'),
            Input('target-date-single', 'date'),
            Input('start-hour', 'value'),
            Input('start-minute', 'value'),
            Input('start-seconds', 'value'),
            Input('end-hour', 'value'),
            Input('end-minute', 'value'),
            Input('end-seconds', 'value'),
            ])
def update_target_submit_button(trading_pair, datetime_option, start_date, end_date, single_date, start_hour, start_minute, start_seconds, end_hour, end_minute, end_seconds):
    if not trading_pair:
        return True

    if datetime_option == 'date':
        if not start_date or not end_date:
            return True
        start = datetime.date.fromisoformat(start_date)
        end = datetime.date.fromisoformat(end_date) + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
        if start >= end:
            return True
    else:
        if not single_date:
            return True
        start_time = datetime.time(hour=int(start_hour), minute=int(start_minute), second=int(seconds))
        end_time = datetime.time(hour=int(end_hour), minute=int(end_minute), second=int(seconds))
        if start_time >= end_time:
            return True

    return False

@app.callback(Output('plots-container', 'children'), Input('dropdown-history', 'value'))
def update_plots_container(target_label: str):
    if target_label not in analysis_history:
        return []
    target = [analysis_history[label] for label in analysis_history if label==target_label][0]

    start_1 = timer()

    db = Database('mywow.db')
    if not analysis.analysis_exists(analysis_target=target):
        client = cb.get_client()
        analysis.fetch_and_upload_data(db, client, analysis_target=target)

    dash.callback_context.record_timing('task_1', timer() - start_1, '1st Task')
    start_2 = timer()

    market_trade_charts = analysis.get_trade_analysis_charts(db, analysis_target=target)
    db.on_exit()

    dash.callback_context.record_timing('task_2', timer() - start_2, '2nd Task')

    candlestick_plot = dcc.Graph(figure=market_trade_charts['candlestick'])
    trade_counts_plot = dcc.Graph(figure=market_trade_charts['trade_counts'])
    trade_totals_plot = dcc.Graph(figure=market_trade_charts['trade_totals'])

    return [
        html.Div(children=[html.Div(children=candlestick_plot)], style={'display':'flex'}),
        html.Div(children=[html.Div(children=trade_counts_plot)], style={'display':'flex'}),
        html.Div(children=[html.Div(children=trade_totals_plot)], style={'display':'flex'}),
    ]

if __name__=='__main__':
    # db = Database('mywow.db')
    # DatabaseSetupService()
    # db.on_exit()
    app.run_server(debug=True)