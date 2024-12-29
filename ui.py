import curses
import datetime

from inputhandling import InputHandler

class Menu:
    def __init__(self, title: str, options: dict = None, stdscr: curses.window = None, action: callable = None, input_handler: InputHandler = None):
        self.title = title
        self.options = options
        self.stdscr = stdscr
        self.action = action
        self.input_handler = input_handler

    def display_options(self, custom_options: dict = None) -> int:
        y, _ = self.stdscr.getyx()
        y += 2 # 1 newline

        self.stdscr.addstr(y - 1, 0, self.title)

        if custom_options:
            options = custom_options
        else:
            options = self.options
        choice = 0
        while True:
            self.stdscr.move(y, 0)
            self.stdscr.clrtobot()

            for i, key in enumerate(options):
                option_output = f"{'>' if i == choice else ' '} {options[key]}"
                self.stdscr.addstr(y + i, 0, option_output)

            user_input = self.stdscr.getch()
            user_input_char = chr(user_input).lower()

            if user_input == curses.KEY_UP or user_input_char == 'w':
                choice = len(options) - 1 if choice - 1 < 0 else choice - 1
            elif user_input == curses.KEY_DOWN or user_input_char == 's':
                choice = (choice + 1) % len(options)

            if user_input_char == 'q':
                return "quit"
            elif user_input == curses.KEY_ENTER or user_input_char == '\n' or user_input == 10:
                break

        keys = [key for key in options.keys()]

        if self.action and not custom_options:
            self.action(keys[choice])

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

            options = {
                "main": "Back to Main Menu",
                "quit": "Exit Program",
            }
            self.stdscr.move(2 + len(data), 0)
            choice = self.display_options(options)

            if choice == "main" or choice == "quit":
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
                return choice

    def addprediction(self):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, "New Prediction (c to cancel, q to quit)")

        while True:
            self.stdscr.move(1, 0)
            self.stdscr.clrtobot()

            trading_pair = self.input_handler.get_input(self.stdscr, "Trading Pair", str, example="BTC-USD, ETH-USD")

            if trading_pair == None: # n for new (start process all over)
                continue
            if trading_pair == "quit" or trading_pair == "q":
                return "quit"
            trading_pair = trading_pair.upper()
            asset = trading_pair.split("-")[0]

            self.stdscr.move(2, 0)
            start_date = self.input_handler.get_input(self.stdscr, "Start Date", datetime.datetime, format="YYYY-MM-DD", example="2022-01-01", default=datetime.datetime.now().strftime("%Y-%m-%d"))
            if start_date == None:
                continue
            if start_date == "quit":
                return "quit"

            # TODO: Have default value be amount returned by api call for product candle
            self.stdscr.move(3, 0)
            end_date =self.input_handler.get_input(self.stdscr, "End Date", datetime.datetime, format="YYYY-MM-DD", example="2022-01-01")
            if end_date == None:
                continue
            if end_date == "quit":
                return "quit"

            self.stdscr.move(4, 0)
            start_price =self.input_handler.get_input(self.stdscr, "Start Price", float, example="100.00, 0.01")
            if start_price == None:
                continue
            if start_price == "quit":
                return "quit"

            self.stdscr.move(5, 0)
            end_price =self.input_handler.get_input(self.stdscr, f"End Price on {end_date}", float, example="100.00, 0.01")
            if end_price == None:
                continue
            if end_price == "quit":
                return "quit"

            self.stdscr.move(6, 0)
            buy_price = self.input_handler.get_input(self.stdscr, "Buy Price", float, example="10000.00, 0.01")
            if buy_price == None:
                continue
            if buy_price == "quit":
                return "quit"

            self.stdscr.move(7, 0)
            sell_price = self.input_handler.get_input(self.stdscr, "Sell Price", float, example="10000.00, 0.01")
            if sell_price == None:
                continue
            if sell_price == "quit":
                return "quit"

            self.stdscr.move(8, 0)
            summary = f"""Summary
            {asset} 
            {start_date:<15} {end_date:<15}
            {start_price:<15.8f} {end_price:<15.8f}
            BUY:{buy_price:<15.8f} SELL:{sell_price:<15.8f}
            """
            self.stdscr.addstr(summary)
            self.stdscr.move(13, 0)
            if (self.input_handler.get_input(self.stdscr, "Confirm?", str, default="n").lower() == "y"):
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
            val = self.input_handler.get_input(self.stdscr, "Symbol", str, example="BTC, ETH")
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
            val = self.input_handler.get_input(self.stdscr, "Start Date, in YYYY-MM-DD", str, example="2022-01-01")
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

    def predictionoverview(self, predictionResult: dict, prediction_service):
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

        candles = prediction_service.get_candles(trading_pair, datetime.datetime.strptime(start_date, "%Y-%m-%d"), datetime.datetime.strptime(end_date, "%Y-%m-%d"))

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

        options = {
            "main": "Back to Main Menu",
            "quit": "Exit Program",
        }
        while True:
            self.stdscr.move(graph_y_end + 3, 0)
            choice = self.display_options(options)

            if choice == "main" or choice == "quit":
                return choice