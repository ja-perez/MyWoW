import curses
from ui import Menu
from services import PredictionService
from inputhandling import InputHandler
import datetime
import utils

class Controller:
    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr
        self.state = {} # For saving and restoring state information (active menu, data, etc.)

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
        self.prediction_service = PredictionService()

        self.setup_menus()
        self.load_state()

    def setup_menus(self):
        mainmenu_options = {
            "preds": "List Predictions",
            "results": "List Prediction Results",
            "add_pred": "Add New Prediction",
            "edit_pred": "Edit Prediction",
            "pred_overview": "Prediction Overview",
            "quit": "Quit"
        }
        self.menus["main"] = Menu("Main Menu", mainmenu_options, self.stdscr, self.handle_mainmenu_action)

        self.menus["preds"] = Menu("Current Predictions", stdscr=self.stdscr, action=self.handle_preds_action)

        self.menus["results"] = Menu("Prediction Results", stdscr=self.stdscr, action=self.handle_results_action)

        self.menus["add_pred"] = Menu("Add Prediction", stdscr=self.stdscr, action=self.handle_add_pred_action, input_handler=self.input_handler)

        self.menus["edit_pred"] = Menu("Edit Prediction", stdscr=self.stdscr, action=self.handle_edit_pred_action, input_handler=self.input_handler)

        self.menus["pred_overview"] = Menu("Prediction Overview", stdscr=self.stdscr, action=self.handle_pred_overview_action)

        self.active_menu = self.menus["main"] # Start program with main menu as default active menu

    def run(self):
        while self.active_menu != None:
            self.stdscr.erase()
            if self.active_menu.has_options:
                choice = self.active_menu.display_options()
                self.active_menu.action(choice)
            else:
                self.active_menu.display_interactive_menu()

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
            "data": self.prediction_service.get_predictions(),
            "results": self.prediction_service.get_results()
        }
        if self.active_menu:
            state["active_menu"] = next(key for key, val in self.menus.items() if val == self.active_menu)

        utils.write_dict_data_to_file(utils.get_path_from_data_dir("state.json"), state)

    def handle_mainmenu_action(self, choice):
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
            self.active_menu = self.menus[choice]
        if choice == "quit":
            self.on_exit()
            self.active_menu = None

    def handle_preds_action(self):
        data = self.prediction_service.get_predictions()
        res = self.active_menu.listpredictions(data)

        if res == "quit":
            self.on_exit()
            self.active_menu = None
        elif res in self.menus:
            self.active_menu = self.menus[res]

    def handle_results_action(self):
        data = self.prediction_service.get_results()
        res = self.active_menu.listresults(data)

        if res == "quit":
            self.on_exit()
            self.active_menu = None
        elif res in self.menus:
            self.active_menu = self.menus[res]

    def handle_add_pred_action(self):
        pred = self.active_menu.addprediction()

        if pred == "quit":
            self.on_exit()
            self.active_menu = None
        elif pred:
            self.prediction_service.add_prediction(pred)
            self.active_menu = self.menus["main"]
        else:
            self.active_menu = self.menus["main"]

    def handle_edit_pred_action(self):
        data = self.prediction_service.get_predictions()
        res = self.active_menu.editprediction(data)

        if res == "quit":
            self.on_exit()
            self.active_menu = None
        elif res:
            symbol, start_date = res
            self.prediction_service.edit_prediction(symbol, start_date)
            self.active_menu = self.menus["main"]
        else:
            self.active_menu = self.menus["main"]

    def handle_pred_overview_action(self):
        data = self.prediction_service.get_results()

        if data:
            results = data[0]
            trading_pair = results["trading-pair"]
            start_date = datetime.datetime.strptime(results["start_date"], "%Y-%m-%d")
            end_date = datetime.datetime.strptime(results["end_date"], "%Y-%m-%d")
            candles = self.prediction_service.get_candles(trading_pair, start_date, end_date)
            res = self.active_menu.predictionoverview(results, candles)

            if res == "quit":
                self.on_exit()
                self.active_menu = None
            else:
                self.active_menu = self.menus["main"]

        else:
            self.active_menu = self.menus["main"]