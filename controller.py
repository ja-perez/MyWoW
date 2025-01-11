import curses
import datetime

import utils
from ui import Menu, QuitMenuError, CancelMenuError
from services import PredictionService, PortfolioService
from database import Database
import services.coinbase as cb
from inputhandling import InputHandler

class MissingDataError(Exception):
    pass

class Controller:
    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr
        self.state: dict = {} # For saving and restoring state information (active menu, data, etc.)

        self.active_menu = None
        self.menus = {
            "main": None,
            "preds": None,
            "results": None,
            "add_pred": None,
            "edit_pred": None,
            "pred_overview": None,
        }

        self.input_handler = InputHandler(stdscr)
        client = cb.get_client()
        self.db = Database('mywow.db')
        self.prediction_service = PredictionService(client, self.db)
        self.portfolio_service = PortfolioService(client, self.db)

        self.setup_menus()
        self.load_state()

    def setup_menus(self):
        mainmenu_options = {
            "preds": "List Predictions",
            "results": "List Prediction Results",
            "add_pred": "Add New Prediction",
            "edit_pred": "Edit Prediction",
            "pred_overview": "Prediction Overview",
            "result_overview": "Result Overview",
            "portfolio": "Portfolio",
            "test": "Test Functionality",
            "quit": "Quit"
        }

        self.menus["main"] = Menu("Main Menu", options=mainmenu_options, stdscr=self.stdscr, action=self.handle_mainmenu_action, input_handler=self.input_handler)

        self.menus["preds"] = Menu("Current Predictions", stdscr=self.stdscr, action=self.handle_preds_action, input_handler=self.input_handler)

        self.menus["results"] = Menu("Prediction Results", stdscr=self.stdscr, action=self.handle_results_action, input_handler=self.input_handler)

        self.menus["add_pred"] = Menu("Add Prediction", stdscr=self.stdscr, action=self.handle_add_pred_action, input_handler=self.input_handler)

        self.menus["edit_pred"] = Menu("Edit Prediction", stdscr=self.stdscr, action=self.handle_edit_pred_action, input_handler=self.input_handler)

        self.menus["pred_overview"] = Menu("Prediction Overview", stdscr=self.stdscr, action=self.handle_pred_overview_action, input_handler=self.input_handler)

        self.menus["result_overview"] = Menu("Result Overview", stdscr=self.stdscr, action=self.handle_result_overview_action, input_handler=self.input_handler)

        self.menus["portfolio"] = Menu("Portfolio", stdscr=self.stdscr, action=self.handle_portfolio_action, input_handler=self.input_handler)

        self.menus["test"] = Menu("Test Menu", stdscr=self.stdscr, action=self.handle_test_action, input_handler=self.input_handler)

        self.active_menu = self.menus["main"] # Start program with main menu as default active menu

    def run(self):
        while self.active_menu != None:
            self.stdscr.erase()
            try:
                self.active_menu.display_menu()
            except QuitMenuError:
                self.on_exit()
                self.active_menu = None
            except CancelMenuError:
                self.active_menu = self.menus['main']
            except MissingDataError:
                self.handle_data_error()

    def load_state(self):
        file_path = utils.get_path_from_data_dir("state.json")
        
        if utils.path.exists(file_path):
            try:
                data = utils.get_dict_data_from_file(file_path)
                self.active_menu = self.menus[data.get("active_menu", "main")]
                self.state = data
            except Exception as e:
                print(f"Failed to load saved state: {e}")

    def on_exit(self):
        state = {
            "active_menu": None,
            "predictions": self.prediction_service.get_predictions(to_json=True),
            "results": self.prediction_service.get_results(to_json=True)
        }
        if self.active_menu:
            state["active_menu"] = next(key for key, val in self.menus.items() if val == self.active_menu)
        utils.write_dict_data_to_file(utils.get_path_from_data_dir("state.json"), state)

        self.db.on_exit()

    def handle_mainmenu_action(self):
        choice = self.active_menu.display_options()
        if choice == "preds":
            self.prediction_service.update_predictions()
            self.active_menu = self.menus[choice]
        if choice == "results":
            self.prediction_service.update_predictions()
            self.active_menu = self.menus[choice]
        if choice == "add_pred":
            self.active_menu = self.menus[choice]
        if choice == "edit_pred":
            self.active_menu = self.menus[choice]
        if choice == "pred_overview":
            self.prediction_service.update_predictions()
            self.active_menu = self.menus[choice]
        if choice == "result_overview":
            self.prediction_service.update_predictions()
            self.active_menu = self.menus[choice]
        if choice == "test":
            self.active_menu = self.menus[choice]
        if choice == "quit":
            self.on_exit()
            self.active_menu = None

    def handle_preds_action(self):
        data = self.prediction_service.get_predictions()
        if not data:
            raise MissingDataError
        res = self.active_menu.predictions(data)

        if res in self.menus:
            self.active_menu = self.menus[res]

    def handle_results_action(self):
        data = self.prediction_service.get_results()
        if not data:
            raise MissingDataError
        res = self.active_menu.results(data)

        if res in self.menus:
            self.active_menu = self.menus[res]

    def handle_add_pred_action(self):
        while True:
            prediction, choice = self.active_menu.addprediction()
            if prediction:
                self.prediction_service.add_prediction(prediction, use_model=True)
            
            if choice == 'new':
                continue
            else:
                break
            
        if choice in self.menus:
            self.active_menu = self.menus[choice]
        if choice == 'quit':
            raise QuitMenuError

    def handle_edit_pred_action(self):
        data = self.prediction_service.get_predictions()
        if not data:
            raise MissingDataError

        while True:
            prediction = self.active_menu.selectprediction(data)
            res = self.active_menu.editprediction(prediction)

            if res == "select_prediction":
                continue
            else:
                break

        if res == "delete":
            self.prediction_service.remove_prediction(prediction)
            res = 'main'

        if res in self.menus:
            self.active_menu = self.menus[res]
        else:
            self.active_menu = self.menus['main']

    def handle_pred_overview_action(self):
        data = self.prediction_service.get_predictions()
        if not data:
            raise MissingDataError

        while True:
            prediction = self.active_menu.selectprediction(data)
            candles = self.prediction_service.get_candles(prediction.trading_pair, prediction.start_date, prediction.end_date)
            res = self.active_menu.predictionoverview(prediction, candles)

            if res == "select_prediction":
                continue
            if res in self.menus:
                self.active_menu = self.menus[res]
                break

    def handle_result_overview_action(self):
        data = self.prediction_service.get_results()
        if not data:
            raise MissingDataError

        while True:
            result = self.active_menu.selectprediction(data)
            candles = self.prediction_service.get_candles(result.trading_pair, result.start_date, result.end_date)

            if not candles:
                raise MissingDataError

            res = self.active_menu.resultoverview(result, candles)

            if res == "select_prediction":
                continue
            if res in self.menus:
                self.active_menu = self.menus[res]
                break

    def handle_portfolio_action(self):
        data = self.portfolio_service.get_portfolio()

    def handle_test_action(self):
        # if res in self.menus:
        #     self.active_menu = self.menus[res]
        self.active_menu = self.menus["main"]

    def handle_data_error(self):
        res = self.active_menu.display_data_error()
        if res in self.menus:
            self.active_menu = self.menus[res]
        else:
            self.active_menu = self.menus["main"]