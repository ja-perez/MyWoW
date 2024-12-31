import curses
import utils
import datetime
import Coinbase as cb
import portfolio
import os

def displayOptions(stdscr: curses.window, options: dict[int, str]) -> int:
    y, _ = stdscr.getyx()
    y += 2 # 2 newlines

    choice = 0
    while True:
        stdscr.move(y, 0)
        stdscr.clrtobot()

        for i, val in enumerate(options):
            option = f"{">" if i == choice else " "} {options[val]}"
            stdscr.addstr(y + i, 0, option)

        key = stdscr.getch()

        # update choice
        if key == curses.KEY_UP or key == ord('w'):
            choice = len(options) - 1 if choice - 1 < 0 else choice - 1
        if key == curses.KEY_DOWN or key == ord('s'):
            choice = (choice + 1) % len(options)
        if key == ord('q'):
            return -1

        # exit once choice selected or q pressed
        if key == curses.KEY_ENTER or key == 10 or key == ord('q'):
            break
    
    values = [val for val in options]
    return values[choice]

def breakdown(stdscr: curses.window):
    stdscr.clear()
    stdscr.addstr(1, 0, "Press any key to continue...")
    stdscr.getch()

    curses.nocbreak()
    curses.curs_set(1)
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

def mainmenu(stdscr) -> int:
    stdscr.clear()
    stdscr.move(0, 0)
    stdscr.addstr(0, 0, "Main Menu")

    options = {
        1: "List predictions",
        2: "List prediction results",
        3: "Add new prediction",
        4: "Edit prediction",
        5: "Prediction overview",
        -1: "Exit Program",
    }
    return displayOptions(stdscr, options)

def getpredictiondata() -> dict:
    fileData = utils.get_csv_data_from_file(utils.get_path_from_data_dir("dummy_data.csv"))
    data = []
    for row in fileData:
        data.append({
            "symbol": row[0],
            "trading-pair": row[1],
            "start_date": row[2],
            "end_date": row[3],
            "start_price": float(row[4]),
            "end_price": float(row[5]),
            "buy_price": float(row[6]),
            "sell_price": float(row[7])
        })
    return data

def getpredictionresults() -> dict:
    fileData = utils.get_csv_data_from_file(utils.get_path_from_data_dir("dummy_results.csv"))
    data = []
    for row in fileData:
        data.append({
            "symbol": row[0],
            "trading-pair": row[1],
            "start_date": row[2],
            "end_date": row[3],
            "start_price": float(row[4]),
            "end_price": float(row[5]),
            "buy_price": float(row[6]),
            "sell_price": float(row[7]),
            "actual_end_price": float(row[8]),
        })
    return data

def updatepredictions():
    data = getpredictiondata()
    today = datetime.datetime.now()

    new_data = []
    for pred in data:
        end_date = datetime.datetime.strptime(pred["end_date"], "%Y-%m-%d")
        start_date = datetime.datetime.strptime(pred["start_date"], "%Y-%m-%d")
        if today > end_date:
            trading_pair = pred["trading-pair"]
            candle = cb.get_asset_candles(cb.get_client(), trading_pair, portfolio.Granularity.ONE_DAY, start_date, end_date) 
            pred_result = pred.copy()
            pred_result["actual_end_price"] = float(candle[0]["close"])
            utils.add_data_to_csv_file(utils.get_path_from_data_dir("dummy_results.csv"), pred_result)
        else:
            new_data.append(pred)
    utils.write_many_data_to_csv_file(utils.get_path_from_data_dir("dummy_data.csv"), new_data)

def listresults(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Prediction Results")

    updatepredictions()

    data = getpredictionresults()

    header = f"{'Symbol':<10} {'Start Date':<15} {'Start Price':<15} {'End Price':<15} {'End Date':<15} {'Actual End Price':<15}"
    while True:
        stdscr.addstr(1, 0, header)
        for index, pred in enumerate(data):
            formattedPred = f"{pred['symbol']:<10} {pred['start_date']:<15} {pred['start_price']:<15.8f} {pred['end_price']:<15.8f} {pred['end_date']:<15} {pred['actual_end_price']:<15.8f}"
            stdscr.addstr(2 + index, 0, formattedPred)

        options = {
            0: "Back to Main Menu",
            -1: "Exit Program",
        }
        stdscr.move(2 + len(data), 0)
        choice = displayOptions(stdscr, options)

        if choice == 0 or choice == -1:
            return choice

def listpredictions(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Predictions")

    data = getpredictiondata()

    header = f"{'Symbol':<10} {'Start Date':<15} {'Start Price':<15} {'End Price':<15} {'End Date':<15} {'Buy Price':<15} {'Sell Price':<15}"
    while True:
        stdscr.addstr(1, 0, header)
        for index, pred in enumerate(data):
            formattedPred = f"{pred['symbol']:<10} {pred['start_date']:<15} {pred['start_price']:<15.8f} {pred['end_price']:<15.8f} {pred['end_date']:<15} {pred['buy_price']:<15.8f} {pred['sell_price']:<15.8f}"
            stdscr.addstr(2 + index, 0, formattedPred)

        options = {
            0: "Back to Main Menu",
            -1: "Exit Program",
        }
        stdscr.move(2 + len(data), 0)
        choice = displayOptions(stdscr, options)

        if choice == 0 or choice == -1:
            return choice

def getInput(stdscr, prompt: str, example: str = "", default: str = "") -> str:
    val = ""
    curses.curs_set(1)
    curses.echo()
    while True:
        # some kind of error check system that ensures the input is valid as its being typed
        stdscr.addstr(f"{prompt}{f' ({example})' if example else ''}: ")
        val = stdscr.getstr().decode("utf-8")
        if not val and default:
            break

        if val:
            break
        # some kind of error checking here or message
        stdscr.delline()
    curses.noecho()
    curses.curs_set(0)
    return val if val else default

# TODO: Refactor this digustingly long, repetitive, ugly dumb looking function
def addprediction(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "New Prediction (c to cancel, q to quit, n for new form)")

    while True:
        stdscr.move(1, 0)
        stdscr.clrtobot()

        trading_pair = getInput(stdscr, "Trading Pair", "BTC-USD, ETH-USD")
        if trading_pair == "n": # n for new (start process all over)
            continue
        if trading_pair == "q":
            return -1
        if trading_pair == "c":
            return 0
        trading_pair = trading_pair.upper()
        asset = trading_pair.split("-")[0]

        stdscr.move(2, 0)
        start_date = getInput(stdscr, "Start Date, in YYYY-MM-DD", "2022-01-01", datetime.datetime.now().strftime("%Y-%m-%d"))
        if start_date == "n":
            continue
        if start_date == "q":
            return -1
        if start_date == "c":
            return 0

        # TODO: Have default value be amount returned by api call for product candle
        stdscr.move(3, 0)
        end_date = getInput(stdscr, "End Date, in YYYY-MM-DD", "2022-01-01") 
        if end_date == "n":
            continue
        if end_date == "q":
            return -1
        if end_date == "c":
            return 0

        stdscr.move(4, 0)
        start_price = getInput(stdscr, "Start Price", "100.00, 0.01")
        if start_price == "n":
            continue
        if start_price == "q":
            return -1
        if start_price == "c":
            return 0
        start_price = float(start_price)

        stdscr.move(5, 0)
        end_price = getInput(stdscr, f"End Price on {end_date}", "100.00, 0.01")
        if end_price == "n":
            continue
        if end_price == "q":
            return -1
        if end_price == "c":
            return 0
        end_price = float(end_price)

        stdscr.move(6, 0)
        buy_price = getInput(stdscr, "Buy Price", "10000.00, 0.01")
        if buy_price == "n":
            continue
        if buy_price == "q":
            return -1
        if buy_price == "c":
            return 0
        buy_price = float(buy_price)

        stdscr.move(7, 0)
        sell_price = getInput(stdscr, "Sell Price", "10000.00, 0.01")
        if sell_price == "n":
            continue
        if sell_price == "q":
            return -1
        if sell_price == "c":
            return 0
        sell_price = float(sell_price)

        stdscr.move(8, 0)
        summary = f"""Summary
        {asset} 
        {start_date:<15} {end_date:<15}
        {start_price:<15.8f} {end_price:<15.8f}
        BUY:{buy_price:<15.8f} SELL:{sell_price:<15.8f}
        """
        stdscr.addstr(summary)
        stdscr.move(13, 0)
        if (getInput(stdscr, "Confirm?", "y/n", "n").lower() == "y"):
            break
        else:
            return 0

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
    utils.add_data_to_csv_file(utils.get_path_from_data_dir("dummy_data.csv"), pred)
    return 0

def editprediction(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Edit Prediction (c to cancel, q to quit)")

    # TODO : Refactor this so finding the desired prediction doesn't require loading the whole file
    data = getpredictiondata()

    while True:
        stdscr.move(1, 0)
        stdscr.clrtoeol()
        val = getInput(stdscr, "Symbol", "BTC, ETH")
        if val == "c" or val == "q":
            break
        val = val.upper()
        found = False
        for pred in data:
            if pred["symbol"] == val:
                found = True
                break
        if found:
            stdscr.move(2, 0)
            stdscr.clrtobot()
            break
        stdscr.addstr(2, 0, f"Error: Symbol {val} not found")

    if val == "c":
        return 0
    if val == "q":
        return -1
    predSymbol = val

    while True:
        stdscr.move(2, 0)
        stdscr.clrtoeol()
        val = getInput(stdscr, "Start Date, in YYYY-MM-DD", "2022-01-01")
        if val == "c" or val == "q":
            break
        found = False
        for pred in data:
            if pred["symbol"] == predSymbol and pred["start_date"] == val:
                found = True
                break
        if found:
            stdscr.move(3, 0)
            stdscr.clrtobot()
            break
        stdscr.addstr(3, 0, "Error: Start Date not found")
    
    if val == "c":
        return 0
    if val == "q":
        return -1
    predStartDate = val

    new_data = []
    for pred in data:
        if pred["symbol"] == predSymbol and pred["start_date"] == predStartDate:
            continue 
        new_data.append(pred)
    utils.write_many_data_to_csv_file(utils.get_path_from_data_dir("dummy_data.csv"), new_data)

    return 0

def displaypricechart(stdscr):
    y_start, x_start = stdscr.getyx()

    stdscr.move(20, 30)

    y_end, x_end = stdscr.getyx()
    y_mid = y_start + ((y_end - y_start) // 2)
    x_mid = x_start + ((x_end - x_start) // 2)
    stdscr.addstr(y_mid, x_mid, "GRAPH HERE")

    stdscr.move(y_end, x_end)

def predictionoverview(stdscr):
    # TODO: Refactor this to be more modular
    # TODO: Refactor this and add an option specifying which prediction to analyze
    # TODO: Refactor this and add a "carousel" for viewing multiple predictions by clicking [P]revious and [N]ext
    stdscr.clear()
    stdscr.addstr(0, 0, "Prediction Analysis")

    predictionResult = getpredictionresults()[0]

    trading_pair = predictionResult["trading-pair"]
    start_date = predictionResult["start_date"]
    end_date = predictionResult["end_date"]
    start_price = predictionResult["start_price"]
    end_price = predictionResult["end_price"]
    buy_price = predictionResult["buy_price"]
    sell_price = predictionResult["sell_price"]
    actual_end_price = predictionResult["actual_end_price"]

    output_filename = f"{start_date.replace("-", "")}_{end_date.replace("-", "")}_{trading_pair}_candles.json"
    output_file_path = utils.get_path_from_data_dir(output_filename)
    if os.path.exists(output_file_path):
        candles = utils.get_dict_data_from_file(output_file_path)
    else:
        start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        candles = cb.get_asset_candles(cb.get_client(), trading_pair, portfolio.Granularity.ONE_DAY, start_datetime, end_datetime)
        utils.write_dict_data_to_file(output_file_path, candles)

    high = -1.0
    low = 99999999999999999.9
    for candle in candles:
        high = max(high, float(candle["high"]))
        low = min(low, float(candle["low"]))

    stdscr.addstr(1, 0, f"{"Symbol":<15} {"Start Date":<15} {"Closing Date":<15} {"Closing Price":<15} {"High":<15} {"Low":<15}")
    stdscr.addstr(2, 0, f"{trading_pair:<15} {start_date:<15} {end_date:<15} {actual_end_price:<15.8f} {high:<15.8f} {low:<15.8f}")

    stdscr.move(3, 0)
    displaypricechart(stdscr)
    graph_y_end, _ = stdscr.getyx()

    stdscr.addstr(graph_y_end + 1, 0, f"{"START PRICE":<15} {"PRED. END PRICE":<20} {"BUY PRICE":<15} {"SELL PRICE":<15}")
    stdscr.addstr(graph_y_end + 2, 0, f"{start_price:<15.8f} {end_price:<20.8f} {buy_price:<15.8f} {sell_price:<15.8f}")

    options = {
        0: "Back to Main Menu",
        -1: "Exit Program",
    }
    while True:
        stdscr.move(graph_y_end + 3, 0)
        choice = displayOptions(stdscr, options)

        if choice == 0 or choice == -1:
            return choice

def main(stdscr):
    stdscr = curses.initscr()
    curses.curs_set(0)
    stdscr.clear()

    state = 0
    while True:
        match state:
            case 0:
                state = mainmenu(stdscr)
            case 1:
                state = listpredictions(stdscr)
            case 2:
                state = listresults(stdscr)
            case 3:
                state = addprediction(stdscr)
            case 4:
                state = editprediction(stdscr)
            case 5:
                state = predictionoverview(stdscr)
            case -1:
                break
            case _:
                break

    breakdown(stdscr)

curses.wrapper(main)