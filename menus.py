import curses
import utils
import datetime

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
            choice = abs(choice - 1) % len(options)
        if key == curses.KEY_DOWN or key == ord('s'):
            choice = abs(choice + 1) % len(options)
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
        1: "List Predictions",
        2: "Add new Prediction",
        3: "Edit Prediction",
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
    stdscr.addstr(0, 0, "New Prediction (c to cancel, q to quit)")

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
                state = addprediction(stdscr)
            case 3:
                state = editprediction(stdscr)
            case -1:
                break
            case _:
                break

    breakdown(stdscr)

curses.wrapper(main)