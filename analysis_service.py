import plotly.express as px # type: ignore
import plotly.graph_objects as go # type: ignore
from plotly.subplots import make_subplots # type: ignore
import seaborn as sns # type: ignore

from typing import Optional
import pandas as pd # type: ignore
import datetime
import os

from models import Candle, MarketTrade
from database import Database, DatabaseSetupService
from coinbase.rest import RESTClient # type: ignore
import services.coinbase_services as cb

CWD = os.getcwd()
DATA_DIR = os.path.join(CWD, 'data')
ANALYSIS_DIR = os.path.join(DATA_DIR, 'analysis')
ANALYSIS_HISTORY_FILENAME = 'history.csv'
ANALYSIS_HISTORY_PATH = os.path.join(ANALYSIS_DIR, ANALYSIS_HISTORY_FILENAME)

WEEKDAY_ORDER = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

PLACEHOLDER_DATE = datetime.datetime.now()

class AnalysisTarget:
    def __init__(self, trading_pair: str, start_date: datetime.datetime, end_date:datetime.datetime):
        self.trading_pair = trading_pair
        self.start_date = start_date
        self.end_date = end_date

        self.expected_candles_count = cb.Granularity.get_count_from_granularity(self.start_date, self.end_date, cb.Granularity.ONE_MINUTE)

    def get_date_summary(self):
        if self.end_date.date() == self.start_date.date():
            return f"{self.start_date.strftime('%m/%d/%y')} between {self.start_date.strftime('%H:%M')}-{self.end_date.strftime('%H:%M')}"
        else:
            return f"between {self.start_date.strftime('%m/%y')}-{self.end_date.strftime('%m/%y')}"

    def get_core_values(self, as_dict: bool=False) -> dict | list:
        if as_dict:
            return {
                'trading_pair': self.trading_pair,
                'start_date': self.start_date,
                'end_date': self.end_date,
            }
        return [self.trading_pair, self.start_date, self.end_date]

def get_analysis_history() -> dict[str, AnalysisTarget]:
    history = {}
    with open(ANALYSIS_HISTORY_PATH, 'r') as f:
        header = f.readline()
        for row in f.readlines():
            data = row.split(',')
            trading_pair = data[0]
            start_date = datetime.datetime.fromisoformat(data[1])
            end_date = datetime.datetime.fromisoformat(data[2])
            # created_date = datetime.datetime.fromisoformat(data[3])
            # last_updated_date = datetime.datetime.fromisoformat(data[4])

            if end_date.date() == start_date.date():
                label_date = f"{start_date.strftime('%m/%d/%y')} between {start_date.strftime('%H:%M')}-{end_date.strftime('%H:%M')}"
            else:
                label_date = f"{start_date.strftime('%m/%y')}-{end_date.strftime('%m/%y')}"

            label = f"{trading_pair} | {label_date}"
            history[label] = AnalysisTarget(trading_pair=trading_pair, start_date=start_date, end_date=end_date)

    return history

def analysis_exists(trading_pair: str='', start_date: datetime.datetime=PLACEHOLDER_DATE, end_date: datetime.datetime=PLACEHOLDER_DATE,
                    analysis_target: Optional[AnalysisTarget]=None):
    """ 
    Checks if parameters exist in local analysis history log file
    """
    trading_pair = analysis_target.trading_pair if analysis_target else trading_pair
    start_date = analysis_target.start_date if analysis_target else start_date
    end_date = analysis_target.end_date if analysis_target else end_date

    with open(ANALYSIS_HISTORY_PATH, 'r') as f:
        header = f.readline()
        for row in f.readlines():
            data = row.split(',')
            row_pair = data[0]
            row_start = datetime.datetime.fromisoformat(data[1])
            row_end = datetime.datetime.fromisoformat(data[2])   

            if row_pair == trading_pair and row_start == start_date and row_end == end_date:
                return True
    return False

def fetch_and_upload_data(
        db: Database, client: RESTClient, 
        trading_pair: str='', start_date: datetime.datetime=PLACEHOLDER_DATE, end_date: datetime.datetime=PLACEHOLDER_DATE,
        analysis_target: Optional[AnalysisTarget]=None):
    trading_pair = analysis_target.trading_pair if analysis_target else trading_pair
    start_date = analysis_target.start_date if analysis_target else start_date
    end_date = analysis_target.end_date if analysis_target else end_date

    if analysis_exists(trading_pair=trading_pair, start_date=start_date, end_date=end_date):
        return

    market_trades = cb.fetch_market_trades(client, trading_pair, start_date, end_date, cb.CANDLES_LIMIT_MAX)
    for market_trade_data in market_trades:
        market_trade = MarketTrade(market_trade_data)
        db.insert_one(table_name='market_trades', values=market_trade.get_values())

    candles = cb.fetch_market_trade_candles(client, trading_pair, start_date, end_date, cb.CANDLES_LIMIT_MAX)
    for candle_data in candles:
        candle = Candle(candle_data)
        db.insert_one(table_name='candles', values=candle.get_values())

def get_candles_df(
        db: Database, granularity: str,
        trading_pair: str='', start_date: datetime.datetime=PLACEHOLDER_DATE, end_date: datetime.datetime=PLACEHOLDER_DATE,
        analysis_target: Optional[AnalysisTarget]=None):
    trading_pair = analysis_target.trading_pair if analysis_target else trading_pair
    start_date = analysis_target.start_date if analysis_target else start_date
    end_date = analysis_target.end_date if analysis_target else end_date

    res = db.get_rows(
        table_name='candles',
        where_statement=f"WHERE trading_pair='{trading_pair}' AND time between '{start_date.isoformat()}' AND '{end_date.isoformat()}' AND granularity='{granularity}'"
    )
    market_candles = [Candle(candle) for candle in res]

    df_candles = pd.DataFrame(data=[candle.to_dict() for candle in market_candles])
    df_candles['timestamp'] = df_candles['start']
    df_candles['minute'] = df_candles['time'].transform(lambda x: x.minute)
    df_candles['hour'] = df_candles['time'].transform(lambda x: x.hour)
    df_candles['weekday'] = df_candles['time'].transform(lambda x: x.strftime('%A'))
    df_candles['month'] = df_candles['time'].transform(lambda x: x.month)
    df_candles['year'] = df_candles['time'].transform(lambda x: x.year)
    df_candles['month_year'] = df_candles['time'].transform(lambda x: x.strftime('%y-%m'))

    df_candles['price_change'] = df_candles['close'] - df_candles['open']
    df_candles['price_direction'] = df_candles['price_change'].transform(lambda x: 'Positive' if x > 0 else 'Negative')
    df_candles['percent_change'] = (df_candles['price_change'] / df_candles['open']) * 100

    return df_candles

def get_market_trades_df(
        db: Database, 
        trading_pair: str='', start_date: datetime.datetime=PLACEHOLDER_DATE, end_date: datetime.datetime=PLACEHOLDER_DATE,
        analysis_target: Optional[AnalysisTarget]=None):
    trading_pair = analysis_target.trading_pair if analysis_target else trading_pair
    start_date = analysis_target.start_date if analysis_target else start_date
    end_date = analysis_target.end_date if analysis_target else end_date

    res = db.get_rows(
        table_name='market_trades',
        where_statement=f"WHERE trading_pair='{trading_pair}' AND time between '{start_date.isoformat()}' AND '{end_date.isoformat()}'"
    )
    market_trades = [MarketTrade(market_trade) for market_trade in res]
    market_trade_data = []
    for trade in market_trades:
        data = trade.to_dict()
        data['total'] = trade.total
        market_trade_data.append(data)

    df_trades = pd.DataFrame(data=market_trade_data)
    df_trades['timestamp'] = df_trades['time'].transform(lambda x: x.timestamp()) 
    df_trades['hour'] = df_trades['time'].transform(lambda x: x.hour)
    df_trades['minute'] = df_trades['time'].transform(lambda x: x.minute)
    df_trades['second'] = df_trades['time'].transform(lambda x: x.second)
    df_trades['hour_min'] = df_trades['time'].transform(lambda x: datetime.time(hour=x.hour, minute=x.minute))
    df_trades.sort_values(by='time', inplace=True)
    return df_trades

# Market Trade Analysis
def generate_candle_chart(df_candles: pd.DataFrame, trgt: AnalysisTarget, save_html: bool = False, save_path: str = '') -> go.Figure:
    fig = go.Figure(
        data=[go.Candlestick(
            x=df_candles.time,
            open=df_candles.open,
            high=df_candles.high,
            low=df_candles.low,
            close=df_candles.close
        )]
    )
    fig.update_layout(
        title=f"Price Change for {trgt.trading_pair} on {trgt.get_date_summary()}",
        yaxis=dict(
            title=dict(text='Price')
        ),
        xaxis=dict(
            title=dict(text='Time'),
            dtick=5*60*1000,
        ),
    )

    if save_html:
        save_path = save_path if save_path else f"{trgt.trading_pair}_candlestick.html"
        fig.write_html(os.path.join(ANALYSIS_DIR, save_path))
    return fig

def generate_trade_counts_chart(df_trades: pd.DataFrame, trgt: AnalysisTarget, save_html: bool = False, save_path: str = '') -> go.Figure:
    df_trade_counts = df_trades.groupby(['hour_min', 'side'], as_index=False).agg(
        counts=pd.NamedAgg(column='trade_id', aggfunc='count')
    )
    fig = px.bar(df_trade_counts, x='hour_min', y='counts', color='side')
    fig.update_layout(
        title=f"{trgt.trading_pair} market trade counts on {trgt.get_date_summary()}",
        yaxis=dict(
            title=dict(text='Counts'),
        ),
        xaxis=dict(
            title=dict(text='Time'),
        ),
    )

    if save_html:
        save_path = save_path if save_path else f"{trgt.trading_pair}_trade_counts_bar.html"
        fig.write_html(os.path.join(ANALYSIS_DIR, save_path))
    return fig

def generate_trade_totals_chart(df_trades: pd.DataFrame, trgt: AnalysisTarget, save_html: bool = False, save_path: str = '') -> go.Figure:
    df_totals = df_trades.groupby(['hour_min', 'side'], as_index=False)['total'].sum()
    fig = px.bar(df_totals, x='hour_min', y='total', color='side')
    fig.update_layout(
        title=f"{trgt.trading_pair} market trade totals on {trgt.get_date_summary()}",
        xaxis=dict(
            title=dict(text='Time')
        ),
        yaxis=dict(
            title=dict(text='Total')
        ),
    )

    if save_html:
        save_path = save_path if save_path else f"{trgt.trading_pair}_trade_totals_bar.html"
        fig.write_html(os.path.join(ANALYSIS_DIR, save_path))
    return fig

# Weekday Price Analysis
def generate_price_direction_counts_chart(df_candles: pd.DataFrame, trgt: AnalysisTarget, save_html: bool = False, save_path: str = '') -> go.Figure:
    df_direction_counts = df_candles.groupby(['month_year', 'weekday', 'price_direction'], as_index=False).agg(
        counts=pd.NamedAgg(column='candle_id', aggfunc='count')
    )
    df_direction_counts.sort_values(by='month_year')
    fig = px.bar(df_direction_counts, x='month_year', y='counts', color='price_direction',
                        barmode='group', facet_row='weekday', category_orders={'weekday': WEEKDAY_ORDER})
    fig.update_layout(
        title=f"{trgt.trading_pair} price direction counts {trgt.get_date_summary()}",
        yaxis=dict(
            title=dict(text='Counts')
        ),
        xaxis=dict(
            title=dict(text='Month-Year')
        ),
    )
    fig.for_each_annotation(lambda x: x.update(text=x.text.split('=')[-1]))

    if save_html:
        save_path = save_path if save_path else f"{trgt.trading_pair}_weekday_price_direction_counts_bar.html"
        fig.write_html(os.path.join(ANALYSIS_DIR, save_path))
    return fig

def generate_percent_diff_totals_chart(df_candles: pd.DataFrame, trgt: AnalysisTarget, save_html: bool = False, save_path: str = '') -> go.Figure:
    df_diff_totals = df_candles.groupby(['month_year', 'weekday', 'price_direction'], as_index=False)['percent_change'].sum()
    fig = px.bar(df_diff_totals, x='month_year', y='percent_change', color='price_direction',
                             barmode='group', facet_row='weekday', category_orders={'weekday': WEEKDAY_ORDER})
    fig.update_layout(
        title=f"{trgt.trading_pair} total percent change {trgt.get_date_summary()}",
        yaxis=dict(
            title=dict(text='% Diff.')
        ),
        xaxis=dict(
            title=dict(text='Month-Year')
        ),
    )
    fig.for_each_annotation(lambda x: x.update(text=x.text.split('=')[-1]))

    if save_html:
        save_path = save_path if save_path else f"{trgt.trading_pair}_weekday_percent_change_totals_bar.html"
        fig.write_html(os.path.join(ANALYSIS_DIR, save_path))
    return fig

def generate_price_change_avg_min_max_chart(df_candles: pd.DataFrame, trgt: AnalysisTarget, save_html: bool = False, save_path: str = '') -> go.Figure:
    df_change = df_candles[['month_year', 'weekday', 'price_change']].groupby(['month_year', 'weekday'], as_index=False).agg(
        average=pd.NamedAgg(column='price_change', aggfunc='mean'),
        min=pd.NamedAgg(column='price_change', aggfunc='min'),
        max=pd.NamedAgg(column='price_change', aggfunc='max'),
    )
    fig = px.bar(df_change, x='month_year', y=['average', 'min', 'max'],
                        barmode='group', facet_row='weekday', category_orders={'weekday': WEEKDAY_ORDER})
    fig.update_layout(
        title=f"{trgt.trading_pair} price change {trgt.get_date_summary()}",
        yaxis=dict(
            title=dict(text='Amount')
        ),
        xaxis=dict(
            title=dict(text='Month-Year')
        ),
    )
    fig.for_each_annotation(lambda x: x.update(text=x.text.split('=')[-1]))

    if save_html:
        save_path = save_path if save_path else f"{trgt.trading_pair}_weekday_avg_min_max_bar.html"
        fig.write_html(os.path.join(ANALYSIS_DIR, save_path))
    return fig

def get_trade_analysis_charts(
        db: Database, analysis_target: Optional[AnalysisTarget]=None, 
        trading_pair: str='', start_date: datetime.datetime=PLACEHOLDER_DATE, end_date: datetime.datetime=PLACEHOLDER_DATE):
    if not analysis_target:
        analysis_target = AnalysisTarget(trading_pair=trading_pair, start_date=start_date, end_date=end_date)
    else:
        trading_pair, start_date, end_date = analysis_target.get_core_values()

    df_candles = get_candles_df(db, analysis_target=analysis_target, granularity=cb.Granularity.ONE_MINUTE)
    df_trades = get_market_trades_df(db, trading_pair, start_date, end_date)

    charts = {
        'candlestick': generate_candle_chart(df_candles, analysis_target),
        'trade_counts': generate_trade_counts_chart(df_trades, analysis_target),
        'trade_totals': generate_trade_totals_chart(df_trades, analysis_target),
    }
    return charts 

def get_weekday_analysis_charts(
        db: Database, analysis_target: Optional[AnalysisTarget]=None, 
        trading_pair: str='', start_date: datetime.datetime=PLACEHOLDER_DATE, end_date: datetime.datetime=PLACEHOLDER_DATE):
    if not analysis_target:
        analysis_target = AnalysisTarget(trading_pair=trading_pair, start_date=start_date, end_date=end_date)
    else:
        trading_pair, start_date, end_date = analysis_target.get_core_values()

    df_candles = get_candles_df(db, trading_pair=trading_pair, start_date=start_date, end_date=end_date, granularity=cb.Granularity.ONE_DAY)

    charts = {
        'price_direction': generate_price_direction_counts_chart(df_candles, analysis_target),
        'percent_difference': generate_percent_diff_totals_chart(df_candles, analysis_target),
        'price_change': generate_price_change_avg_min_max_chart(df_candles, analysis_target),
    }
    return charts 

def main():
    db = Database('mywow.db')
    DatabaseSetupService(db)

    client = cb.get_client()

    # market trades analysis
    trading_pair = 'SWELL-USD'
    start = datetime.datetime(year=2025, month=2, day=10, hour=1, minute=30, second=0, tzinfo=cb.LOCAL_TZ)
    end = datetime.datetime(year=2025, month=2, day=10, hour=3, minute=00, second=0, tzinfo=cb.LOCAL_TZ)
    target = AnalysisTarget(trading_pair=trading_pair, start_date=start, end_date=end)

    if not analysis_exists(analysis_target=target):
        fetch_and_upload_data(db, client, analysis_target=target)

    df_candles = get_candles_df(db, trading_pair=trading_pair, start_date=start, end_date=end, granularity=cb.Granularity.ONE_MINUTE)
    df_trades = get_market_trades_df(db, trading_pair, start, end)
    generate_candle_chart(df_candles, target, save_html=True)
    generate_trade_counts_chart(df_trades, target, save_html=True)
    generate_trade_totals_chart(df_trades, target, save_html=True)

    # weekday analysis
    trading_pair = 'ARB-USD'
    start = datetime.datetime(year=2024, month=8, day=1, tzinfo=cb.LOCAL_TZ)
    end = datetime.datetime(year=2025, month=2, day=1, tzinfo=cb.LOCAL_TZ) - datetime.timedelta(seconds=1)
    target = AnalysisTarget(trading_pair=trading_pair, start_date=start, end_date=end)

    df_candles = get_candles_df(db, trading_pair=trading_pair, start_date=start, end_date=end, granularity=cb.Granularity.ONE_DAY)
    generate_price_direction_counts_chart(df_candles, target, save_html=True)
    generate_percent_diff_totals_chart(df_candles, target, save_html=True)
    generate_price_change_avg_min_max_chart(df_candles, target, save_html=True)


if __name__=='__main__':
    main()