from coinbase.rest import RESTClient # type: ignore

class Position:
    def __init__(self, data: dict):
        self.symbol = data['asset']
        self.quantity = data['total_balance_crypto']
        self.value = data['total_balance_fiat']

        self.curr_price = self.value / self.quantity

        self.entry_value = data['average_entry_price']['value']
        self.entry_cost = data['cost_basis']['value']

class Portfolio:
    def __init__(self, data: dict):
        self.data: dict = data
        self.balance: dict = self.get_balance()
        self.active_positions = [Position(position) for position in self.data['spot_positions']]

    def get_balance(self):
        balance = self.data['portfolio_balances']
        formatted_balance = {
            'total': float(balance['total_balance']['value']),
            'cash': float(balance['total_cash_equivalent_balance']['value']),
            'crypto': float(balance['total_crypto_balance']['value']),
        }
        return formatted_balance