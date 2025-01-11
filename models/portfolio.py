from coinbase.rest import RESTClient # type: ignore

class Portfolio:
    def __init__(self, data: dict):
        self.data: dict = data
        self.balance: dict = self.get_balance()

    def get_balance(self):
        balance = self.data['portfolio_balances']
        formatted_balance = {
            'total': float(balance['total_balance']['value']),
            'cash': float(balance['total_cash_equivalent_balance']['value']),
            'crypto': float(balance['total_crypto_balance']['value']),
        }
        return formatted_balance