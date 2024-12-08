from coinbase.rest import RESTClient
from dotenv import dotenv_values
from portfolio import Granularity
import utils
import datetime

# Load environment variables
config = dotenv_values(".env")
coinbaseAPIKey = config["COINBASE_API_KEY"]
coinbaseAPISecret = config["COINBASE_API_SECRET"]

client = RESTClient(api_key=coinbaseAPIKey, api_secret=coinbaseAPISecret)

def get_default_portfolio():
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
 
def get_asset_candles(product_id: str, granularity: str, start: datetime.datetime, end: datetime.datetime, limit= int | None):
    start_unix = str(int(start.timestamp()))
    end_unix = str(int(end.timestamp()))
    if (not Granularity.verify(granularity)):
        raise ValueError("Granularity must be one of the following: ONE_MINUTE, FIVE_MINUTES, FIFTEEN_MINUTES, THIRTY_MINUTES, ONE_HOUR, TWO_HOUR, SIX_HOUR, ONE_DAY")
    candles_response = client.get_candles(product_id=product_id, start=start_unix, end=end_unix, granularity=granularity, limit=limit)
    candles = candles_response.to_dict()["candles"]
    # timestamp = int(datetime.datetime.now().timestamp())
    # utils.write_data_to_file(utils.get_path_from_cwd(f"{product_id}_candles_{timestamp}.json"), candles)
    return candles

def main():
    candles = utils.get_data_from_file(utils.get_path_from_log_dir("candles.json"))["candles"]

    for candle in candles:
        date: str = utils.unix_to_date_string(int(candle["start"]))
        high: str = candle["high"]
        weekday: str = utils.get_weekday(datetime.datetime.fromtimestamp(int(candle["start"])))
        print(f"{date} {weekday}: {high}")

if __name__=="__main__":
    main()