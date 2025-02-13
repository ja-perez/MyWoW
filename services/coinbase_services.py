from coinbase.rest import RESTClient # type: ignore
from coinbase.wallet.client import Client # type: ignore
from typing import Optional
from dotenv import dotenv_values
from math import ceil
import datetime

CANDLES_LIMIT_MAX = 350
LOCAL_TZ = datetime.datetime.now().astimezone().tzinfo

class Granularity:
    ONE_MINUTE = 'ONE_MINUTE'
    FIVE_MINUTES = 'FIVE_MINUTES'
    FIFTEEN_MINUTES = 'FIFTEEN_MINUTES'
    THIRTY_MINUTES = 'THIRTY_MINUTES'
    ONE_HOUR = 'ONE_HOUR'
    TWO_HOUR = 'TWO_HOUR'
    SIX_HOUR = 'SIX_HOUR'
    ONE_DAY = 'ONE_DAY'

    seconds = {
        ONE_MINUTE: 60,
        FIVE_MINUTES: 5 * 60,
        FIFTEEN_MINUTES: 15 * 60,
        THIRTY_MINUTES: 30 * 60,
        ONE_HOUR: 3600,
        TWO_HOUR: 2 * 3600,
        SIX_HOUR: 6 * 3600,
        ONE_DAY: 24 * 3600
    }

    @staticmethod
    def verify(granularity: str) -> bool:
        return granularity in [Granularity.ONE_MINUTE, Granularity.FIVE_MINUTES, Granularity.FIFTEEN_MINUTES,
                              Granularity.THIRTY_MINUTES, Granularity.ONE_HOUR, Granularity.TWO_HOUR, Granularity.SIX_HOUR,
                              Granularity.ONE_DAY]

    @staticmethod
    def to_seconds(granularity: str) -> int:
        return Granularity.seconds[granularity]
    
    @staticmethod
    def get_count_from_granularity(start: datetime.datetime, end: datetime.datetime, granularity: str) -> int:
        time_delta = end - start
        time_delta_seconds = time_delta.seconds + time_delta.days * 24 * 3600

        return ceil(time_delta_seconds / Granularity.to_seconds(granularity=granularity))

def get_client(dotenv_path: str = ".env") -> RESTClient:
    # Load environment variables
    config = dotenv_values(dotenv_path)
    coinbaseAPIKey = config["COINBASE_API_KEY"]
    coinbaseAPISecret = config["COINBASE_API_SECRET"]

    client = RESTClient(api_key=coinbaseAPIKey, api_secret=coinbaseAPISecret)
    return client

def get_wallet_client(dotenv_path: str = ".env") -> Client:
    # Load environment variables
    config = dotenv_values(dotenv_path)
    coinbaseAPIKey = config["COINBASE_API_KEY"]
    coinbaseAPISecret = config["COINBASE_API_SECRET"]

    client = Client(api_key=coinbaseAPIKey, api_secret=coinbaseAPISecret)
    return client

def get_default_portfolio(client: RESTClient):
    portfolios_response = client.get_portfolios()
    portfolios = portfolios_response.to_dict()["portfolios"]

    for portfolio in portfolios:
        portfolio_bd_res = client.get_portfolio_breakdown(portfolio_uuid=portfolio["uuid"])
        portfolio_bd = portfolio_bd_res.to_dict()["breakdown"]
        #timestamp = int(datetime.datetime.now().timestamp())
        #utils.write_data_to_file(utils.get_path_from_cwd(f"portfolios_{timestamp}.json"), portfolio_bd)

        if portfolio["type"] == "DEFAULT":
            default_portfolio = portfolio_bd
    return default_portfolio
 
def get_asset_candles(client: RESTClient, product_id: str, granularity: str, start: datetime.datetime, end: datetime.datetime, limit: int = CANDLES_LIMIT_MAX):
    if (not Granularity.verify(granularity)):
        raise ValueError("Granularity must be one of the following: ONE_MINUTE, FIVE_MINUTES, FIFTEEN_MINUTES, THIRTY_MINUTES, ONE_HOUR, TWO_HOUR, SIX_HOUR, ONE_DAY")
    candles: list = []
    base_end_time = end + datetime.timedelta(seconds=1)
    while True:
        if Granularity.get_count_from_granularity(start, end, granularity) > CANDLES_LIMIT_MAX:
            end = min(start + datetime.timedelta(seconds=Granularity.to_seconds(granularity) * CANDLES_LIMIT_MAX), base_end_time)

        start_unix = str(int(start.timestamp()))
        end_unix = str(int(end.timestamp()))

        res = client.get_candles(product_id=product_id, start=start_unix, end=end_unix, granularity=granularity, limit=None)
        curr_candles = res.to_dict()['candles']
        for candle in curr_candles:
            candle['trading_pair'] = product_id
            candle['granularity'] = granularity
        candles = curr_candles + candles 

        if Granularity.get_count_from_granularity(start, end, granularity) < limit:
            break
        else:
            start = end
            end = base_end_time

    # utils.write_data_to_file(utils.get_path_from_cwd(f"{product_id}_candles_{timestamp}.json"), candles)
    return candles

def fetch_market_trades(client: RESTClient, product_id: str, start_time: datetime.datetime, end_time: datetime.datetime, limit: int):
    market_trades: list = []
    while start_time < end_time:
        start_unix = str(int(start_time.timestamp()))
        end_unix = str(int(end_time.timestamp()))

        res = client.get_market_trades(product_id=product_id, limit=limit, start=start_unix, end=end_unix)
        curr_market_trades = res.to_dict()['trades']
        for market_trade in curr_market_trades:
            market_trade['time'] = datetime.datetime.fromisoformat(market_trade['time']).astimezone(LOCAL_TZ).isoformat()
        market_trades = curr_market_trades + market_trades

        if len(res['trades']) < limit:
            break

        end_time = datetime.datetime.fromisoformat(min(curr_market_trades, key=lambda x: x['time'])['time']).astimezone(LOCAL_TZ)
        
    return market_trades

def fetch_market_trade_candles(client: RESTClient, product_id: str, start_time: datetime.datetime, end_time: datetime.datetime, limit: int = CANDLES_LIMIT_MAX):
    candles = get_asset_candles(client, product_id=product_id, granularity=Granularity.ONE_MINUTE, start=start_time, end=end_time, limit=limit)
    return candles

def main():
    client = get_client()

if __name__=="__main__":
    main()
    pass