import services.coinbase as cb
from coinbase.rest import RESTClient # type: ignore
from typing import Optional

from database import Database

class PortfolioService:
    def __init__(self, client: RESTClient = None, db: Optional[Database] = None):
        self.client = client if client else cb.get_client()
        self.db = db if db else Database()

    def get_portfolio(self):
        default_portfolio = cb.get_default_portfolio(self.client)

        return default_portfolio