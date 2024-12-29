import curses
from ui import Menu
from services import PredictionService
from inputhandling import InputHandler

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

        self.menus["add_pred"] = Menu("Add Prediction", stdscr=self.stdscr, action=self.handle_add_pred_action)

        self.menus["edit_pred"] = Menu("Edit Prediction", stdscr=self.stdscr, action=self.handle_edit_pred_action)

        self.menus["pred_overview"] = Menu("Prediction Overview", stdscr=self.stdscr, action=self.handle_pred_overview_action)

        self.active_menu = self.menus["main"] # Start program with main menu as default active menu

    def run(self):
        while self.active_menu != None:
            self.stdscr.erase()
            if self.active_menu.options:
                self.active_menu.display_options()
            else:
                self.active_menu.display_interactive_menu()

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
            self.active_menu = None

    def handle_preds_action(self):
        data = self.prediction_service.get_predictions()
        res = self.active_menu.listpredictions(data)

        if res == "quit":
            self.active_menu = None
        elif res in self.menus:
            self.active_menu = self.menus[res]

    def handle_results_action(self):
        data = self.prediction_service.get_results()
        res = self.active_menu.listresults(data)

        if res == "quit":
            self.active_menu = None
        elif res in self.menus:
            self.active_menu = self.menus[res]

    def handle_add_pred_action(self):
        pred = self.active_menu.addprediction()

        if pred == "quit":
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
            prediction_result = data[0]
            res = self.active_menu.predictionoverview(prediction_result, self.prediction_service)

            if res == "quit":
                self.active_menu = None
            else:
                self.active_menu = self.menus["main"]

        else:
            self.active_menu = self.menus["main"]