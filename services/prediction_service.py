import datetime
import os
from typing import Optional
from coinbase.rest import RESTClient # type: ignore

import utils
import services.coinbase_services as cb
from services.coinbase_services import Granularity
from database.database import Database
from database.db_setup import MyWoWDatabase

from models.prediction import Prediction
from models.candles import Candle

class PredictionService:
    def __init__(self, client: Optional[RESTClient] = None, db: Optional[Database] = None, dbms: Optional[MyWoWDatabase] = None):
        self.client = client if client else cb.get_client()
        self.db = db if db else Database('mywow.db')
        self.dbms = dbms if dbms else MyWoWDatabase()
        
        self.prediction_data_path = utils.get_path_from_data_dir("local_predictions.csv")
        self.prediction_results_path = utils.get_path_from_data_dir("local_results.csv")

        self.predictions_updated = False
        self.update_predictions()

    def get_predictions(self, start_index: int = 0, limit: int = 10) -> list[Prediction]:
        start_index = 0 if start_index < 0 else start_index # TODO: Handle start_index being greater than count of predictions (predictions object? count query? TBD)
        limit = -1 if limit < 0 else start_index + limit # offsets limit as queryed records are those UPTO start_index + desired limit count
        result = self.dbms.get_items(table_name='predictions', start_index=start_index, limit=limit)
        return [Prediction(data=result_data) for result_data in result]

    def get_results(self, start_index: int = 0, limit: int = 10) -> list[Prediction]:
        start_index = 0 if start_index < 0 else start_index # TODO: Handle start_index being greater than count of predictions (predictions object? count query? TBD)
        limit = -1 if limit < 0 else start_index + limit # offsets limit as queryed records are those UPTO start_index + desired limit count
        result = self.dbms.get_items(table_name='results', start_index=start_index, limit=limit)
        return [Prediction(data=result_data) for result_data in result]

    def update_candles(self, prediction: Prediction):
        candles = cb.get_asset_candles(self.client, prediction.trading_pair, cb.Granularity.ONE_DAY, prediction.start_date, prediction.end_date)
        for candle_data in candles:
            candle = Candle(candle_data)
            self.db.insert_one(table_name='candles', values=candle.get_values())

    def update_predictions(self):
        if self.predictions_updated:
            return

        todays_date = datetime.date.today()
        predictions = self.get_predictions(limit=-1)
        for pred in predictions:
            self.update_candles(pred)
            candles = self.get_candles(pred.trading_pair, pred.start_date, pred.end_date)

            if todays_date > pred.end_date.date():
                candles.sort(key=lambda x: x.date, reverse=True)
                pred.close_price = candles[0].close_price
                self.add_result(pred)
                self.remove_prediction(pred)

        self.predictions_updated = True

    def add_result(self, result: Prediction):
        self.dbms.add_item(table_name='results', values=result.result_upload())

    def add_prediction(self, prediction: Prediction):
        self.dbms.add_item(table_name='predictions', values=prediction.prediction_upload())
        self.update_predictions()

    def remove_prediction(self, pred_to_remove: Prediction):
        self.dbms.remove_item(table_name='predictions', values={'symbol':pred_to_remove.symbol, 'start_date':pred_to_remove.view_start_date()})

    def get_candles(self, trading_pair: str, start_date: datetime.datetime, end_date: datetime.datetime) -> list[Candle]:
        where_statement = self.db.build_where(
            eq={
                'trading_pair':f"'{trading_pair}'"
            },
            btwn={
                'date':{
                    'min':f"'{datetime.datetime.strftime(start_date, "%Y-%m-%d")}'",
                    'max':f"'{datetime.datetime.strftime(end_date, "%Y-%m-%d")}'",
                }
            })
        rows = self.dbms.get_items(table_name='candles', where_statement=where_statement)

        if not rows:
            return []

        candles = [Candle(row) for row in rows]
        range_high = max(candles, key=lambda x:x.high_price).high_price
        range_low = min(candles, key=lambda x:x.low_price).low_price
        for candle in candles:
            candle.range_high = range_high
            candle.range_low = range_low

        return candles

class AnalysisService:
    # Break-even Analysis
    def calculateBreakEvenPrice(self, P1: float, Q1: float, Q2: float):
        GR = (Q2 - Q1) / Q1
        P3 = P1 * (1 + GR)
        # print("\t", P1, Q1, Q2)
        # print("\t\t", GR, P3, "\n")
        return P3

    def calculateBreakEvenQuantity(self, P1: float, P2: float, L1: float):
        GR = (P2 - P1) / P1
        Q4 = L1 / GR
        # print("\t", P1, P2, L1)
        # print("\t\t", GR, Q4, "\n")
        return Q4

    def calculateRepositionGain(self, P1: float, P2: float, Q1: float):
        GR = (P2 - P1) / P1
        return Q1 * GR

    def genBreakEvenAnalysis(self):
        """
        Position with loss (PWL):
        # P2 < P1 : Sold at lower price than bought
        # Q2 < Q1 : Value sold is less than value bought
            Buy @ P1 with quantity value Q1
            Sell @ P2 with quantity value Q2

            L1 = Loss Value = Q2 - Q1
            LR = Loss Rate = L1 / Q1


        Calculate required price to break even with initial position Q2:
            Buy @ P2 with quantity value Q2 == Q1 - L1
            Sell @ P3 with quantity value Q3 == Q2 + L1 == Q1

            G1 = Gain Value = Q3 - Q2 == L1
            GR = Gain Rate = G1 / Q2

            P3 = P2 (1 + GR)


        Calculate required quantity to break even with final price P1:
            Buy @ P2 with quantity value Q4
            Sell @ P1 with quantity value Q5 == Q4 + L1

            G1 = Gain Value = Q5 - Q4 == L1
            GR = Gain Rate = G1 / Q4 == (P1 - P2) / P2

            Q4 = G1 / GR == L1 / GR
        """
        initial_price = 2.65
        initial_quantity = 50.11

        final_price = 2.0
        final_quantity = initial_quantity * (1 + (final_price - initial_price) / initial_price)
        loss = initial_quantity - final_quantity

        print(f"Initial Price: {initial_price:<15} Initial Quantity: {initial_quantity:<15.2f}")
        print(f"Final Price: {final_price:<15}\tFinal Quantity: {final_quantity:<15.8f}")
        print(f"Loss: {loss}")
        print()
        print(f"Break Even Price: {self.calculateBreakEvenPrice(final_price, final_quantity, initial_quantity):.15f}")
        print(f"Break Even Quantity: {self.calculateBreakEvenQuantity(final_price, initial_price, loss):.8f}")
        repoGain = self.calculateRepositionGain(final_price, initial_price, initial_quantity)
        print(f"Reposition Gain: {repoGain - loss:.8f} ({(repoGain - loss)/initial_quantity * 100:.2f}%)")