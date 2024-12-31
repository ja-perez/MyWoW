import curses
import datetime

class InvalidInputError(Exception):
    """Raised when input is invalid"""
    pass

class CancelInputError(Exception):
    """Raised when input is cancelled"""
    pass

class QuitInputError(Exception):
    """Raised when user quits the input process."""
    pass

class InputHandler:
    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr

    def inputFromUser(func):
        def wrapper(*args, **kwargs):
            curses.curs_set(1)
            curses.echo()

            result = func(*args, **kwargs)

            curses.curs_set(0)
            curses.noecho()

            return result

        return wrapper

    @inputFromUser
    def get_input(self,
                  prompt: str,
                  input_type: type,
                  format: str="",
                  example: str ="",
                  default = None,
                  validation = None):
        err_flag = False
        return_val = None

        # Input prompt
        output = f"{prompt} "
        if format or example:
            output += f"({f"{format} " if format and example else format}{f"e.g. {example}" if example else ''}): "

        #self.stdscr.addstr(f"{prompt}{f" {hint}" if hint else ''}")
        self.stdscr.addstr(output)

        y, x = self.stdscr.getyx()
        while True:
            try:
                user_input = self.stdscr.getstr().decode("utf-8").lower()

                # Default
                if not user_input and default:
                    self.stdscr.addstr(y, x, default + '\n')
                    return_val = default
                    break
                if not user_input:
                    raise InvalidInputError("Required value, cannot be empty")
                # Cancel current action
                if user_input == 'c':
                    raise CancelInputError()
                # Quit program
                if user_input == 'q':
                    raise QuitInputError()

                if input_type == int:
                    user_input = int(user_input)
                elif input_type == float:
                    user_input = float(user_input)
                elif input_type == datetime.datetime:
                    user_input = datetime.datetime.strptime(user_input, "%Y-%m-%d").strftime("%Y-%m-%d")

                if validation:
                    validation(user_input)
                
                return_val = user_input
                break

            except ValueError as e:
                self.stdscr.addstr(f"  Invalid Input: {e}\n")
                err_flag = True
            except InvalidInputError as e:
                self.stdscr.addstr(f"  Invalid Input: {e}\n")
                err_flag = True
            except AssertionError as e:
                self.stdscr.addstr(f"  Invalid Input: {e}\n")
                err_flag = True

            except CancelInputError:
                return_val = None
                break
            except QuitInputError:
                return_val = "quit"
                break

            # Clean up prompt
            self.stdscr.move(y, x)
            self.stdscr.clrtoeol()

        if err_flag:
            self.stdscr.clrtoeol()

        return return_val

def main(stdscr):
    stdscr = curses.initscr()
    curses.curs_set(0)
    curses.noecho()
    stdscr.clear()
    
    ih = InputHandler(stdscr)

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

    curses.nocbreak()
    curses.curs_set(1)
    curses.echo()
    stdscr.keypad(False)
    curses.endwin()

    print(int_test)
    print(date_test)
    print(float_test)

if __name__=="__main__":
    curses.wrapper(main)