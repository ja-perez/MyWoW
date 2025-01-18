import datetime
import os
from typing import Any

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

    def get_predictions(self, to_json=False) -> list[dict] | list[Prediction]:
        # TODO: See ui/menu.py/Menu/selectprediction
        if self.db.table_exists('predictions'):
            res = self.db.get_rows('predictions', limit=10)
            predictions = [Prediction(data=result_data) for result_data in res]

            if to_json:
                return [pred.to_json() for pred in predictions]
            else:
                return predictions
        else:
            file_data = utils.get_csv_data_from_file(self.prediction_data_path)
            data = []
            for row in file_data:
                data.append({
                    "symbol": row[0],
                    "trading_pair": row[1],
                    "start_date": row[2],
                    "end_date": row[3],
                    "start_price": float(row[4]),
                    "end_price": float(row[5]),
                    "buy_price": float(row[6]),
                    "sell_price": float(row[7])
                })
            return data

    def get_results(self, to_json=False) -> list[Prediction] | list[dict]:
        # TODO: See ui/menu.py/Menu/selectprediction
        if self.db.table_exists('results'):
            res = self.db.get_rows('results', limit=10)
            results: list[Prediction] = [Prediction(data=result_data) for result_data in res]

            if to_json:
                return [result.to_json() for result in results]
            else:
                return results 
        else:
            file_data = utils.get_csv_data_from_file(self.prediction_results_path)
            data = []
            for row in file_data:
                data.append({
                    "symbol": row[0],
                    "trading_pair": row[1],
                    "start_date": row[2],
                    "end_date": row[3],
                    "start_price": float(row[4]),
                    "end_price": float(row[5]),
                    "buy_price": float(row[6]),
                    "sell_price": float(row[7]),
                    "close_price": float(row[8]),
                })
            return data

    def update_predictions(self):
        if self.predictions_updated:
            return

        todays_date = datetime.date.today()
        if self.db.table_exists('predictions'):
            predictions = [Prediction(data=pred_data) for pred_data in self.db.get_rows(table_name='predictions', limit=-1)]
            for prediction in predictions:
                end_date = prediction.end_date
                start_date = prediction.start_date
                if todays_date > end_date.date():
                    candles: list[dict] = self.get_candles(prediction.trading_pair, start_date, end_date)
                    candles.sort(key=lambda x: x['date'], reverse=True)
                    close_price = candles[0]['close']
                    prediction.close_price = close_price
                    self.add_result(prediction.get_values())
                    self.remove_prediction(prediction)
        else:
            predictions = self.get_predictions()
            new_data = []
            for pred in predictions:
                end_date = datetime.datetime.strptime(pred["end_date"], "%Y-%m-%d")
                start_date = datetime.datetime.strptime(pred["start_date"], "%Y-%m-%d")
                if todays_date > end_date.date():   # want to update preds day after end date
                    trading_pair = pred["trading_pair"]
                    candle = cb.get_asset_candles(self.client, trading_pair, Granularity.ONE_DAY, start_date, end_date) 
                    pred_result = pred.copy()
                    pred_result["close_price"] = float(candle[0]["close"])
                    utils.add_data_to_csv_file(self.prediction_results_path, pred_result)
                else:
                    new_data.append(pred)
            utils.write_many_data_to_csv_file(self.prediction_data_path, new_data)

        self.predictions_updated = True

    def add_result(self, result_data: dict):
        if self.db.table_exists('results'):
            self.db.insert_one(table_name='results', values=result_data)

    def add_prediction(self, prediction_data: dict, use_model=False):
        if self.db.table_exists('predictions'):
            if use_model:
                prediction = Prediction(data=prediction_data)
                self.db.insert_one(table_name='predictions', values=prediction.get_values())
            else:
                symbol: str = prediction_data['symbol']
                start_date: datetime.datetime = prediction_data['start_date']
                end_date: datetime.datetime = prediction_data['end_date']
                prediction_data['prediction_id'] = f'{symbol}-{start_date.month}{start_date.day}{end_date.month}{end_date.day}-{start_date.year}'
                prediction_data['start_date'] = prediction_data["start_date"].strftime("%Y-%m-%d")
                prediction_data['end_date'] = prediction_data["end_date"].strftime("%Y-%m-%d")
                self.db.insert_one(table_name='predictions', values=prediction_data)
        else:
            ordered_prediction = {
                "symbol": prediction_data["symbol"],
                "trading_pair": prediction_data["trading_pair"],
                "start_date": prediction_data["start_date"].strftime("%Y-%m-%d"),
                "end_date": prediction_data["end_date"].strftime("%Y-%m-%d"),
                "start_price": prediction_data["start_price"],
                "end_price": prediction_data["end_price"],
                "buy_price": prediction_data["buy_price"],
                "sell_price": prediction_data["sell_price"],
            }
            utils.add_dict_to_csv_file(self.prediction_data_path, ordered_prediction)

        self.predictions_updated = False

    def remove_prediction(self, prediction: Prediction):
        if self.db.table_exists('predictions'):
            self.db.delete_where(table_name='predictions', values={'symbol':prediction.symbol, 'start_date':prediction.view_start_date()})
        else:
            file_data: Any = self.get_predictions()

            new_data = []
            for pred in file_data:
                if pred["symbol"] == prediction.symbol and pred["start_date"] == prediction.view_start_date():
                    continue
                new_data.append(pred)

            utils.write_many_data_to_csv_file(self.prediction_data_path, new_data)

    def get_candles(self, trading_pair: str, start_date: datetime.datetime, end_date: datetime.datetime) -> list[dict]:
        if self.db.table_exists('candles'):
            days_timedelta = min(end_date, datetime.datetime.today() - datetime.timedelta(days=1)) - start_date
            days = days_timedelta.days + 1
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
            
            if len(candles) < days:
                res = cb.get_asset_candles(self.client, trading_pair, Granularity.ONE_DAY, start_date, end_date)
                for candle in res:
                    self.upload_candle(trading_pair, candle)

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