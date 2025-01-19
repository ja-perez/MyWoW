from coinbase.rest import RESTClient # type: ignore
from coinbase.wallet.client import Client # type: ignore
from dotenv import dotenv_values
import utils
import datetime

class Granularity:
    ONE_MINUTE = 'ONE_MINUTE'
    FIVE_MINUTES = 'FIVE_MINUTES'
    FIFTEEN_MINUTES = 'FIFTEEN_MINUTES'
    THIRTY_MINUTES = 'THIRTY_MINUTES'
    ONE_HOU = 'ONE_HOUR'
    TWO_HOUR = 'TWO_HOUR'
    SIX_HOUR = 'SIX_HOUR'
    ONE_DAY = 'ONE_DAY'

    @staticmethod
    def verify(granularity: str) -> bool:
        return granularity in [Granularity.ONE_MINUTE, Granularity.FIVE_MINUTES, Granularity.FIFTEEN_MINUTES,
                              Granularity.THIRTY_MINUTES, Granularity.ONE_HOU, Granularity.TWO_HOUR, Granularity.SIX_HOUR,
                              Granularity.ONE_DAY]

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
 
def get_asset_candles(client: RESTClient, product_id: str, granularity: str, start: datetime.datetime, end: datetime.datetime, limit: int | None = None):
    start_unix = str(int(start.timestamp()))
    end_unix = str(int(end.timestamp()))
    if (not Granularity.verify(granularity)):
        raise ValueError("Granularity must be one of the following: ONE_MINUTE, FIVE_MINUTES, FIFTEEN_MINUTES, THIRTY_MINUTES, ONE_HOUR, TWO_HOUR, SIX_HOUR, ONE_DAY")
    candles_response = client.get_candles(product_id=product_id, start=start_unix, end=end_unix, granularity=granularity, limit=limit)
    candles = candles_response.to_dict()["candles"]
    for candle in candles:
        candle['trading_pair'] = product_id
    # timestamp = int(datetime.datetime.now().timestamp())
    # utils.write_data_to_file(utils.get_path_from_cwd(f"{product_id}_candles_{timestamp}.json"), candles)
    return candles

def main():
    client = get_client()

    try:
        candles = utils.get_dict_data_from_file(utils.get_path_from_log_dir("candles.json"))["candles"]

        for candle in candles:
            date: str = utils.unix_to_date_string(int(candle["start"]))
            high: str = candle["high"]
            weekday: str = utils.get_weekday(datetime.datetime.fromtimestamp(int(candle["start"])))
            print(f"{date} {weekday}: {high}")
    except Exception as _:
        print("Failed to read data from file: " + utils.get_path_from_log_dir("candles.json"))

if __name__=="__main__":
    main()