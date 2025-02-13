import datetime
from typing import Optional
from coinbase.rest import RESTClient # type: ignore
from os import path

import services.coinbase_services as cb
from database import Database
from models.portfolio import Portfolio
import utils.utils

class PortfolioService:
    def __init__(self, client: RESTClient = None, db: Optional[Database] = None):
        self.client = client if client else cb.get_client()
        self.db = db if db else Database('mywow.db')

        self.cache_path = utils.get_path_from_data_dir('portfolios.json')

    def get_portfolio(self):
        if path.exists(self.cache_path):
            file_data = utils.get_dict_data_from_file(self.cache_path)

            last_updated = datetime.datetime.strptime(file_data['last_updated'], '%Y-%m-%d')
            if last_updated.date() == datetime.date.today():
                return Portfolio(file_data)

        default_portfolio = cb.get_default_portfolio(self.client)
        default_portfolio['last_updated'] = datetime.date.today().strftime('%Y-%m-%d')
        utils.write_dict_data_to_file(self.cache_path, default_portfolio) 
        portfolio = Portfolio(default_portfolio)
        return portfolio