#!/usr/bin/env python3
"""
CPU Frequency Monitor - A real-time terminal-based CPU frequency monitoring tool.

This script displays live CPU frequency information for each core with:
- Real-time frequency graphs using Unicode block characters
- 60-second rolling averages
- Visual alerts when frequencies drop below threshold (potential throttling)
- Color-coded terminal interface

Dependencies:
- psutil: For reading CPU frequency information
- curses: For terminal UI (built into Python)

Author: Generated with Claude Code
"""

import curses
import time
from collections import deque
import psutil

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# How many seconds of frequency history to keep for calculating averages
HISTORY_SECONDS = 60

# How many times per second to update the display (1 = once per second)
UPDATE_FREQUENCY_HZ = 1

# Alert threshold: warn if any core's average frequency drops below this
# percentage of the maximum frequency (0.50 = 50%)
THROTTLING_ALERT_THRESHOLD = 0.50

# ============================================================================
# CORE FUNCTIONS - CPU Frequency Reading
# ============================================================================

def get_cpu_frequencies():
    """
    Retrieve current CPU frequencies for all cores.

    Uses psutil to read the current frequency of each CPU core and determine
    the maximum frequency capability of the processor.

    Returns:
        tuple: (list_of_current_frequencies, maximum_frequency)
            - list_of_current_frequencies: List of current MHz values for each core
            - maximum_frequency: The maximum MHz this CPU can achieve

    Raises:
        Exception: If psutil cannot read frequency information (may happen on
                  some systems or if permissions are insufficient)
    """
    # Get frequency info for each core separately (percpu=True)
    frequency_info = psutil.cpu_freq(percpu=True)

    # Extract just the current frequency from each core's info
    current_frequencies = [core_info.current for core_info in frequency_info]

    # The maximum frequency is the same for all cores, so we use the first one
    maximum_frequency = frequency_info[0].max

    return current_frequencies, maximum_frequency

# ============================================================================
# HELPER FUNCTIONS - Alert Detection and Statistics
# ============================================================================

def detect_throttling_alert(frequency_histories, maximum_frequency):
    """
    Check if any CPU core is experiencing potential throttling.

    Calculates the average frequency for each core over the stored history
    and checks if any core's average has dropped below the alert threshold.

    Args:
        frequency_histories: List of deque objects containing frequency history for each core
        maximum_frequency: The maximum frequency this CPU can achieve (MHz)

    Returns:
        bool: True if any core's average frequency is below the threshold (potential throttling)
    """
    # Calculate average frequency for each core from its history
    average_frequencies = []
    for core_history in frequency_histories:
        if len(core_history) > 0:
            average_freq = sum(core_history) / len(core_history)
            average_frequencies.append(average_freq)
        else:
            # If no history yet, assume we're at max frequency
            average_frequencies.append(maximum_frequency)

    # Check if ANY core is below the throttling threshold
    throttling_threshold = maximum_frequency * THROTTLING_ALERT_THRESHOLD
    is_throttling = any(avg < throttling_threshold for avg in average_frequencies)

    return is_throttling, average_frequencies


def setup_terminal_colors():
    """
    Initialize color pairs for the terminal display.

    Sets up different color combinations for:
    - Normal frequency graphs (green)
    - Alert frequency graphs (red)
    - Alert backgrounds (red background)
    - Alert text (white on red)
    - Box borders (cyan or yellow)
    - Labels (cyan or yellow)
    """
    curses.start_color()
    curses.use_default_colors()

    # Color pair 1: Green text for normal frequency graphs
    curses.init_pair(1, curses.COLOR_GREEN, -1)

    # Color pair 2: Red text for frequency graphs during alerts
    curses.init_pair(2, curses.COLOR_RED, -1)

    # Color pair 3: Red background for alert mode
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_RED)

    # Color pair 4: White text on red background for alert text
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_RED)

    # Color pair 5: Cyan text for normal box borders
    curses.init_pair(5, curses.COLOR_CYAN, -1)

    # Color pair 6: Yellow text for normal labels
    curses.init_pair(6, curses.COLOR_YELLOW, -1)


def draw_statistics_box(screen, box_position, average_frequencies, maximum_frequency, is_alert_mode):
    """
    Draw the statistics box showing frequency averages and percentages.

    Args:
        screen: The curses screen object
        box_position: Tuple of (x, y, width, height) for box placement
        average_frequencies: List of average frequencies for each core
        maximum_frequency: Maximum frequency capability
        is_alert_mode: Whether we're currently in alert mode (affects colors)
    """
    box_x, box_y, box_width, box_height = box_position
    number_of_cores = len(average_frequencies)

    # Choose colors based on alert mode
    if is_alert_mode:
        box_color = curses.color_pair(4)  # White on red for alerts
        text_color = curses.color_pair(4)
    else:
        box_color = curses.color_pair(5)  # Cyan for normal mode
        text_color = curses.color_pair(6)  # Yellow for normal mode

    # Only draw if the box fits on screen
    screen_height, screen_width = screen.getmaxyx()
    if box_y >= 0 and box_x >= 0 and box_y + box_height < screen_height:

        # Draw the top border of the box
        top_border = '┌' + '─' * (box_width - 2) + '┐'
        screen.addstr(box_y, box_x, top_border, box_color)

        # Draw the header line - make it exactly box_width characters
        header_text = '  60s Avg Frequency   '
        padding_needed = box_width - 2 - len(header_text)  # -2 for the │ characters
        header = '│' + header_text + ' ' * padding_needed + '│'
        screen.addstr(box_y + 1, box_x, header, box_color)

        # Draw the separator line
        separator = '├' + '─' * (box_width - 2) + '┤'
        screen.addstr(box_y + 2, box_x, separator, box_color)

        # Draw frequency info for each core
        for core_index, average_freq in enumerate(average_frequencies):
            # Calculate what percentage this represents of maximum frequency
            frequency_percentage = (average_freq / maximum_frequency) * 100

            # Format the line with fixed width to ensure straight right border
            content_text = f' Core {core_index:<2} {average_freq:>4.0f} MHz {frequency_percentage:>3.0f}% '
            padding_needed = box_width - 2 - len(content_text)  # -2 for the │ characters
            frequency_line = '│' + content_text + ' ' * padding_needed + '│'

            line_y = box_y + 3 + core_index
            if line_y < screen_height:
                screen.addstr(line_y, box_x, frequency_line, text_color)

        # Draw the bottom border
        bottom_border = '└' + '─' * (box_width - 2) + '┘'
        bottom_y = box_y + 3 + number_of_cores
        if bottom_y < screen_height:
            screen.addstr(bottom_y, box_x, bottom_border, box_color)


def draw_alert_banner(screen, screen_width):
    """
    Draw the warning banner at the top when throttling is detected.

    Args:
        screen: The curses screen object
        screen_width: Width of the terminal screen
    """
    # The warning message to display
    warning_message = ' ⚠  THROTTLING: avg freq below 50% of max ⚠ '

    # Center the message on the screen
    banner_x = max(0, (screen_width - len(warning_message)) // 2)

    # Draw at the top of the screen with bold white text on red background
    alert_style = curses.color_pair(4) | curses.A_BOLD
    screen.addstr(0, banner_x, warning_message, alert_style)


def draw_frequency_graphs(screen, graph_area, frequency_histories, current_frequencies, maximum_frequency, is_alert_mode, stats_box_width):
    """
    Draw the real-time frequency graphs for each CPU core.

    Args:
        screen: The curses screen object
        graph_area: Tuple of (x, y, width, height) for graph placement
        frequency_histories: List of deque objects with frequency history
        current_frequencies: List of current frequency values
        maximum_frequency: Maximum frequency capability
        is_alert_mode: Whether we're in alert mode (affects colors)
    """
    graph_x, graph_y, graph_width, graph_height = graph_area
    number_of_cores = len(frequency_histories)

    # Unicode block characters for drawing the frequency bars (low to high)
    frequency_bars = '▁▂▃▄▅▆▇█'

    # Calculate how many rows each core gets for its graph
    rows_per_core = max(1, graph_height // number_of_cores)

    # Choose graph color based on alert mode
    if is_alert_mode:
        graph_color = curses.color_pair(2)  # Red during alerts
        label_color = curses.color_pair(4)  # White on red during alerts
    else:
        graph_color = curses.color_pair(1)  # Green normally
        label_color = curses.color_pair(6)  # Yellow normally

    # Draw a graph for each CPU core
    for core_index, core_history in enumerate(frequency_histories):
        # Calculate the vertical position for this core's graph
        core_y_position = graph_y + core_index * rows_per_core

        # Skip if this would go off the bottom of the screen
        screen_height, screen_width = screen.getmaxyx()
        if core_y_position >= screen_height - 1:
            break

        # Draw the core label (e.g., "C0 ")
        core_label = f'C{core_index} '
        screen.addstr(core_y_position, graph_x, core_label, label_color | curses.A_BOLD)

        # Calculate how much horizontal space we have for the graph
        # We need to account for the frequency display that will be shown after the graph
        frequency_display_sample = f' {current_frequencies[core_index]:>7.0f}/{maximum_frequency:.0f} MHz'
        space_needed_for_freq_display = len(frequency_display_sample)

        # Calculate actual available width for the frequency bars
        available_graph_width = (graph_width - len(core_label) - 
                                space_needed_for_freq_display - 2)  # 2 chars margin

        # Get the most recent frequency samples that fit in our graph width
        recent_samples = list(core_history)[-available_graph_width:]

        # If we don't have enough history to fill the graph, pad with empty space
        padding_needed = available_graph_width - len(recent_samples)

        # Draw the frequency history as bars
        for sample_index, frequency_sample in enumerate(recent_samples):
            # Calculate horizontal position for this bar
            bar_x_position = graph_x + len(core_label) + padding_needed + sample_index

            # Convert frequency to a percentage of maximum
            frequency_percentage = min(1.0, frequency_sample / maximum_frequency)

            # Pick the appropriate Unicode block character
            bar_character_index = int(frequency_percentage * (len(frequency_bars) - 1))
            bar_character = frequency_bars[bar_character_index]

            # Draw the bar if it fits on screen
            if (bar_x_position < graph_width and 
                core_y_position < screen_height - 1 and 
                bar_x_position >= 0):
                screen.addstr(core_y_position, bar_x_position, bar_character, graph_color)

        # Draw current frequency value immediately after the graph bars
        current_freq = current_frequencies[core_index]
        frequency_display = f' {current_freq:>7.0f}/{maximum_frequency:.0f} MHz'

        # Position it right after the graph bars with a small gap
        freq_display_x = len(core_label) + available_graph_width + 1
        screen_height, screen_width = screen.getmaxyx()

        # Make sure it fits on screen
        if (freq_display_x + len(frequency_display) < screen_width and 
            core_y_position < screen_height - 1):
            screen.addstr(core_y_position, freq_display_x, frequency_display, label_color)


def main_display_loop(screen, frequency_histories, maximum_frequency):
    """
    Main display loop that continuously updates the frequency monitor.

    This is the core loop that:
    1. Reads current CPU frequencies
    2. Updates frequency histories
    3. Detects throttling conditions
    4. Draws the complete interface
    5. Sleeps until next update

    Args:
        screen: The curses screen object
        frequency_histories: List of deque objects for storing frequency history
        maximum_frequency: Maximum frequency capability of the CPU
    """
    # Set up colors for the terminal display
    setup_terminal_colors()


    number_of_cores = len(frequency_histories)

    # ========================================================================
    # MAIN DISPLAY LOOP - This runs continuously until the user exits
    # ========================================================================
    while True:
        # Step 1: Get the current frequency of each CPU core
        current_frequencies, _ = get_cpu_frequencies()

        # Step 2: Add the new frequency readings to our history
        for core_index, current_frequency in enumerate(current_frequencies):
            frequency_histories[core_index].append(current_frequency)

        # Step 3: Clear the screen to prepare for new display
        screen.erase()

        # Step 4: Get current screen dimensions
        screen_height, screen_width = screen.getmaxyx()

        # Step 5: Check if we should trigger throttling alerts
        is_throttling, average_frequencies = detect_throttling_alert(
            frequency_histories, maximum_frequency
        )

        # Step 6: Set background color for alert mode
        if is_throttling:
            # Red background during alerts
            screen.bkgd(' ', curses.color_pair(3))

        # Step 7: Calculate layout dimensions

        # Statistics box (right side of screen)
        stats_box_width = 30
        stats_box_x = screen_width - stats_box_width - 1
        stats_box_height = number_of_cores + 4  # cores + header + borders
        stats_box_y = (screen_height - stats_box_height) // 2  # center vertically

        # Frequency graphs (left side of screen)
        graph_area_x = 0
        graph_area_y = 1  # leave top margin
        graph_area_width = stats_box_x - 2  # leave space between graph and box
        graph_area_height = screen_height - 2  # leave top/bottom margins

        # Step 8: Draw all the interface components

        # Draw the statistics box (averages and percentages)
        draw_statistics_box(
            screen,
            (stats_box_x, stats_box_y, stats_box_width, stats_box_height),
            average_frequencies,
            maximum_frequency,
            is_throttling
        )

        # Draw the alert banner if we're in throttling mode
        if is_throttling:
            draw_alert_banner(screen, screen_width)

        # Draw the frequency graphs for each core
        draw_frequency_graphs(
            screen,
            (graph_area_x, graph_area_y, graph_area_width, graph_area_height),
            frequency_histories,
            current_frequencies,
            maximum_frequency,
            is_throttling,
            stats_box_width  # Pass box width so graphs don't overlap
        )

        # Step 9: Update the display with all our changes
        screen.refresh()

        # Step 10: Wait before the next update
        time.sleep(1.0 / UPDATE_FREQUENCY_HZ)

# ============================================================================
# MAIN PROGRAM ENTRY POINT
# ============================================================================

def main():
    """
    Main function that sets up the frequency monitor and starts the display.

    This function:
    1. Tests that we can read CPU frequency information
    2. Sets up history storage for each CPU core
    3. Launches the terminal interface
    4. Handles any errors gracefully
    """
    try:
        # Test that we can read CPU frequencies before starting the interface
        initial_frequencies, maximum_frequency = get_cpu_frequencies()
    except Exception as error:
        # If we can't read frequencies, show helpful error message and exit
        print(f"Error reading CPU frequencies: {error}")
        print("Make sure psutil is installed: pip install psutil")
        print("")
        print("On some systems, you may need to run with elevated permissions")
        print("or check that your system supports frequency monitoring.")
        return

    # Determine how many CPU cores we're monitoring
    number_of_cores = len(initial_frequencies)
    print(f"Starting CPU frequency monitor for {number_of_cores} cores...")
    print(f"Maximum frequency: {maximum_frequency:.0f} MHz")
    print(f"Press Ctrl+C to exit")
    print("")

    # Create history storage for each core
    # Each deque will automatically maintain only the most recent HISTORY_SECONDS values
    frequency_histories = [
        deque(maxlen=HISTORY_SECONDS) for _ in range(number_of_cores)
    ]

    # Launch the terminal interface
    # curses.wrapper handles terminal setup/cleanup automatically
    try:
        curses.wrapper(
            lambda screen: main_display_loop(screen, frequency_histories, maximum_frequency)
        )
    except KeyboardInterrupt:
        # User pressed Ctrl+C - exit gracefully
        print("\nMonitoring stopped by user.")
    except Exception as error:
        # Handle any unexpected errors
        print(f"\nUnexpected error: {error}")
        print("The monitor has been stopped.")


if __name__ == '__main__':
    main()
