import dash # type: ignore
from dash import dcc, html, ctx, dash_table
from dash.dependencies import Input, Output, State # type: ignore
import plotly.graph_objs as go # type: ignore
import plotly.express as px # type: ignore

import pandas as pd # type: ignore
from requests.exceptions import HTTPError # type: ignore
from datetime import datetime, timedelta
from timeit import default_timer as timer

from database import Database, DatabaseSetupService
import services.coinbase_services as cb
import services.prediction_service as ps
from models import Prediction
import utils.utils as utils

MIN_DATE_DEFAULT: datetime = datetime(2020, 1, 1)
MAX_DATE_DEFAULT: datetime = datetime(datetime.today().year + 1, 6, 1)

db = Database('mywow.db')
DatabaseSetupService()
predictions_table_schema = db.get_table_schema('predictions')
df_predictions = pd.DataFrame(columns=[col_name for col_name in predictions_table_schema.keys()])
for col in df_predictions.columns:
    df_predictions[col].astype(db.typename_to_obj[predictions_table_schema[col]])
db.on_exit()

create_prediction_view = html.Div(
    id='create-prediction-view',
    hidden=True,
    children=[
        dcc.ConfirmDialog(
            id='confirm-clear',
            message='Are you sure you want to clear the form?',
        ),
        dcc.ConfirmDialog(
            id='confirm-submit',
            message='Are you sure you want to submit the prediction?'
        ),
        dcc.Input(
            id='trading-pair',
            type='text',
            placeholder='ex. BTC-USD, ETH-USD',
            value='',
            debounce=True
        ),
        dcc.DatePickerRange(
            id='date-range',
            min_date_allowed=MIN_DATE_DEFAULT,
            max_date_allowed=MAX_DATE_DEFAULT,
            initial_visible_month=datetime.today(),
        ),

        # Time selection check option
        # Start time setting component
        # End time setting component

        dcc.Checklist(
            id='opening-as-start-option',
            options=[{'label':'Use opening price as start price', 'value':True, 'disabled':False}],
            value=[True],
        ),
        dcc.Input(
            # TODO: Fetch opening price of trading pair for specified start date
            id='start-price',
            type='number',
            placeholder=0.0,
            debounce=True,
            min=0.0,
            disabled=True,
        ),
        dcc.Input(
            id='end-price',
            type='number',
            placeholder=0.0,
            debounce=True,
            min=0.0,
        ),
        html.Div('-%', id='price-change-indicator', style={}),

        dcc.Input(
            # TODO: Fetch opening price of trading pair for specified start date
            id='buy-price',
            type='number',
            placeholder=0.0,
            debounce=True,
            min=0.0,
        ),
        dcc.Input(
            id='sell-price',
            type='number',
            placeholder=0.0,
            debounce=True,
            min=0.0,
        ),
        html.Div('--.- %', id='expected-returns-percent-indicator', style={}),
        html.Div('$ --.--', id='expected-returns-amount-indicator', style={}),
        html.Button(
            id='submit-prediction-button',
            children='Submit',
            n_clicks=0,
        ),
        html.Button(
            id='clear-form-button',
            children='Clear',
            n_clicks=0,
        )
    ]
)

read_prediction_view = html.Div(
    id='read-prediction-view',
    hidden=True,
    children=[
        dash_table.DataTable(df_predictions)
    ]
)

update_prediction_view = html.Div(
    id='update-prediction-view',
    hidden=True,
    children=[
    ]
)

delete_prediction_view = html.Div(
    id='delete-prediction-view',
    hidden=True,
    children=[
    ]
)

invalid_input_style = {
    'borderColor': 'red'
}

def register_callbacks(app):
    @app.callback(Output('trading-pair', 'style'),
                  Output('date-range', 'disabled'),
                  Output('date-range', 'min_date_allowed'),
                  Input('trading-pair', 'value'))
    def validate_trading_pair(trading_pair: str):
        if not trading_pair:
            return {}, True, MIN_DATE_DEFAULT
        trading_pair_details = cb.trading_pair_exists(cb.get_client(), trading_pair)
        return_values = [
            invalid_input_style if not trading_pair_details else {},
            not trading_pair_details,
            datetime.fromisoformat(trading_pair_details.get('new_at', MIN_DATE_DEFAULT.isoformat()))
        ]
        return return_values

    @app.callback(Output('start-price', 'disabled'),
                  Output('end-price', 'disabled'),
                  Output('buy-price', 'disabled'),
                  Output('sell-price', 'disabled'),
                  Output('opening-as-start-option', 'options'),
                  Output('opening-as-start-option', 'value'),
                  State('opening-as-start-option', 'options'),
                  Input('date-range', 'start_date'),
                  Input('date-range', 'end_date'),)
    def validate_date_range(options, start_date, end_date):
        for option in options:
            option['disabled'] = True

        if not start_date or not end_date:
            return [True, True, True, True, options, [True]]
        if datetime.fromisoformat(start_date).date() >= datetime.today().date():
            return [False, False, False, False, options, []]

        for option in options:
            option['disabled'] = False
        return [False, False, False, False, options, [True]]

    @app.callback(Output('start-price', 'value'),
                  Input('start-price', 'disabled'),
                  Input('opening-as-start-option', 'value'),
                  State('trading-pair', 'value'),
                  State('date-range', 'start_date'),
                  Input('confirm-clear', 'submit_n_clicks'))
    def update_start_price(disabled, use_opening_price, trading_pair, start_date, submit_n_clicks):
        print(disabled, use_opening_price, trading_pair, start_date, submit_n_clicks)
        if ctx.triggered_id == 'confirm-clear' or disabled or not use_opening_price:
            return 0
        start = datetime.fromisoformat(start_date)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        start_date_candle = cb.get_asset_candles(cb.get_client(), trading_pair, cb.Granularity.ONE_DAY, start, end, limit=1)[-1]
        return float(start_date_candle['open'])

    @app.callback(Output('price-change-indicator', 'children'),
                  Input('start-price', 'value'),
                  Input('end-price', 'value'),
                  Input('confirm-clear', 'submit_n_clicks'))
    def update_price_change_indicator(start_price, end_price, submit_n_clicks):
        if ctx.triggered_id == 'confirm-clear' or not start_price or not end_price:
            return '--.- %' 
        price_change = (float(end_price) - float(start_price)) / float(start_price) * 100
        return f'{price_change:+.1f} %'

    @app.callback(Output('expected-returns-percent-indicator', 'children'),
                  Output('expected-returns-amount-indicator', 'children'),
                  Input('buy-price', 'value'),
                  Input('sell-price', 'value'),
                  Input('confirm-clear', 'submit_n_clicks'))
    def update_expected_returns_indicator(buy_price, sell_price, submit_n_clicks):
        if ctx.triggered_id == 'confirm-clear' or not buy_price or not sell_price:
            return '--.- %', '$ --.--'
        expected_returns = (float(sell_price) - float(buy_price)) / float(buy_price) * 100
        expected_returns_amount = float(sell_price) - float(buy_price)
        return f'{expected_returns:+.1f} %', f'{'+' if expected_returns_amount > 0 else '-'}${abs(expected_returns_amount):.2f}'

    @app.callback(Output('submit-prediction-button', 'disabled'),
                  Input('trading-pair', 'value'),
                  Input('date-range', 'start_date'),
                  Input('date-range', 'end_date'),
                  Input('start-price', 'value'),
                  Input('end-price', 'value'),
                  Input('buy-price', 'value'),
                  Input('sell-price', 'value'),)
    def activate_submit_button(trading_pair, start_date, end_date, start_price, end_price, buy_price, sell_price):
        if not trading_pair or not start_date or not end_date or not start_price or not end_price or not buy_price or not sell_price:
            return True
        return False

    @app.callback(Output('confirm-submit', 'displayed'),
                  Input('submit-prediction-button', 'n_clicks'))
    def display_submit_confirm(n_clicks):
        return n_clicks > 0

    @app.callback(Output('confirm-clear', 'submit_n_clicks'),
                  Input('confirm-submit', 'submit_n_clicks'),
                  State('confirm-clear', 'submit_n_clicks'),
                  State('trading-pair', 'value'),
                  State('date-range', 'start_date'),
                  State('date-range', 'end_date'),
                  State('start-price', 'value'),
                  State('end-price', 'value'),
                  State('buy-price', 'value'),
                  State('sell-price', 'value'))
    def submit_prediction(submit_n_clicks, clear_n_clicks, trading_pair, start_date, end_date, start_price, end_price, buy_price, sell_price):
        if not submit_n_clicks:
            return dash.no_update
        prediction_data = {
            'symbol': trading_pair.split('-')[0],
            'trading_pair': trading_pair,
            'start_date': datetime.fromisoformat(start_date),
            'end_date': datetime.fromisoformat(end_date),
            'start_price': float(start_price),
            'end_price': float(end_price),
            'buy_price': float(buy_price),
            'sell_price': float(sell_price),
        }
        prediction = Prediction(prediction_data)
        try:
            ps.PredictionService().add_prediction(prediction)
        except Exception as e:
            print('ERROR CREATING DATABASE')
        return 1 if not clear_n_clicks else clear_n_clicks + 1

    @app.callback(Output('confirm-clear', 'displayed'),
                  Input('clear-form-button', 'n_clicks'))
    def display_clear_confirm(n_clicks):
        return n_clicks > 0

    @app.callback(Output('trading-pair' , 'value'),
                  Output('date-range', 'start_date'),
                  Output('date-range', 'end_date'),
                  Output('end-price', 'value'),
                  Output('buy-price', 'value'),
                  Output('sell-price', 'value'),
                  Input('confirm-clear', 'submit_n_clicks'),)
    def clear_form_button(submit_n_clicks):
        return [
            '',
            None,
            None,
            0,
            0,
            0,
            ]
