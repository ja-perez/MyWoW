import curses
import utils

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
        -1: "Exit Program",
    }
    return displayOptions(stdscr, options)

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
def listpredictions(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Predictions")

    header = f"{'Symbol':<10} {'Start Date':<15} {'Start Price':<15} {'End Date':<15} {'End Price':<15} {'Buy Price':<15} {'Sell Price':<15}"
    while True:
        stdscr.addstr(1, 0, header)
        for index, pred in enumerate(data):
            formattedPred = f"{pred['symbol']:<10} {pred['start_date']:<15} {pred['start_price']:<15.8f} {pred['end_date']:<15} {pred['end_price']:<15.8f} {pred['buy_price']:<15.8f} {pred['sell_price']:<15.8f}"
            stdscr.addstr(2 + index, 0, formattedPred)

        options = {
            0: "Back to Main Menu",
            -1: "Exit Program",
        }
        stdscr.move(2 + len(data), 0)
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
            case -1:
                break
            case _:
                break

    breakdown(stdscr)

curses.wrapper(main)