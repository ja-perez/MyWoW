import curses
from typing import Optional

def clean_up(stdscr: curses.window):
    curses.nocbreak()
    curses.curs_set(1)
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

def draw_border(stdscr: curses.window, box_width: int, box_height: int):
    curr_y, curr_x = stdscr.getyx()

    # Top line
    stdscr.hline(curr_y, curr_x + 1, curses.ACS_HLINE, box_width - 2)
    # Bottom line
    stdscr.hline(curr_y + box_height, curr_x + 1, curses.ACS_HLINE, box_width - 2)

    # Left line
    stdscr.vline(curr_y + 1, curr_x, curses.ACS_VLINE, box_height - 1)
    # Right line
    stdscr.vline(curr_y + 1, curr_x + box_width - 1, curses.ACS_VLINE, box_height - 1)

    # Corners
    stdscr.addch(curr_y, curr_x, curses.ACS_ULCORNER)           # Upper Left
    stdscr.addch(curr_y, curr_x + box_width - 1, curses.ACS_URCORNER)  # Upper Right
    stdscr.addch(curr_y + box_height, curr_x, curses.ACS_LLCORNER)      # Lower Left
    stdscr.addch(curr_y + box_height, curr_x + box_width - 1, curses.ACS_LRCORNER) # Lower Right

def draw_ticks(stdscr: curses.window, 
               box_width: int, box_height: int,
               x_scale: Optional[list[int]] = None, 
               x_step: int = 0,
               y_scale: Optional[list[int]] = None, 
               y_step: int = 0):
    curr_y, curr_x = stdscr.getyx()

    # y-axis ticks
    if y_scale and y_step:
        y_min, y_max = y_scale
        offsets, values = get_axis_legend(box_height, y_min, y_max, y_step)
        for offset, value in zip(offsets, values):
            stdscr.addstr(curr_y + box_height - offset, 0, str(value))

    # x-axis ticks
    if x_scale and x_step:
        x_min, x_max = x_scale
        offsets, values = get_axis_legend(box_width, x_min, x_max, x_step)
        for offset, value in zip(offsets, values):
            stdscr.addstr(curr_y + box_height + 1, curr_x + offset, str(value))

def get_axis_legend(box_offset: int, axis_min: int, axis_max: int, step: int):
    offsets = [x for x in range(0, box_offset + 1, box_offset // (axis_max // step))]
    values = [val for val in range(axis_min, axis_max + 1, step)]
    return offsets, values

def main(stdscr):
    stdscr = curses.initscr()
    curses.curs_set(0)
    stdscr.clear()

    while True:
        stdscr.erase()
        y, x = stdscr.getyx()
        plot_ul_y, plot_ul_x = y + 2, x + 3
        stdscr.move(plot_ul_y, plot_ul_x)

        box_w, box_h = 80, 40
        draw_border(stdscr, box_w, box_h)

        stdscr.move(plot_ul_y, plot_ul_x)
        h_scale = [0, 20]
        v_scale = [0, 20]
        h_step = 1
        v_step = 1
        draw_ticks(stdscr, box_w, box_h, x_scale=h_scale, x_step=h_step, y_scale=v_scale, y_step=v_step)

        data = [
            [1, 3],
            [3, 9],
            [9, 18]
        ]
        stdscr.move(plot_ul_y, plot_ul_x)
        h_zero = plot_ul_x
        v_zero = plot_ul_y + box_h
        x_offsets, x_values = get_axis_legend(box_w, h_scale[0], h_scale[1], h_step)
        y_offsets, y_values = get_axis_legend(box_h, v_scale[0], v_scale[1], v_step)
        x_value_to_offset = {
            val: offset for offset, val in zip(x_offsets, x_values)
        }
        y_value_to_offset = {
            val: offset for offset, val in zip(y_offsets, y_values)
        }
        for point_x, point_y in data:
            corrected_x = h_zero + x_value_to_offset[point_x]
            corrected_y = v_zero - y_value_to_offset[point_y]
            stdscr.addch(corrected_y, corrected_x, '#')

        key = stdscr.getch()
        if key == 10 or key == curses.KEY_ENTER:
            break

    clean_up(stdscr)

if __name__=='__main__':
    curses.wrapper(main)