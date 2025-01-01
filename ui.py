import curses
import datetime

from inputhandling import InputHandler, QuitInputError, CancelInputError, RefreshInputError

class QuitMenuError(Exception):
    """Raised when user quits the program."""
    pass

class CancelMenuError(Exception):
    """Raised when the menu is cancelled"""
    pass

class RefreshMenuError(Exception):
    """Raised when the menu is refreshed"""

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

    def menu_output(func):
        def wrapper(self, *args, **kwargs):
            self.stdscr.clear()
            menu_title = ' '.join([self.title, '(press q to quit program, enter c to cancel input)', '\n\n'])
            if curses.has_colors() and curses.can_change_color():
                self.stdscr.addstr(0, 0, menu_title, curses.A_BOLD)
            else:
                self.stdscr.addstr(0, 0, menu_title)
            return func(self, *args, **kwargs)
        return wrapper

    def menu_exception_handler(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except QuitMenuError:
                raise
            except CancelMenuError:
                raise
        return wrapper

    def display_header(self, header: str):
        if curses.has_colors() and curses.can_change_color():
            self.stdscr.addstr(header, curses.A_UNDERLINE)
        else:
            self.stdscr.addstr(header.strip('\n'))
            y, x = self.stdscr.getyx()
            self.stdscr.move(y + 1, 0)
            self.stdscr.hline('-', x)
            self.stdscr.addstr(y + 2, 0, '\n')

    def display_options(self) -> int:
        y, _ = self.stdscr.getyx()
        y += 2
        self.stdscr.addstr(y - 1, 0, "Options:\n")

        options_count = len(self.options)
        choice = 0
        while True:
            self.stdscr.move(y, 0)
            for i, key in enumerate(self.options):
                self.stdscr.clrtoeol()
                option_output = f"{'>' if i == choice else ' '} {self.options[key]}\n"
                self.stdscr.addstr(option_output)

            try:
                updated_choice = self.input_handler.get_choice(choice, options_count)
                if updated_choice == curses.KEY_ENTER:
                    break
                else:
                    choice = updated_choice
            except QuitInputError:
                raise QuitMenuError

        keys = [key for key in self.options]
        return keys[choice]

    @menu_output
    def display_menu(self):
        self.action()

    @menu_exception_handler
    def results(self, data: list[dict]):
        header = f"{'Symbol':<10} {'Start Date':<15} {'Start Price':<15} {'End Price':<15} {'End Date':<15} {'Actual End Price':<15}\n"
        self.display_header(header)

        for pred in data:
            formattedPred = f"{pred['symbol']:<10} {pred['start_date']:<15} {pred['start_price']:<15.8f} {pred['end_price']:<15.8f} {pred['end_date']:<15} {pred['actual_end_price']:<15.8f}\n"
            self.stdscr.addstr(formattedPred)

        self.options = {
            "main": "Back to Main Menu",
            "quit": "Exit Program",
        }
        choice = self.display_options()
        if choice == 'main':
            return choice
        if choice == 'quit':
            raise QuitMenuError

    @menu_exception_handler
    def predictions(self, data: list[dict]):
        header = f"{'Symbol':<10} {'Start Date':<15} {'Start Price':<15} {'End Price':<15} {'End Date':<15} {'Buy Price':<15} {'Sell Price':<15}\n"
        self.display_header(header)

        for pred in data:
            formattedPred = f"{pred['symbol']:<10} {pred['start_date']:<15} {pred['start_price']:<15.8f} {pred['end_price']:<15.8f} {pred['end_date']:<15} {pred['buy_price']:<15.8f} {pred['sell_price']:<15.8f}\n"
            self.stdscr.addstr(formattedPred)

        self.options = {
            "main": "Back to Main Menu",
            "quit": "Exit Program",
        }
        choice = self.display_options()
        if choice == 'main':
            return choice
        if choice == 'quit':
            raise QuitMenuError

    @menu_exception_handler
    def addprediction(self):
        prediction = {}
        y, _ = self.stdscr.getyx()
        while True:
            self.stdscr.move(y, 0)
            self.stdscr.clrtobot()

            try:
                prediction["trading_pair"] = self.input_handler.get_input(
                    prompt="Trading Pair", input_type=str, example="BTC-USD", can_refresh=True).upper()
                prediction["symbol"] = prediction["trading_pair"].split("-")[0]

                prediction["start_date"] = self.input_handler.get_input(
                    prompt="Start Date", input_type=datetime.datetime, format="YYYYY-MM-DD", example="2024-01-01", default=datetime.datetime.now().strftime("%Y-%m-%d"), can_refresh=True)

                prediction["end_date"] = self.input_handler.get_input(
                    prompt="End Date", input_type=datetime.datetime, format="YYYYY-MM-DD", example="2024-01-01", validation=lambda x: x > prediction["start_date"], can_refresh=True)
                
                prediction["start_price"] = self.input_handler.get_input(
                    prompt="Start Price", input_type=float, example="35600.75", validation=lambda x:x > 0, can_refresh=True)

                prediction["end_price"] = self.input_handler.get_input(
                    prompt="End Price", input_type=float, example="35600.75", validation=lambda x:x > 0, can_refresh=True)

                prediction["buy_price"] = self.input_handler.get_input(
                    prompt="Buy Price", input_type=float, example="35600.75", validation=lambda x:x > 0, can_refresh=True)

                prediction["sell_price"] = self.input_handler.get_input(
                    prompt="Sell Price", input_type=float, example="35600.75", validation=lambda x:x > 0, can_refresh=True)

                summary_header = f"\nSummary of {prediction['symbol']} prediction:\n\t{'START':<15} {'END':<15}"
                summary_dates = f"\t{prediction['start_date']:<15} {prediction['end_date']:<15}"
                summary_prices = f"\t{prediction['start_price']:<15.8f} {prediction['end_price']:<15.8f}\n"
                summary_buysell_header = f"\t{'BUY':<15} {'SELL':<15}",
                summary_buysell_prices = f"\t{prediction['buy_price']:<15.8f} {prediction['sell_price']:<15.8f}\n",
                summary = '\n'.join([summary_header, summary_dates, summary_prices, summary_buysell_header, summary_buysell_prices])
                self.stdscr.addstr(summary)

                submit = self.input_handler.get_input(
                    prompt="Submit Prediction", input_type=str, format="y/n", default="n", can_refresh=True).lower()
                
                if submit == 'y':
                    return prediction

                self.options = {
                    "new": "Start new prediction",
                    "main": "Back to Main Menu",
                    "quit": "Exit Program"
                }
                choice = self.display_options()

                if choice == "main":
                    raise CancelMenuError
                if choice == "quit":
                    raise QuitMenuError
                if choice == "new":
                    raise RefreshMenuError

            except QuitInputError:
                raise QuitMenuError
            except QuitMenuError:
                raise
            except CancelInputError:
                return None
            except CancelMenuError:
                return None
            except RefreshInputError:
                continue
            except RefreshMenuError:
                continue

    @menu_exception_handler
    def editprediction(self, data: list[dict]):
        try:
            def symbol_validation(target_symbol: str):
                for pred in data:
                    pred_symbol: str = pred['symbol']
                    if target_symbol.lower() == pred_symbol.lower():
                        return True
                return False
            symbol = self.input_handler.get_input(prompt="Symbol", input_type=str, example="BTC/btc", validation=symbol_validation).upper()
            def date_validation(target_date: str):
                for pred in data:
                    if symbol == pred["symbol"] and target_date == pred["start_date"]:
                        return True
                return False
            start_date = self.input_handler.get_input(
                prompt="Start Date", input_type=datetime.datetime, format="YYYYY-MM-DD", example="2024-01-01", validation=date_validation)

            self.stdscr.addstr('\n')

            self.options = {
                "delete": "Remove Prediction",
                "main": "Main Menu",
                "quit": "Exit Program"
            }
            choice = self.display_options()

            if choice == "quit":
                raise QuitMenuError
            if choice == "main":
                raise CancelMenuError
            if choice == "delete":
                return (choice, symbol, start_date)

        except QuitInputError:
            raise QuitMenuError
        except QuitMenuError:
            raise
        except CancelInputError:
            return None
        except CancelMenuError:
            return None

    def displaypricechart(self, data: list[dict]):
        y_start, x_start = self.stdscr.getyx()

        self.stdscr.move(20, 30)

        y_end, x_end = self.stdscr.getyx()
        y_mid = y_start + ((y_end - y_start) // 2)
        x_mid = x_start + ((x_end - x_start) // 2)
        self.stdscr.addstr(y_mid, x_mid, "GRAPH HERE")

        self.stdscr.move(y_end + 1, 0)

    @menu_exception_handler
    def predictionoverview(self, predictionResult: dict, candles: list[dict]):
        # TODO: Refactor this to be more modular
        # TODO: Refactor this and add an option specifying which prediction to analyze
        # TODO: Refactor this and add a "carousel" for viewing multiple predictions by clicking [P]revious and [N]ext

        header = f'{"Symbol":<15} {"Start Date":<15} {"Closing Date":<15} {"Closing Price":<15} {"High":<15} {"Low":<15}\n'
        self.display_header(header)

        high = candles[0]['range_high']
        low = candles[0]['range_low']

        while True:
            trading_pair = predictionResult["trading_pair"]
            start_date = predictionResult["start_date"]
            end_date = predictionResult["end_date"]
            start_price = predictionResult["start_price"]
            end_price = predictionResult["end_price"]
            buy_price = predictionResult["buy_price"]
            sell_price = predictionResult["sell_price"]
            actual_end_price = predictionResult["actual_end_price"]
            self.stdscr.addstr(f"{trading_pair:<15} {start_date:<15} {end_date:<15} {actual_end_price:<15.8f} {high:<15.8f} {low:<15.8f}\n")
    
            self.displaypricechart(candles)
    
            price_header = f'{"START PRICE":<15} {"PRED. END PRICE":<20} {"BUY PRICE":<15} {"SELL PRICE":<15}\n'
            self.display_header(price_header)
            self.stdscr.addstr(f'{start_price:<15.8f} {end_price:<20.8f} {buy_price:<15.8f} {sell_price:<15.8f}\n')
    
            self.options = {
                "main": "Back to Main Menu",
                "quit": "Exit Program",
            }
            choice = self.display_options()

            if choice == 'main':
                break
            if choice == 'quit':
                raise QuitMenuError

        return choice