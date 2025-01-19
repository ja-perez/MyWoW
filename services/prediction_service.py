import datetime
import os
from typing import Optional

import utils
import services.coinbase as cb
from services.coinbase import Granularity
from coinbase.rest import RESTClient # type: ignore
from database import Database

from models.prediction import Prediction

class PredictionService:
    def __init__(self, client: RESTClient = None, db: Database | None = None):
        self.client = client if client else cb.get_client()
        self.db = db if db else Database()
        
        self.prediction_data_path = utils.get_path_from_data_dir("dummy_data.csv")
        self.prediction_results_path = utils.get_path_from_data_dir("dummy_results.csv")

        self.predictions_updated = False

    def get_predictions(self, start_index: int = 0, limit: int = 10) -> list[Prediction]:
        # TODO: See ui/menu.py/Menu/selectprediction
        if self.db.table_exists('predictions'):
            # use start_index to offset limit to return next set of rows
            limit = -1 if limit < 0 else start_index + limit
            res = self.db.get_rows('predictions', limit=limit)
            predictions = [Prediction(data=result_data) for result_data in res[start_index:]]
            return predictions
        else:
            file_rows = utils.get_csv_data_from_file(self.prediction_data_path)
            data = []
            end_index = len(file_rows) if limit < 0 else start_index + limit
            for row in file_rows[start_index:end_index]:
                pred_data = {
                    "symbol": row[0],
                    "trading_pair": row[1],
                    "start_date": row[2],
                    "end_date": row[3],
                    "start_price": float(row[4]),
                    "end_price": float(row[5]),
                    "buy_price": float(row[6]),
                    "sell_price": float(row[7])
                }
                data.append(Prediction(pred_data))
            return data

    def get_results(self, start_index: int = 0, limit: int = 10) -> list[Prediction]:
        # TODO: See ui/menu.py/Menu/selectprediction
        if self.db.table_exists('results'):
            limit = -1 if limit < 0 else start_index + limit
            res = self.db.get_rows('results', limit=limit)
            results = [Prediction(data=result_data) for result_data in res]
            return results 
        else:
            file_rows = utils.get_csv_data_from_file(self.prediction_results_path)
            data = []
            end_index = len(file_rows) if limit < 0 else start_index + limit
            for row in file_rows[start_index: end_index]:
                result_data = {
                    "symbol": row[0],
                    "trading_pair": row[1],
                    "start_date": row[2],
                    "end_date": row[3],
                    "start_price": float(row[4]),
                    "end_price": float(row[5]),
                    "buy_price": float(row[6]),
                    "sell_price": float(row[7]),
                    "close_price": float(row[8]),
                }
                data.append(Prediction(result_data))
            return data

    def update_predictions(self):
        if self.predictions_updated:
            return

        todays_date = datetime.date.today()
        if self.db.table_exists('predictions'):

            predictions = [Prediction(data=pred_data) for pred_data in self.db.get_rows(table_name='predictions', limit=-1)]
            for pred in predictions:
                end_date = pred.end_date
                start_date = pred.start_date

                candles: list[dict] = self.get_candles(pred.trading_pair, start_date, end_date)
                for candle in candles:
                    self.upload_candle(pred.trading_pair, candle)

                if todays_date > end_date.date():
                    candles.sort(key=lambda x: x['date'], reverse=True)
                    close_price = candles[0]['close']
                    pred.close_price = close_price
                    self.add_result(pred.get_values(is_result=True))
                    self.remove_prediction(pred)
        else:
            predictions = self.get_predictions(limit=-1)
            new_data = []
            for pred in predictions:
                if todays_date > pred.end_date.date():
                    candle = cb.get_asset_candles(self.client, pred.trading_pair, Granularity.ONE_DAY, pred.start_date, pred.end_date)
                    pred.close_price = float(candle[0]['close'])
                    utils.add_data_to_csv_file(self.prediction_results_path, pred.to_json())
                else:
                    new_data.append(pred)
            utils.write_many_data_to_csv_file(self.prediction_data_path, new_data)

        self.predictions_updated = True

    def add_result(self, result_data: dict):
        if self.db.table_exists('results'):
            self.db.insert_one(table_name='results', values=result_data)

    def add_prediction(self, prediction: Prediction):
        if self.db.table_exists('predictions'):
            self.db.insert_one(table_name='predictions', values=prediction.get_values())
        else:
            utils.add_dict_to_csv_file(self.prediction_data_path, prediction.to_json())

        self.predictions_updated = False

    def remove_prediction(self, pred_to_remove: Prediction):
        if self.db.table_exists('predictions'):
            self.db.delete_where(table_name='predictions', values={'symbol':pred_to_remove.symbol, 'start_date':pred_to_remove.view_start_date()})
        else:
            curr_predictions: list[Prediction] = self.get_predictions(limit=-1)
            new_data = []
            for pred in curr_predictions:
                if pred.symbol == pred_to_remove.symbol and pred.start_date == pred_to_remove.start_date:
                    continue
                new_data.append(pred.to_json())
            utils.write_many_data_to_csv_file(self.prediction_data_path, new_data)

    def get_candles(self, trading_pair: str, start_date: datetime.datetime, end_date: datetime.datetime) -> list[dict]:
        if self.db.table_exists('candles'):
            where_conditions = self.db.build_where(
                eq={
                    'trading_pair':f"'{trading_pair}'"
                },
                btwn={
                    'date':{
                        'min':f"'{datetime.datetime.strftime(start_date, "%Y-%m-%d")}'",
                        'max':f"'{datetime.datetime.strftime(end_date, "%Y-%m-%d")}'",
                    }
                })

            candles = self.db.get_rows('candles', where_statement=where_conditions)
        else:
            output_filename = f'{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}_{trading_pair}_candles.json'
            output_file_path = utils.get_path_from_data_dir(output_filename)

            if os.path.exists(output_file_path):
                candles = utils.get_dict_data_from_file(output_file_path)
            else:
                candles = cb.get_asset_candles(self.client, trading_pair, Granularity.ONE_DAY, start_date, end_date)
                utils.write_dict_data_to_file(output_file_path, candles)

        range_high = float('-inf')
        range_low = float('inf')
        for candle in candles:
            range_high = max(range_high, float(candle['high']))
            range_low = min(range_low, float(candle['low']))

        for i, candle in enumerate(candles):
            candle = {
                'start': int(candle['start']),
                'low': float(candle['low']),
                'high': float(candle['high']),
                'open': float(candle['open']),
                'close': float(candle['close']),
                'volume': float(candle['volume']),
            }
            candle['date'] = utils.unix_to_datetime_string(candle['start'])
            candle['range_high'] = range_high
            candle['range_low'] = range_low

            candles[i] = candle

        return candles

    def upload_candle(self, trading_pair: str, candle: dict):
        start = int(candle['start'])
        date = datetime.datetime.fromtimestamp(start).strftime("%Y-%m-%d")
        candle_open = float(candle['open'])
        high = float(candle['high'])
        low = float(candle['low'])
        close = float(candle['close'])
        volume = float(candle['volume'])
        symbol = trading_pair.split('-')[0]
        id = f"{symbol}-{start}"

        insert_data = [
            id,
            date,
            start,
            trading_pair,
            candle_open,
            high,
            low,
            close,
            volume,
        ]
        self.db.insert_one(values=insert_data, table_name='candles')

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