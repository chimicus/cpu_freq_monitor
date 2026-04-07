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

# CPU usage alert thresholds
CPU_USAGE_WARNING_THRESHOLD = 70  # % - warn when core usage exceeds this
CPU_USAGE_HIGH_THRESHOLD = 90     # % - alert when core usage exceeds this

# CPU temperature alert thresholds
TEMPERATURE_WARNING_THRESHOLD = 80   # °C - warn when core temperature exceeds this
TEMPERATURE_CRITICAL_THRESHOLD = 90  # °C - alert when core temperature exceeds this

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


def get_cpu_usage():
    """
    Retrieve current CPU usage percentages for all cores.

    Uses psutil to read the current usage percentage of each CPU core.
    This function blocks briefly to measure CPU usage over a short interval.

    Returns:
        list: List of current usage percentages (0-100) for each core

    Raises:
        Exception: If psutil cannot read CPU usage information
    """
    # Get CPU usage for each core with a brief interval for accurate measurement
    current_usage = psutil.cpu_percent(percpu=True, interval=0.1)
    return current_usage


def get_cpu_temperatures():
    """
    Retrieve current CPU temperatures for all cores.

    Uses psutil to read temperature sensor data from various sources including
    Intel coretemp sensors and AMD k10temp sensors. Extracts per-core temperatures
    and returns them in a consistent format.

    Returns:
        list or None: List of current temperatures in °C for each core, or None if
                     no temperature sensors are available or accessible

    Raises:
        None: Function handles all exceptions gracefully and returns None on error
    """
    try:
        # Get all available temperature sensors
        sensor_data = psutil.sensors_temperatures()
        
        if not sensor_data:
            # No temperature sensors available on this system
            return None
        
        core_temps = []
        
        # Try Intel coretemp sensors first (most common)
        if 'coretemp' in sensor_data:
            for sensor in sensor_data['coretemp']:
                # Look for individual core temperatures (skip package/socket temps)
                if sensor.label and 'Core' in sensor.label:
                    temp = sensor.current
                    # Validate temperature is reasonable (0-150°C)
                    if 0 <= temp <= 150:
                        core_temps.append(temp)
        
        # Try AMD k10temp sensors if coretemp not available or insufficient
        elif 'k10temp' in sensor_data:
            for sensor in sensor_data['k10temp']:
                # AMD sensors may have different label patterns
                if sensor.label:
                    temp = sensor.current
                    # Validate temperature range
                    if 0 <= temp <= 150:
                        core_temps.append(temp)
        
        # Try other common sensor names
        else:
            # Look for any other temperature sensors
            for sensor_name, sensors in sensor_data.items():
                for sensor in sensors:
                    if sensor.label and sensor.current:
                        temp = sensor.current
                        if 0 <= temp <= 150:
                            core_temps.append(temp)
        
        # Return the core temperatures, or None if none found
        return core_temps if core_temps else None
        
    except Exception:
        # Handle any psutil errors gracefully (permissions, missing sensors, etc.)
        return None

# ============================================================================
# HELPER FUNCTIONS - Alert Detection and Statistics
# ============================================================================

def detect_alerts(frequency_histories, usage_histories, maximum_frequency):
    """
    Check for various CPU alert conditions (throttling, high usage).

    Calculates averages and checks for:
    - Frequency throttling (average frequency below threshold)
    - High CPU usage (current usage above thresholds)

    Args:
        frequency_histories: List of deque objects containing frequency history for each core
        usage_histories: List of deque objects containing usage history for each core
        maximum_frequency: The maximum frequency this CPU can achieve (MHz)

    Returns:
        tuple: (alert_active, alert_type, average_frequencies, average_usage)
            - alert_active: True if any alert condition is met
            - alert_type: String describing the primary alert type
            - average_frequencies: List of average frequencies for each core
            - average_usage: List of average usage percentages for each core
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

    # Calculate average usage for each core from its history
    average_usage = []
    for core_history in usage_histories:
        if len(core_history) > 0:
            average_use = sum(core_history) / len(core_history)
            average_usage.append(average_use)
        else:
            # If no history yet, assume 0% usage
            average_usage.append(0.0)

    # Check for throttling (frequency-based alert)
    throttling_threshold = maximum_frequency * THROTTLING_ALERT_THRESHOLD
    is_throttling = any(avg < throttling_threshold for avg in average_frequencies)

    # Check for high CPU usage
    high_usage_cores = sum(1 for avg in average_usage if avg > CPU_USAGE_HIGH_THRESHOLD)
    warning_usage_cores = sum(1 for avg in average_usage if avg > CPU_USAGE_WARNING_THRESHOLD)

    # Determine primary alert type (prioritize critical conditions)
    alert_active = False
    alert_type = "normal"
    
    if is_throttling:
        alert_active = True
        alert_type = "throttling"
    elif high_usage_cores > 0:
        alert_active = True
        alert_type = f"high_usage_{high_usage_cores}_cores"
    elif warning_usage_cores > 0:
        alert_active = True
        alert_type = f"warning_usage_{warning_usage_cores}_cores"

    return alert_active, alert_type, average_frequencies, average_usage


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


def draw_statistics_box(screen, box_position, average_frequencies, average_usage, maximum_frequency, is_alert_mode, minimum_averages):
    """
    Draw the statistics box showing frequency and usage averages.

    Args:
        screen: The curses screen object
        box_position: Tuple of (x, y, width, height) for box placement
        average_frequencies: List of average frequencies for each core
        average_usage: List of average usage percentages for each core
        maximum_frequency: Maximum frequency capability
        is_alert_mode: Whether we're currently in alert mode (affects colors)
        minimum_averages: List of minimum average frequencies for each core (None until window is full)
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
        header_text = ' Core  Freq  %  Usage%  Min% '
        padding_needed = box_width - 2 - len(header_text)  # -2 for the │ characters
        header = '│' + header_text + ' ' * padding_needed + '│'
        screen.addstr(box_y + 1, box_x, header, box_color)

        # Draw the separator line
        separator = '├' + '─' * (box_width - 2) + '┤'
        screen.addstr(box_y + 2, box_x, separator, box_color)

        # Draw frequency and usage info for each core
        for core_index, average_freq in enumerate(average_frequencies):
            # Calculate what percentage this represents of maximum frequency
            frequency_percentage = (average_freq / maximum_frequency) * 100
            
            # Get usage percentage for this core
            usage_percentage = average_usage[core_index]
            
            # Get minimum average frequency for this core and convert to percentage
            min_avg = minimum_averages[core_index]
            min_pct_str = f'{(min_avg / maximum_frequency * 100):>3.0f}%' if min_avg is not None else '---'

            # Format the line with fixed width to ensure straight right border
            content_text = f'  {core_index:<2} {average_freq:>4.0f} {frequency_percentage:>2.0f}% {usage_percentage:>5.1f}%  {min_pct_str} '
            padding_needed = box_width - 2 - len(content_text)  # -2 for the │ characters
            info_line = '│' + content_text + ' ' * padding_needed + '│'

            line_y = box_y + 3 + core_index
            if line_y < screen_height:
                # Choose color based on usage level
                if usage_percentage > CPU_USAGE_HIGH_THRESHOLD:
                    line_color = curses.color_pair(2)  # Red for high usage
                elif usage_percentage > CPU_USAGE_WARNING_THRESHOLD:
                    line_color = curses.color_pair(6) | curses.A_BOLD  # Bold yellow for warning
                else:
                    line_color = text_color  # Normal color
                    
                screen.addstr(line_y, box_x, info_line, line_color)

        # Draw the bottom border
        bottom_border = '└' + '─' * (box_width - 2) + '┘'
        bottom_y = box_y + 3 + number_of_cores
        if bottom_y < screen_height:
            screen.addstr(bottom_y, box_x, bottom_border, box_color)


def draw_alert_banner(screen, screen_width, alert_type):
    """
    Draw the warning banner at the top based on alert type.

    Args:
        screen: The curses screen object
        screen_width: Width of the terminal screen
        alert_type: String describing the type of alert to display
    """
    # Generate warning message based on alert type
    if alert_type == "throttling":
        warning_message = ' ⚠  THROTTLING: avg freq below 50% of max ⚠ '
    elif alert_type.startswith("high_usage_"):
        cores = alert_type.split('_')[2]
        warning_message = f' ⚠  HIGH CPU LOAD: {cores} cores >90% usage ⚠ '
    elif alert_type.startswith("warning_usage_"):
        cores = alert_type.split('_')[2]
        warning_message = f' ⚠  CPU WARNING: {cores} cores >70% usage ⚠ '
    else:
        warning_message = ' ⚠  CPU ALERT DETECTED ⚠ '

    # Center the message on the screen
    banner_x = max(0, (screen_width - len(warning_message)) // 2)

    # Draw at the top of the screen with bold white text on red background
    alert_style = curses.color_pair(4) | curses.A_BOLD
    screen.addstr(0, banner_x, warning_message, alert_style)


def draw_frequency_graphs(screen, graph_area, frequency_histories, current_frequencies, usage_histories, current_usage, maximum_frequency, is_alert_mode, stats_box_width):
    """
    Draw the real-time frequency and usage graphs for each CPU core.

    Args:
        screen: The curses screen object
        graph_area: Tuple of (x, y, width, height) for graph placement
        frequency_histories: List of deque objects with frequency history
        current_frequencies: List of current frequency values
        usage_histories: List of deque objects with usage history
        current_usage: List of current usage percentages
        maximum_frequency: Maximum frequency capability
        is_alert_mode: Whether we're in alert mode (affects colors)
    """
    graph_x, graph_y, graph_width, graph_height = graph_area
    number_of_cores = len(frequency_histories)

    # Unicode block characters for drawing the frequency bars (low to high)
    frequency_bars = '▁▂▃▄▅▆▇█'

    # Calculate how many rows each core gets for its graphs (frequency + usage = 2 lines)
    rows_per_core = max(2, graph_height // number_of_cores)

    # Choose graph colors based on alert mode
    if is_alert_mode:
        freq_graph_color = curses.color_pair(2)  # Red during alerts
        usage_graph_color = curses.color_pair(2)  # Red during alerts
        label_color = curses.color_pair(4)  # White on red during alerts
    else:
        freq_graph_color = curses.color_pair(1)  # Green for frequency
        usage_graph_color = curses.color_pair(5)  # Cyan for usage
        label_color = curses.color_pair(6)  # Yellow normally

    # Draw frequency and usage graphs for each CPU core
    for core_index, core_freq_history in enumerate(frequency_histories):
        # Calculate the vertical position for this core's graphs (frequency + usage)
        freq_y_position = graph_y + core_index * rows_per_core
        usage_y_position = freq_y_position + 1

        # Skip if this would go off the bottom of the screen
        screen_height, screen_width = screen.getmaxyx()
        if usage_y_position >= screen_height - 1:
            break

        # Draw the core label on the frequency line (e.g., "C0 ")
        core_label = f'C{core_index} '
        screen.addstr(freq_y_position, graph_x, core_label, label_color | curses.A_BOLD)
        
        # Draw usage indicator on the usage line
        usage_label = '   U'
        screen.addstr(usage_y_position, graph_x, usage_label, label_color)

        # Calculate how much horizontal space we have for the graphs
        frequency_display_sample = f' {current_frequencies[core_index]:>7.0f}/{maximum_frequency:.0f} MHz'
        usage_display_sample = f' {current_usage[core_index]:>5.1f}%'
        space_needed_for_freq_display = len(frequency_display_sample)
        space_needed_for_usage_display = len(usage_display_sample)

        # Use the larger of the two display widths for consistent alignment
        space_needed_for_display = max(space_needed_for_freq_display, space_needed_for_usage_display)
        
        # Calculate actual available width for the graph bars
        available_graph_width = (graph_width - len(core_label) - 
                                space_needed_for_display - 2)  # 2 chars margin

        # FREQUENCY GRAPH - Get the most recent frequency samples
        recent_freq_samples = list(core_freq_history)[-available_graph_width:]
        padding_needed = available_graph_width - len(recent_freq_samples)

        # Draw the frequency history as bars
        for sample_index, frequency_sample in enumerate(recent_freq_samples):
            bar_x_position = graph_x + len(core_label) + padding_needed + sample_index
            frequency_percentage = min(1.0, frequency_sample / maximum_frequency)
            bar_character_index = int(frequency_percentage * (len(frequency_bars) - 1))
            bar_character = frequency_bars[bar_character_index]

            if (bar_x_position < graph_width and 
                freq_y_position < screen_height - 1 and 
                bar_x_position >= 0):
                screen.addstr(freq_y_position, bar_x_position, bar_character, freq_graph_color)

        # USAGE GRAPH - Get the most recent usage samples
        core_usage_history = usage_histories[core_index]
        recent_usage_samples = list(core_usage_history)[-available_graph_width:]
        padding_needed = available_graph_width - len(recent_usage_samples)

        # Draw the usage history as bars
        for sample_index, usage_sample in enumerate(recent_usage_samples):
            bar_x_position = graph_x + len(usage_label) + padding_needed + sample_index
            usage_percentage = min(1.0, usage_sample / 100.0)  # Convert to 0-1 range
            bar_character_index = int(usage_percentage * (len(frequency_bars) - 1))
            bar_character = frequency_bars[bar_character_index]

            if (bar_x_position < graph_width and 
                usage_y_position < screen_height - 1 and 
                bar_x_position >= 0):
                screen.addstr(usage_y_position, bar_x_position, bar_character, usage_graph_color)

        # Draw current values after the graphs
        freq_display_x = len(core_label) + available_graph_width + 1
        usage_display_x = len(usage_label) + available_graph_width + 1

        # Draw frequency display
        current_freq = current_frequencies[core_index]
        frequency_display = f' {current_freq:>7.0f}/{maximum_frequency:.0f} MHz'
        if (freq_display_x + len(frequency_display) < screen_width and 
            freq_y_position < screen_height - 1):
            screen.addstr(freq_y_position, freq_display_x, frequency_display, label_color)

        # Draw usage display  
        usage_display = f' {current_usage[core_index]:>5.1f}%'
        if (usage_display_x + len(usage_display) < screen_width and 
            usage_y_position < screen_height - 1):
            screen.addstr(usage_y_position, usage_display_x, usage_display, label_color)


def main_display_loop(screen, frequency_histories, usage_histories, maximum_frequency, minimum_averages):
    """
    Main display loop that continuously updates the CPU monitor.

    This is the core loop that:
    1. Reads current CPU frequencies and usage
    2. Updates frequency and usage histories
    3. Detects alert conditions (throttling, high usage)
    4. Draws the complete interface
    5. Sleeps until next update

    Args:
        screen: The curses screen object
        frequency_histories: List of deque objects for storing frequency history
        usage_histories: List of deque objects for storing usage history
        maximum_frequency: Maximum frequency capability of the CPU
        minimum_averages: List to track minimum average frequencies after window is full
    """
    # Set up colors for the terminal display
    setup_terminal_colors()

    number_of_cores = len(frequency_histories)

    # ========================================================================
    # MAIN DISPLAY LOOP - This runs continuously until the user exits
    # ========================================================================
    while True:
        # Step 1: Get the current frequency and usage of each CPU core
        current_frequencies, _ = get_cpu_frequencies()
        current_usage = get_cpu_usage()

        # Step 2: Add the new frequency and usage readings to our history
        for core_index, current_frequency in enumerate(current_frequencies):
            frequency_histories[core_index].append(current_frequency)
            usage_histories[core_index].append(current_usage[core_index])

        # Step 2.5: Update minimum average frequencies (start tracking immediately)
        for core_index, core_history in enumerate(frequency_histories):
            if len(core_history) > 0:  # Have at least one sample
                current_average = sum(core_history) / len(core_history)
                if minimum_averages[core_index] is None:
                    # First time, initialize with current average
                    minimum_averages[core_index] = current_average
                else:
                    # Update minimum if current average is lower
                    minimum_averages[core_index] = min(minimum_averages[core_index], current_average)

        # Step 3: Clear the screen to prepare for new display
        screen.erase()

        # Step 4: Get current screen dimensions
        screen_height, screen_width = screen.getmaxyx()

        # Step 5: Check for alert conditions (throttling, high usage)
        alert_active, alert_type, average_frequencies, average_usage = detect_alerts(
            frequency_histories, usage_histories, maximum_frequency
        )

        # Step 6: Set background color for alert mode
        if alert_active:
            # Red background during alerts
            screen.bkgd(' ', curses.color_pair(3))

        # Step 7: Calculate layout dimensions

        # Statistics box (right side of screen) - wider to accommodate usage column
        stats_box_width = 42
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
            average_usage,
            maximum_frequency,
            alert_active,
            minimum_averages
        )

        # Draw the alert banner if we're in alert mode
        if alert_active:
            draw_alert_banner(screen, screen_width, alert_type)

        # Draw the frequency and usage graphs for each core
        draw_frequency_graphs(
            screen,
            (graph_area_x, graph_area_y, graph_area_width, graph_area_height),
            frequency_histories,
            current_frequencies,
            usage_histories,
            current_usage,
            maximum_frequency,
            alert_active,
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
    print(f"Starting CPU monitor for {number_of_cores} cores...")
    print(f"Maximum frequency: {maximum_frequency:.0f} MHz")
    print(f"Monitoring: Frequency & CPU Usage")
    
    # Initialize CPU usage monitoring (required for accurate measurements)
    print("Initializing CPU usage monitoring...")
    psutil.cpu_percent(percpu=True)  # Baseline call - discarded
    time.sleep(0.5)  # Short wait to establish baseline
    
    print(f"Press Ctrl+C to exit")
    print("")

    # Create history storage for each core
    # Each deque will automatically maintain only the most recent HISTORY_SECONDS values
    frequency_histories = [
        deque(maxlen=HISTORY_SECONDS) for _ in range(number_of_cores)
    ]
    
    # Create usage history storage for each core
    usage_histories = [
        deque(maxlen=HISTORY_SECONDS) for _ in range(number_of_cores)
    ]
    
    # Create minimum average frequency tracking for each core (starts as None until window is full)
    minimum_averages = [None for _ in range(number_of_cores)]

    # Launch the terminal interface
    # curses.wrapper handles terminal setup/cleanup automatically
    try:
        curses.wrapper(
            lambda screen: main_display_loop(screen, frequency_histories, usage_histories, maximum_frequency, minimum_averages)
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
