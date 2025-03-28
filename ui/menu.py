import curses
import datetime
from typing import Callable, Optional, Any

from inputhandling import InputHandler, QuitInputError, CancelInputError, RefreshInputError, NextPageException, PreviousPageException
from models.prediction import Prediction, MissingDataError, InvalidDataError
from models.candles import Candle
from models.portfolio import Portfolio

class QuitMenuError(Exception):
    """Raised when user quits the program."""
    pass

class CancelMenuError(Exception):
    """Raised when the menu is cancelled"""
    pass

class RefreshMenuError(Exception):
    """Raised when the menu is refreshed"""

class Menu:
    def __init__(self, title: str, stdscr: curses.window, action: Optional[Callable] = None, input_handler: Optional[InputHandler] = None, options: Optional[dict] = None):
        self.title = title
        self.stdscr = stdscr
        self.action = action
        self.input_handler = input_handler if input_handler else InputHandler(stdscr)
        self.options = options if options else {}
        self.has_options = True if options else False
        if not stdscr:
            raise Exception("stdscr cannot be None")

    def menu_output(func: Any):
        def wrapper(self, *args, **kwargs):
            self.stdscr.clear()
            menu_title = f"{self.title}\n\n"
            special_keys = '(q to quit, c to cancel, n for next, p for previous)'
            if curses.has_colors() and curses.can_change_color():
                self.stdscr.addstr(0, 0, menu_title, curses.A_BOLD)
            else:
                self.stdscr.addstr(0, 0, menu_title)
            max_y, _ = self.stdscr.getmaxyx() 
            self.stdscr.addstr(max_y - 1, 0, special_keys)
            self.stdscr.move(2, 0)
            return func(self, *args, **kwargs)
        return wrapper

    def menu_exception_handler(func: Any):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except QuitMenuError:
                raise
            except CancelMenuError:
                raise
            except NextPageException:
                raise
            except PreviousPageException:
                raise
        return wrapper

    def clear_lines(self, start_y: int, line_count: int):
        max_y, _ = self.stdscr.getmaxyx()
        for i in range(0, line_count):
            if start_y + i >= max_y:
                break
            self.stdscr.move(start_y + i, 0)
            self.stdscr.clrtoeol()
        self.stdscr.move(start_y, 0)

    def display_header(self, header: str):
        if curses.has_colors() and curses.can_change_color():
            self.stdscr.addstr(header, curses.A_UNDERLINE)
        else:
            self.stdscr.addstr(header.strip('\n'))
            y, x = self.stdscr.getyx()
            self.stdscr.move(y + 1, 0)
            self.stdscr.hline('-', x)
            self.stdscr.addstr(y + 2, 0, '\n')

    def display_options(self, pagination: bool = False) -> Any:
        y, _ = self.stdscr.getyx()
        y += 1

        options_count = len(self.options)
        choice = 0
        while True:
            self.stdscr.move(y, 0)
            for i, key in enumerate(self.options):
                self.stdscr.clrtoeol()
                if i == choice:
                    self.stdscr.addstr(f"> {self.options[key]} \n", curses.A_REVERSE)
                else:
                    self.stdscr.addstr(f"  {self.options[key]}\n")

            try:
                updated_choice = self.input_handler.get_choice(choice, options_count, pagination=pagination)
                if updated_choice == curses.KEY_ENTER:
                    break
                else:
                    choice = updated_choice
            except QuitInputError:
                raise QuitMenuError
            except CancelInputError:
                raise CancelMenuError
        self.stdscr.clrtobot()

        keys = [key for key in self.options]
        return keys[choice]

    @menu_output
    def display_menu(self):
        self.action()

    @menu_exception_handler
    def results(self, data: list[Prediction]):
        header = f"{'Symbol':<10} {'Start Date':<15} {'Start Price':<15} {'End Price':<15} {'End Date':<15} {'Close Price':<15}\n"
        self.display_header(header)

        for result in data:
            formattedPred = f"{result.symbol:<10} {result.view_start_date():<15} {result.start_price:<15.8f} {result.end_price:<15.8f} {result.view_end_date():<15} {result.close_price:<15.8f}\n"
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
    def predictions(self, data: list[Prediction]):
        header = f"{'Symbol':<10} {'Start Date':<15} {'Start Price':<15} {'End Price':<15} {'End Date':<15} {'Buy Price':<15} {'Sell Price':<15}\n"
        self.display_header(header)

        for prediction in data:
            formattedPred = f"{prediction.symbol:<10} {prediction.view_start_date():<15} {prediction.start_price:<15.8f} {prediction.end_price:<15.8f} {prediction.view_end_date():<15} {prediction.buy_price:<15.8f} {prediction.sell_price:<15.8f}\n"
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

    @menu_output
    @menu_exception_handler
    def addprediction(self):
        y, _ = self.stdscr.getyx()
        last_y, _ = self.stdscr.getmaxyx()
        last_y -= 2

        while True:
            self.clear_lines(y, last_y - y)

            try:
                prediction = {}
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

                summary_header = f"\nSummary of prediction for {prediction['symbol']}:"
                summary_labels = f"{'':<10} {'DATE':<15} {'PRICE':<15}"
                summary_start = f"{'START':<10} {prediction['start_date'].strftime('%Y-%m-%d'):<15} {prediction['start_price']:<15}"
                summary_end = f"{'END':<10} {prediction['end_date'].strftime('%Y-%m-%d'):<15} {prediction['end_price']:<15}\n"
                summary_buy = f"{'BUY':<10} ${prediction['buy_price']:<15.8f}"
                summary_sell = f"{'SELL':<10} ${prediction['sell_price']:<15.8f}\n"

                summary = '\n'.join([summary_header, summary_labels, summary_start, summary_end, summary_buy, summary_sell])
                self.stdscr.addstr(summary + '\n')

                submit = self.input_handler.get_input(
                    prompt="Submit Prediction", input_type=str, format="y/n", default="n", can_refresh=True, validation=lambda x: x.lower() in 'yn').lower()
                
                if submit == 'n':
                    prediction = None
                else: 
                    prediction = Prediction(prediction)

                self.options = {
                    "new": "Start new prediction",
                    "main": "Back to Main Menu",
                    "quit": "Exit Program"
                }
                choice = self.display_options()

                if choice == "main":
                    return (prediction, choice)
                if choice == "quit":
                    return (prediction, choice)
                if choice == "new":
                    return (prediction, choice)

            except QuitInputError:
                raise QuitMenuError
            except QuitMenuError:
                raise
            except CancelInputError:
                raise CancelMenuError
            except CancelMenuError:
                raise
            except RefreshInputError:
                last_y = self.stdscr.getyx()
                continue

            except MissingDataError:
                last_y = self.stdscr.getyx()
                self.stdscr.addstr("Error with prediction upload: Missing data")
                continue
            except InvalidDataError:
                last_y = self.stdscr.getyx()
                self.stdscr.addstr("Error with prediction upload: Invalid data")
                continue
            except TypeError:
                last_y = self.stdscr.getyx()
                self.stdscr.addstr("Error with prediction upload: Type error")
                continue

    @menu_exception_handler
    def editprediction(self, prediction: Prediction):
        try:
            header = f"{'SYMBOL':<15} {'START DATE':<15} {'START PRICE':<15}\n"
            self.display_header(header)
            info = f"{prediction.symbol:<15} {prediction.view_start_date():<15} ${prediction.start_price:<14.8f}\n"
            self.stdscr.addstr(info + '\n')

            self.options = {
                "select_prediction": "Select a different Prediction",
                "delete": "Remove Prediction",
                "main": "Main Menu",
                "quit": "Exit Program"
            }
            choice = self.display_options()

            if choice == "quit":
                raise QuitMenuError
            if choice == "main":
                raise CancelMenuError
            if choice == "select_prediction":
                return choice
            if choice == "delete":
                return choice

        except QuitInputError:
            raise QuitMenuError
        except QuitMenuError:
            raise
        except CancelInputError:
            return None
        except CancelMenuError:
            return None

    def displaypricechart(self, data: list[Candle]):
        y_start, x_start = self.stdscr.getyx()

        self.stdscr.move(20, 30)

        y_end, x_end = self.stdscr.getyx()
        y_mid = y_start + ((y_end - y_start) // 2)
        x_mid = x_start + ((x_end - x_start) // 2)
        self.stdscr.addstr(y_mid, x_mid, "GRAPH HERE")

        self.stdscr.move(y_end + 1, 0)

    @menu_output
    @menu_exception_handler
    def selectprediction(self, data: list[Prediction]) -> Prediction:
        # TODO: Add menu option or special inputs for retrieving next 10 predictions, currently limit data retrieval to 10
        y, _ = self.stdscr.getyx()
        header = f"  {'Symbol':<10} {'Start Date':<15} {'Start Price':<15} {'End Date':<15}"
        self.display_header(header)

        predictions_output = {
            pred : f"{pred.symbol:<10} {pred.view_start_date():<15} {pred.start_price:<15.8f} {pred.view_end_date():<15}"
            for pred in data
        }
        self.options = predictions_output

        prediction = self.display_options(pagination=True)

        self.stdscr.move(y, 0)
        self.stdscr.clrtobot()

        return prediction

    @menu_exception_handler
    def predictionoverview(self, prediction: Prediction, candles: list[Candle]):
        # TODO: Refactor this to be more modular
        # TODO: Refactor this and add a "carousel" for viewing multiple predictions by clicking [P]revious and [N]ext
        header = f'{"Symbol":<15} {"Start Date":<15} {"End Date":<15}\n'
        self.display_header(header)

        while True:
            self.stdscr.addstr(f"{prediction.trading_pair:<15} {prediction.view_start_date():<15} {prediction.view_end_date():<15}\n")
    
            self.displaypricechart(candles)
    
            price_header = f'{"START PRICE":<15} {"PRED. END PRICE":<20} {"BUY PRICE":<15} {"SELL PRICE":<15}\n'
            self.display_header(price_header)
            self.stdscr.addstr(f'{prediction.start_price:<15.8f} {prediction.end_price:<20.8f} {prediction.buy_price:<15.8f} {prediction.sell_price:<15.8f}\n')
    
            self.options = {
                "select_prediction": "Select another Prediction",
                "main": "Back to Main Menu",
                "quit": "Exit Program",
            }
            choice = self.display_options()

            if choice == "select_prediction":
                break
            if choice == 'main':
                break
            if choice == 'quit':
                raise QuitMenuError

        return choice

    @menu_exception_handler
    def resultoverview(self, result: Prediction, candles: list[Candle]):
        header = f'{"Symbol":<15} {"Start Date":<15} {"End Date":<15} {"Close Price":<15} {"Low":<15} {"High":<15}\n'
        self.display_header(header)

        high = candles[0].range_high
        low = candles[0].range_low

        while True:
            self.stdscr.addstr(f"{result.trading_pair:<15} {result.view_start_date():<15} {result.view_end_date():<15} {result.close_price:<15.8f} {low:<15.8f} {high:<15.8f}\n")
    
            self.displaypricechart(candles)
    
            price_header = f'{"START PRICE":<15} {"PRED. END PRICE":<20} {"BUY PRICE":<15} {"SELL PRICE":<15}\n'
            self.display_header(price_header)
            self.stdscr.addstr(f'{result.start_price:<15.8f} {result.end_price:<20.8f} {result.buy_price:<15.8f} {result.sell_price:<15.8f}\n')
    
            self.options = {
                "select_prediction": "Select another Prediction Result",
                "main": "Back to Main Menu",
                "quit": "Exit Program",
            }
            choice = self.display_options()

            if choice == "select_prediction":
                break
            if choice == 'main':
                break
            if choice == 'quit':
                raise QuitMenuError

        return choice

    @menu_exception_handler
    def portfoliosummary(self, portfolio: Portfolio):
        # Balance section sub-title
        balance_header = f"BALANCES\n"
        self.stdscr.addstr(balance_header, curses.A_BOLD)
        # Balance section data
        balance = portfolio.get_balance()
        for balance_type in balance:
            output = f"{'':>4}{balance_type.upper():<7}: $ {balance[balance_type]:>7.2f}\n"
            self.stdscr.addstr(output)

        self.stdscr.addstr('\n')

        # Active positions section sub-title and header
        positions_title = "Active Positions\n"
        self.stdscr.addstr(positions_title, curses.A_BOLD)
        positions_header = f"{'Symbol':<15} {'Current Price':>15} {'Owned Quantity':>15} {'Owned Value':>15}\n"
        self.display_header(positions_header)
        # Active positions section data
        for position in portfolio.active_positions[:5]:
            position_out = f"{position.symbol:<15} {position.curr_price:>15.2f} {position.quantity:>15.2f} {position.value:>15.2f}\n"
            self.stdscr.addstr(position_out)

        self.options = {
            'main': 'Back to Main Menu',
            'quit': 'Exit Program'
        }
        choice = self.display_options()

        if choice == 'main':
            return choice
        if choice == 'quit':
            raise QuitMenuError

    @menu_output
    @menu_exception_handler
    def display_data_error(self):
        self.stdscr.addstr("Your previous action resulted in a data error!\n")
        self.stdscr.addstr("\tEither no data is available and the menu cannot function without it, or\n")
        self.stdscr.addstr("\tthere was an issue while retrieving the data.\n")

        self.options = {
            "main": "Back to Main Menu",
            "quit": "Exit Program",
        }

        choice = self.display_options()

        if choice == 'main':
            return choice
        if choice == 'quit':
            raise QuitMenuError

