import curses
import datetime
from typing import Any

class InvalidInputError(Exception):
    """Raised when input is invalid."""
    pass

class ValidateInputError(Exception):
    """Raised when input validation fails."""
    pass

class QuitInputError(Exception):
    """Raised when user quits the input process."""
    pass

class CancelInputError(Exception):
    """Raised when input is cancelled."""
    pass

class RefreshInputError(Exception):
    """Raised when input process is refreshed."""
    pass

class NextPageException(Exception):
    """Raised by input treated as a special key"""
    pass
class PreviousPageException(Exception):
    """Raised by input treated as a special key"""
    pass

class InputHandler:
    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr

    def input_from_user(func: Any):
        def wrapper(*args, **kwargs):
            curses.curs_set(1)
            curses.echo()

            try:
                result = func(*args, **kwargs)
            except QuitInputError:
                raise
            except CancelInputError:
                raise
            except RefreshInputError:
                raise
            finally:
                curses.curs_set(0)
                curses.noecho()

            return result

        return wrapper

    @input_from_user
    def get_input(self,
                  prompt: str,
                  input_type: type,
                  format: str="",
                  example: str ="",
                  default = None,
                  validation = None,
                  can_refresh = False):
        err_flag = False
        return_val: Any = None

        # Input prompt
        output = f"{prompt} "
        if format or example:

            output += f'({format}{" " if format and example else ""}'
            output += f'{f"e.g. {example}" if example else ""}): '
        self.stdscr.addstr(output)

        y, x = self.stdscr.getyx()
        while True:
            try:
                user_input: str = self.stdscr.getstr().decode("utf-8").lower()

                # Default
                if not user_input and default:
                    self.stdscr.addstr(y, x, default + '\n')
                    user_input = default
                if not user_input:
                    raise InvalidInputError("Required value, cannot be empty")
                # Cancel current action
                if user_input == 'c':
                    raise CancelInputError
                # Quit program
                if user_input == 'q':
                    raise QuitInputError
                # Refresh input process
                if user_input == 'r' and can_refresh:
                    raise RefreshInputError

                if input_type == str:
                    return_val = user_input
                if input_type == int:
                    return_val = int(user_input)
                elif input_type == float:
                    return_val = float(user_input)
                elif input_type == datetime.datetime:
                    return_val = datetime.datetime.strptime(user_input, "%Y-%m-%d")

                if validation and not validation(return_val):
                    raise ValidateInputError("Validation failed")
                
                break

            except ValueError as e:
                self.stdscr.addstr(f"  Invalid Input (VE): {e}\n")
                err_flag = True
            except InvalidInputError as e:
                self.stdscr.addstr(f"  Invalid Input (IIE): {e}\n")
                err_flag = True
            except ValidateInputError as e:
                self.stdscr.addstr(f"  Invalid Input (VE): {e}\n")
                err_flag = True

            except CancelInputError:
                raise
            except QuitInputError:
                raise
            except RefreshInputError:
                raise

            except Exception as e:
                self.stdscr.addstr(f"  Invalid Input: Unexpected Error\n\t{e}")
                err_flag = True

            # Clean up previous input
            self.stdscr.move(y, x)
            self.stdscr.clrtoeol()

        if err_flag:
            self.stdscr.clrtoeol()

        return return_val

    def get_choice(self, curr_choice: int, options_cnt: int, pagination: bool = False) -> int:
        while True:
            try:
                input_key = self.stdscr.getch()
                input_key_as_char = chr(input_key).lower()

                if input_key == curses.KEY_UP or input_key_as_char == 'w':
                    return max(0, curr_choice - 1)
                if input_key == curses.KEY_DOWN or input_key_as_char == 's':
                    return min(options_cnt - 1, curr_choice + 1)
                if input_key == curses.KEY_ENTER or input_key == 10 or input_key_as_char == '\n':
                    return curses.KEY_ENTER
                if input_key_as_char == 'q':
                    raise QuitInputError
                if input_key_as_char == 'c':
                    raise CancelInputError
                if input_key_as_char == 'n' and pagination:
                    raise NextPageException
                if input_key_as_char == 'p' and pagination:
                    raise PreviousPageException

            except QuitInputError:
                raise
            except CancelInputError:
                raise
            except NextPageException:
                raise
            except PreviousPageException:
                raise

def main(stdscr):
    stdscr = curses.initscr()
    curses.curs_set(0)
    curses.noecho()
    stdscr.clear()
    
    ih = InputHandler(stdscr)

    try:
        int_test = ih.get_input(
            prompt=">",
            input_type=int,
            format="int"
        )

        date_test = ih.get_input(
            prompt="Enter date",
            input_type=datetime.datetime,
            format="YYYY-MM-DD",
            example="2022-12-01",
            default=datetime.datetime.strftime(datetime.datetime.today(), "%Y-%m-%d")
        )

        def float_validator(x):
            try:
                val = float(x)
                assert(val > 0)
                return True
            except ValueError as _:
                raise ValueError
            except AssertionError as _:
                raise AssertionError("Must be greater than zero")

        float_test = ih.get_input(
            prompt=">",
            input_type=float,
            validation=float_validator
        )

        print(int_test)
        print(date_test)
        print(float_test)

    except QuitInputError:
        stdscr.addstr("Quit Input")
    except CancelInputError:
        stdscr.addstr("Cancelled Input")
    finally:
        curses.nocbreak()
        curses.curs_set(1)
        curses.echo()
        stdscr.keypad(False)
        curses.endwin()

if __name__=="__main__":
    curses.wrapper(main)