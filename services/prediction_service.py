import datetime
import os

import utils
import Coinbase as cb
from portfolio import Granularity


class PredictionService:
    def __init__(self):
        self.client = cb.get_client()
        
        self.prediction_data_path = utils.get_path_from_data_dir("dummy_data.csv")
        self.prediction_results_path = utils.get_path_from_data_dir("dummy_results.csv")

    def get_predictions(self) -> list[dict]:
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

    def get_results(self) -> list[dict]:
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
                "actual_end_price": float(row[8]),
            })
        return data

    def update_predictions(self):
        file_data = self.get_predictions()
        todays_date = datetime.date.today()

        new_data = []
        for pred in file_data:
            end_date = datetime.datetime.strptime(pred["end_date"], "%Y-%m-%d")
            start_date = datetime.datetime.strptime(pred["start_date"], "%Y-%m-%d")
            if todays_date > end_date.date():   # want to update preds day after end date
                trading_pair = pred["trading_pair"]
                candle = cb.get_asset_candles(self.client, trading_pair, Granularity.ONE_DAY, start_date, end_date) 
                pred_result = pred.copy()
                pred_result["actual_end_price"] = float(candle[0]["close"])
                utils.add_data_to_csv_file(self.prediction_results_path, pred_result)
            else:
                new_data.append(pred)
        utils.write_many_data_to_csv_file(self.prediction_data_path, new_data)

    def add_prediction(self, prediction: dict):
        ordered_prediction = {
            "symbol": prediction["symbol"],
            "trading_pair": prediction["trading_pair"],
            "start_date": prediction["start_date"],
            "end_date": prediction["end_date"],
            "start_price": prediction["start_price"],
            "end_price": prediction["end_price"],
            "buy_price": prediction["buy_price"],
            "sell_price": prediction["sell_price"],
        }
        utils.add_data_to_csv_file(self.prediction_data_path, ordered_prediction)

    def remove_prediction(self, symbol: str, start_date: str):
        file_data = self.get_predictions()

        new_data = []
        for pred in file_data:
            if pred["symbol"] == symbol and pred["start_date"] == start_date:
                continue
            new_data.append(pred)

        utils.write_many_data_to_csv_file(self.prediction_data_path, new_data)

    def get_candles(self, trading_pair: str, start_date: datetime.datetime, end_date: datetime.datetime) -> list[dict]:
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
                'volume': int(candle['volume']),
            }
            candle['date'] = utils.unix_to_datetime_string(candle['start'])
            candle['range_high'] = range_high
            candle['range_low'] = range_low

            candles[i] = candle

        return candles

def calculateBreakEvenPrice(P1: float, Q1: float, Q2: float):
    GR = (Q2 - Q1) / Q1
    P3 = P1 * (1 + GR)
    # print("\t", P1, Q1, Q2)
    # print("\t\t", GR, P3, "\n")
    return P3

def calculateBreakEvenQuantity(P1: float, P2: float, L1: float):
    GR = (P2 - P1) / P1
    Q4 = L1 / GR
    # print("\t", P1, P2, L1)
    # print("\t\t", GR, Q4, "\n")
    return Q4

def calculateRepositionGain(P1: float, P2: float, Q1: float):
    GR = (P2 - P1) / P1
    return Q1 * GR

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
def analysis():
    initial_price = 2.65
    initial_quantity = 50.11

    final_price = 2.0
    final_quantity = initial_quantity * (1 + (final_price - initial_price) / initial_price)
    loss = initial_quantity - final_quantity

    print(f"Initial Price: {initial_price:<15} Initial Quantity: {initial_quantity:<15.2f}")
    print(f"Final Price: {final_price:<15}\tFinal Quantity: {final_quantity:<15.8f}")
    print(f"Loss: {loss}")
    print()
    print(f"Break Even Price: {calculateBreakEvenPrice(final_price, final_quantity, initial_quantity):.15f}")
    print(f"Break Even Quantity: {calculateBreakEvenQuantity(final_price, initial_price, loss):.8f}")
    repoGain = calculateRepositionGain(final_price, initial_price, initial_quantity)
    print(f"Reposition Gain: {repoGain - loss:.8f} ({(repoGain - loss)/initial_quantity * 100:.2f}%)")