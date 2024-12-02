from coinbase.rest import RESTClient
from dotenv import dotenv_values
from json import dumps

config = dotenv_values(".env")
coinbaseAPIKey = config["COINBASE_API_KEY"]
coinbaseAPISecret = config["COINBASE_API_SECRET"]

client = RESTClient(api_key=coinbaseAPIKey, api_secret=coinbaseAPISecret)

portfolios_response = client.get_portfolios()
portfolios = portfolios_response.to_dict()["portfolios"]
print(dumps(portfolios, indent=2))

default_portfolio = None
for portfolio in portfolios:
    portfolio_bd_response = client.get_portfolio_breakdown(portfolio_uuid=portfolio["uuid"])
    portfolio_bd = portfolio_bd_response.to_dict()
    #print(dumps(portfolio_bd, indent=2))

    if portfolio["type"] == "DEFAULT":
        default_portfolio = portfolio_bd["breakdown"]



print()

spot_positions = default_portfolio["spot_positions"]
print("Positions:")
# TODO: import panda and format data into table
for position in spot_positions:
    asset_name: str = position["asset"]
    curr_value: float = float(position["cost_basis"]["value"])
    value_currency: str = position["cost_basis"]["currency"]
    amount: float = position["total_balance_fiat"]
    print(asset_name, curr_value, value_currency, amount, sep='\t')
print()