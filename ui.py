import curses
import datetime

from inputhandling import InputHandler

class QuitMenuError(Exception):
    """Raised when user quits the program."""
    pass

class CancelMenuError(Exception):
    """Raised when the menu is cancelled"""
    pass

class Menu:
    def __init__(self, title: str, options: dict = None, stdscr: curses.window = None, action: callable = None, input_handler: InputHandler = None):
        self.title = title
        self.options = options
        self.stdscr = stdscr
        self.action = action
        self.input_handler = input_handler
        self.has_options = True if options else False

        if not stdscr:
            raise Exception("stdscr cannot be None")

    def display_options(self) -> int:
        y, _ = self.stdscr.getyx()
        y += 2 # 1 newline
        self.stdscr.addstr(y - 1, 0, self.title)

        options_count = len(self.options)
        choice = 0
        while True:
            self.stdscr.move(y, 0)
            self.stdscr.clrtobot()

            for i, key in enumerate(self.options):
                option_output = f"{'>' if i == choice else ' '} {self.options[key]}"
                self.stdscr.addstr(y + i, 0, option_output)

            updated_choice = self.input_handler.get_choice(choice, options_count)
            if updated_choice == curses.KEY_ENTER:
                break
            if updated_choice == 'q':
                raise QuitMenuError
            choice = updated_choice

        keys = [key for key in self.options]
        return keys[choice]

    def display_interactive_menu(self):
        self.action()

    def listresults(self, data: list[dict]):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, "Prediction Results")

        header = f"{'Symbol':<10} {'Start Date':<15} {'Start Price':<15} {'End Price':<15} {'End Date':<15} {'Actual End Price':<15}"
        while True:
            self.stdscr.addstr(1, 0, header)
            for index, pred in enumerate(data):
                formattedPred = f"{pred['symbol']:<10} {pred['start_date']:<15} {pred['start_price']:<15.8f} {pred['end_price']:<15.8f} {pred['end_date']:<15} {pred['actual_end_price']:<15.8f}"
                self.stdscr.addstr(2 + index, 0, formattedPred)

            self.options = {
                "main": "Back to Main Menu",
                "quit": "Exit Program",
            }
            self.stdscr.move(2 + len(data), 0)
            choice = self.display_options()

            if choice == "main" or choice == "quit":
                break

        return choice

    def listpredictions(self, data: list[dict]):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, "Predictions")

        header = f"{'Symbol':<10} {'Start Date':<15} {'Start Price':<15} {'End Price':<15} {'End Date':<15} {'Buy Price':<15} {'Sell Price':<15}"
        while True:
            self.stdscr.addstr(1, 0, header)
            for index, pred in enumerate(data):
                formattedPred = f"{pred['symbol']:<10} {pred['start_date']:<15} {pred['start_price']:<15.8f} {pred['end_price']:<15.8f} {pred['end_date']:<15} {pred['buy_price']:<15.8f} {pred['sell_price']:<15.8f}"
                self.stdscr.addstr(2 + index, 0, formattedPred)

            self.options = {
                "main": "Back to Main Menu",
                "quit": "Exit Program",
            }
            self.stdscr.move(2 + len(data), 0)
            choice = self.display_options()

            if choice == "main" or choice == "quit":
                break

        return choice

    def addprediction(self):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, "New Prediction (c to cancel, q to quit)")

        while True:
            self.stdscr.move(1, 0)
            self.stdscr.clrtobot()

            trading_pair = self.input_handler.get_input("Trading Pair", str, example="BTC-USD, ETH-USD")

            if trading_pair == "n": # n for new (start process all over)
                continue
            if trading_pair == "quit" or trading_pair == None:
                return trading_pair
            trading_pair = trading_pair.upper()
            asset = trading_pair.split("-")[0]

            self.stdscr.move(2, 0)
            start_date = self.input_handler.get_input("Start Date", datetime.datetime, format="YYYY-MM-DD", example="2022-01-01", default=datetime.datetime.now().strftime("%Y-%m-%d"))
            if start_date == "n":
                continue
            if start_date == "quit" or start_date == None:
                return start_date

            # TODO: Have default value be amount returned by api call for product candle
            self.stdscr.move(3, 0)
            end_date =self.input_handler.get_input("End Date", datetime.datetime, format="YYYY-MM-DD", example="2022-01-01")
            if end_date == "n":
                continue
            if end_date == "quit" or end_date == None:
                return end_date

            self.stdscr.move(4, 0)
            start_price =self.input_handler.get_input("Start Price", float, example="100.00, 0.01")
            if start_price == "n":
                continue
            if start_price == "quit" or start_price == None:
                return start_price

            self.stdscr.move(5, 0)
            end_price =self.input_handler.get_input(f"End Price on {end_date}", float, example="100.00, 0.01")
            if end_price == "n":
                continue
            if end_price == "quit" or end_price == None:
                return end_price

            self.stdscr.move(6, 0)
            buy_price = self.input_handler.get_input("Buy Price", float, example="10000.00, 0.01")
            if buy_price == "n":
                continue
            if buy_price == "quit" or buy_price == None:
                return buy_price

            self.stdscr.move(7, 0)
            sell_price = self.input_handler.get_input("Sell Price", float, example="10000.00, 0.01")
            if sell_price == "n":
                continue
            if sell_price == "quit" or sell_price == None:
                return sell_price

            self.stdscr.move(8, 0)
            summary = f"""Summary
            {asset} 
            {start_date:<15} {end_date:<15}
            {start_price:<15.8f} {end_price:<15.8f}
            BUY:{buy_price:<15.8f} SELL:{sell_price:<15.8f}
            """
            self.stdscr.addstr(summary)
            self.stdscr.move(13, 0)
            if (self.input_handler.get_input("Confirm?", str, default="n").lower() == "y"):
                break
            else:
                return None

        pred = {
            "symbol": asset,
            "trading-pair": trading_pair,
            "start_date": start_date,
            "end_date": end_date,
            "start_price": start_price,
            "end_price": end_price,
            "buy_price": buy_price,
            "sell_price": sell_price
        }
        return pred

    def editprediction(self, data: list[dict]):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, "Edit Prediction (c to cancel, q to quit)")

        while True:
            self.stdscr.move(1, 0)
            self.stdscr.clrtoeol()
            val = self.input_handler.get_input(prompt="Symbol", input_type=str, example="BTC, ETH")
            if val == None or val == "quit":
                return val
            val = val.upper()
            found = False
            for pred in data:
                if pred["symbol"] == val:
                    found = True
                    break
            if found:
                self.stdscr.move(2, 0)
                self.stdscr.clrtobot()
                break
            self.stdscr.addstr(2, 0, f"Error: Symbol {val} not found")

        if val == None or val == "quit":
            return val
        predSymbol = val

        while True:
            self.stdscr.move(2, 0)
            self.stdscr.clrtoeol()
            val = self.input_handler.get_input("Start Date, in YYYY-MM-DD", str, example="2022-01-01")
            if val == None or val == "quit":
                return val
            found = False
            for pred in data:
                if pred["symbol"] == predSymbol and pred["start_date"] == val:
                    found = True
                    break
            if found:
                self.stdscr.move(3, 0)
                self.stdscr.clrtobot()
                break
            self.stdscr.addstr(3, 0, "Error: Start Date not found")
        
        if val == None or val == "quit":
            return val
        predStartDate = val
        
        return predSymbol, predStartDate

    def displaypricechart(self):
        y_start, x_start = self.stdscr.getyx()

        self.stdscr.move(20, 30)

        y_end, x_end = self.stdscr.getyx()
        y_mid = y_start + ((y_end - y_start) // 2)
        x_mid = x_start + ((x_end - x_start) // 2)
        self.stdscr.addstr(y_mid, x_mid, "GRAPH HERE")

        self.stdscr.move(y_end, x_end)

    def predictionoverview(self, predictionResult: dict, candles: list[dict]):
        # TODO: Refactor this to be more modular
        # TODO: Refactor this and add an option specifying which prediction to analyze
        # TODO: Refactor this and add a "carousel" for viewing multiple predictions by clicking [P]revious and [N]ext
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, "Prediction Analysis")

        trading_pair = predictionResult["trading-pair"]
        start_date = predictionResult["start_date"]
        end_date = predictionResult["end_date"]
        start_price = predictionResult["start_price"]
        end_price = predictionResult["end_price"]
        buy_price = predictionResult["buy_price"]
        sell_price = predictionResult["sell_price"]
        actual_end_price = predictionResult["actual_end_price"]

        high = -1.0
        low = 99999999999999999.9
        for candle in candles:
            high = max(high, float(candle["high"]))
            low = min(low, float(candle["low"]))

        self.stdscr.addstr(1, 0, f"{"Symbol":<15} {"Start Date":<15} {"Closing Date":<15} {"Closing Price":<15} {"High":<15} {"Low":<15}")
        self.stdscr.addstr(2, 0, f"{trading_pair:<15} {start_date:<15} {end_date:<15} {actual_end_price:<15.8f} {high:<15.8f} {low:<15.8f}")

        self.stdscr.move(3, 0)
        self.displaypricechart()
        graph_y_end, _ = self.stdscr.getyx()

        self.stdscr.addstr(graph_y_end + 1, 0, f"{"START PRICE":<15} {"PRED. END PRICE":<20} {"BUY PRICE":<15} {"SELL PRICE":<15}")
        self.stdscr.addstr(graph_y_end + 2, 0, f"{start_price:<15.8f} {end_price:<20.8f} {buy_price:<15.8f} {sell_price:<15.8f}")

        self.options = {
            "main": "Back to Main Menu",
            "quit": "Exit Program",
        }
        while True:
            self.stdscr.move(graph_y_end + 3, 0)
            choice = self.display_options()

            if choice == "main" or choice == "quit":
                break
        
        return choice