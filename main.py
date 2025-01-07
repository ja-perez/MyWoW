import curses
from controller import Controller

def main(stdscr):
    stdscr = curses.initscr()
    curses.curs_set(0)
    stdscr.clear()

    controller = Controller(stdscr)
    controller.run()

    curses.nocbreak()
    curses.curs_set(1)
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

if __name__ == "__main__":
    curses.wrapper(main)