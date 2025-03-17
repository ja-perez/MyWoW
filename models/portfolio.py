currency_to_symbol = {
    'USD': '$',
    'USDC': '($)'
}

class Position:
    def __init__(self, data: dict):
        self.symbol = data['asset']
        self.asset_uuid = data['asset_uuid']
        self.currency = data['cost_basis']['currency']
        self.entry_price = float(data['average_entry_price']['value'])
        self.quantity = data['total_balance_crypto']
        self.value = float(data['total_balance_fiat'])
        self.unrealized_return = float(data['unrealized_pnl'])
        self.curr_price = float(self.value / self.quantity)

    def display_entry_price(self):
        if self.entry_price < 1 or self.entry_price > 1000:
            return f'{currency_to_symbol[self.currency]}{self.entry_price: .2e}'
        else:
            return f'{currency_to_symbol[self.currency]}{self.entry_price: .2f}'

    def display_value(self):
        return f'{currency_to_symbol[self.currency]}{self.value: .2f}'

    def display_unrealized_return(self):
        return f'{currency_to_symbol[self.currency]}{self.unrealized_return: .2f}'

    def display_curr_price(self):
        if self.curr_price < 1 or self.curr_price > 1000:
            return f'{currency_to_symbol[self.currency]}{self.curr_price: .2e}'
        else:
            return f'{currency_to_symbol[self.currency]}{self.curr_price: .2f}'

class Portfolio:
    def __init__(self, data: dict):
        self.data: dict = data
        self.balances: dict[str, dict] = self.get_balances()
        self.balance: dict[str, float] = {balance_type: self.balances[balance_type]['value'] for balance_type in self.balances} #!!!!# LEGACY VARIABLE USED BY CLI DISPLAY #!!!!#
        self.held_positions = [Position(position) for position in self.data['spot_positions']]

    def get_balances(self):
        balance = self.data['portfolio_balances']
        formatted_balance = {
            'total': {
                'value': float(balance['total_balance']['value']),
                'currency': balance['total_balance']['currency'],
            },
            'cash': {
                'value': float(balance['total_cash_equivalent_balance']['value']),
                'currency': balance['total_cash_equivalent_balance']['currency'],
            },
            'crypto': {
                'value': float(balance['total_crypto_balance']['value']),
                'currency': balance['total_crypto_balance']['currency'],
            }
        }
        return formatted_balance

    def get_total(self) -> float:
        return self.balances['total']['value']

    def get_cash(self) -> float:
        return self.balances['cash']['value']

    def get_crypto(self) -> float:
        return self.balances['crypto']['value']

    def display_balance(self, balance_type: str) -> str:
        value = self.balances[balance_type]['value']
        currency = self.balances[balance_type]['currency']
        return f"{currency_to_symbol[currency]}{value: .2f}"