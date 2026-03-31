#!/usr/bin/env python3
import curses
import time
from collections import deque
import psutil

HISTORY = 60       # seconds of history
UPDATE_HZ = 1      # updates per second
WARN_PCT = 0.50    # alert if avg drops below 50% of max

def get_core_freqs():
    freqs = psutil.cpu_freq(percpu=True)
    return [f.current for f in freqs], freqs[0].max

def draw(stdscr, histories, max_freq):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN,  -1)           # normal graph
    curses.init_pair(2, curses.COLOR_RED,    -1)           # alert graph
    curses.init_pair(3, curses.COLOR_BLACK,  curses.COLOR_RED)   # alert bg
    curses.init_pair(4, curses.COLOR_WHITE,  curses.COLOR_RED)   # alert text
    curses.init_pair(5, curses.COLOR_CYAN,   -1)           # box normal
    curses.init_pair(6, curses.COLOR_YELLOW, -1)           # labels

    n_cores = len(histories)
    bars = '▁▂▃▄▅▆▇█'

    while True:
        freqs, _ = get_core_freqs()
        for i, f in enumerate(freqs):
            histories[i].append(f)

        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # Check alert condition
        avgs = [sum(d) / len(d) for d in histories]
        alert = any(a < max_freq * WARN_PCT for a in avgs)

        if alert:
            stdscr.bkgd(' ', curses.color_pair(3))

        # --- Stats box (right side) ---
        box_w = 28
        box_x = w - box_w - 1
        box_h = n_cores + 4
        box_y = (h - box_h) // 2

        box_attr = curses.color_pair(4) if alert else curses.color_pair(5)
        txt_attr = curses.color_pair(4) if alert else curses.color_pair(6)

        # Draw box border
        if box_y >= 0 and box_x >= 0:
            stdscr.addstr(box_y,     box_x, '┌' + '─' * (box_w - 2) + '┐', box_attr)
            stdscr.addstr(box_y + 1, box_x, '│' + ' 60s Avg Frequency    ' + '│', box_attr)
            stdscr.addstr(box_y + 2, box_x, '├' + '─' * (box_w - 2) + '┤', box_attr)
            for i, avg in enumerate(avgs):
                pct = (avg / max_freq) * 100
                label = f'│ Core {i:<2}  {avg:>7.0f} MHz  {pct:>4.0f}% │'
                stdscr.addstr(box_y + 3 + i, box_x, label, txt_attr)
            stdscr.addstr(box_y + 3 + n_cores, box_x, '└' + '─' * (box_w - 2) + '┘', box_attr)

        # Alert banner
        if alert:
            msg = ' ⚠  THROTTLING: avg freq below 50% of max ⚠ '
            bx = max(0, (w - len(msg)) // 2)
            stdscr.addstr(0, bx, msg, curses.color_pair(4) | curses.A_BOLD)

        # --- Graphs (left side) ---
        graph_w = box_x - 2
        graph_h = h - 2  # leave top/bottom margin
        rows_per_core = max(1, (graph_h) // n_cores)

        for i, hist in enumerate(histories):
            y = 1 + i * rows_per_core
            if y >= h - 1:
                break

            # Label
            label = f'C{i} '
            lattr = curses.color_pair(4) if alert else curses.color_pair(6)
            if y < h:
                stdscr.addstr(y, 0, label, lattr | curses.A_BOLD)

            # Draw history right-to-left
            col_count = graph_w - len(label)
            samples = list(hist)[-col_count:]  # most recent N samples
            # Pad left with spaces if not enough history yet
            pad = col_count - len(samples)

            gattr = curses.color_pair(2) if alert else curses.color_pair(1)

            for j, sample in enumerate(samples):
                x = len(label) + pad + j
                pct = min(1.0, sample / max_freq)
                bar_idx = int(pct * (len(bars) - 1))
                char = bars[bar_idx]
                if x < graph_w and y < h - 1:
                    stdscr.addstr(y, x, char, gattr)

            # Frequency value at end
            val = f' {freqs[i]:>7.0f}/{max_freq:.0f} MHz'
            ex = graph_w
            if ex + len(val) < w - box_w - 2 and y < h - 1:
                stdscr.addstr(y, ex, val, lattr)

        stdscr.refresh()
        time.sleep(1.0 / UPDATE_HZ)

def main():
    try:
        freqs, max_freq = get_core_freqs()
    except Exception as e:
        print(f"Error reading CPU frequencies: {e}")
        print("Make sure psutil is installed: pip install psutil")
        return

    n_cores = len(freqs)
    histories = [deque(maxlen=HISTORY) for _ in range(n_cores)]

    curses.wrapper(lambda s: draw(s, histories, max_freq))

if __name__ == '__main__':
    main()
