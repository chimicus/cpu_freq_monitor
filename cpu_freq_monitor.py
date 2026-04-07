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

# Temperature graph scale (fixed range for consistent visualization)
TEMPERATURE_SCALE_MIN = 40.0  # °C - minimum temperature for graph scale
TEMPERATURE_SCALE_MAX = 100.0 # °C - maximum temperature for graph scale

# Layout constants for triple graph display
ROWS_PER_CORE_WITH_TEMPERATURE = 3  # Frequency + Usage + Temperature lines per core

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
    Retrieve current CPU temperatures for all logical cores.

    Uses psutil to read temperature sensor data from physical cores and maps them
    to logical cores. For hyperthreaded systems, each physical core temperature
    is applied to both logical cores (e.g., physical core 0 → logical cores 0,1).

    Returns:
        list or None: List of current temperatures in °C for each logical core, or None if
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
        
        physical_core_temps = []
        
        # Try Intel coretemp sensors first (most common)
        if 'coretemp' in sensor_data:
            for sensor in sensor_data['coretemp']:
                # Look for individual core temperatures (skip package/socket temps)
                if sensor.label and 'Core' in sensor.label:
                    temp = sensor.current
                    # Validate temperature is reasonable (0-150°C)
                    if 0 <= temp <= 150:
                        physical_core_temps.append(temp)
        
        # Try AMD k10temp sensors if coretemp not available or insufficient
        elif 'k10temp' in sensor_data:
            for sensor in sensor_data['k10temp']:
                # AMD sensors may have different label patterns
                if sensor.label:
                    temp = sensor.current
                    # Validate temperature range
                    if 0 <= temp <= 150:
                        physical_core_temps.append(temp)
        
        # Try other common sensor names
        else:
            # Look for any other temperature sensors
            for sensor_name, sensors in sensor_data.items():
                for sensor in sensors:
                    if sensor.label and sensor.current:
                        temp = sensor.current
                        if 0 <= temp <= 150:
                            physical_core_temps.append(temp)
        
        if not physical_core_temps:
            return None
        
        # Map physical core temperatures to logical cores  
        # Get CPU topology info
        logical_core_count = psutil.cpu_count(logical=True)
        physical_core_count = psutil.cpu_count(logical=False)
        
        if logical_core_count and physical_core_count:
            logical_cores_per_physical = logical_core_count // physical_core_count
        else:
            # Fallback: assume no hyperthreading
            logical_cores_per_physical = 1
        
        # Create temperature mapping for all logical cores
        logical_core_temps = []
        for logical_core_index in range(logical_core_count):
            # Calculate which physical core this logical core belongs to
            physical_core_index = logical_core_index // logical_cores_per_physical
            
            # If we have temperature data for this physical core, use it
            if physical_core_index < len(physical_core_temps):
                logical_core_temps.append(physical_core_temps[physical_core_index])
            else:
                # No temperature data available for this physical core
                logical_core_temps.append(None)
        
        return logical_core_temps
        
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

    # Check for warning-level CPU usage only (removed high usage alerts per user request)
    warning_usage_cores = sum(1 for avg in average_usage if avg > CPU_USAGE_WARNING_THRESHOLD)

    # Determine primary alert type (prioritize critical conditions)
    alert_active = False
    alert_type = "normal"
    
    if is_throttling:
        alert_active = True
        alert_type = "throttling"
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


def draw_statistics_box(screen, box_position, average_frequencies, average_usage, average_temperatures, maximum_frequency, is_alert_mode, minimum_averages):
    """
    Draw the statistics box showing frequency, usage, and temperature averages.

    Args:
        screen: The curses screen object
        box_position: Tuple of (x, y, width, height) for box placement
        average_frequencies: List of average frequencies for each core
        average_usage: List of average usage percentages for each core
        average_temperatures: List of average temperatures for each core (or None if unavailable)
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
        header_text = ' Core  Freq  %  Usage%  Temp  Min% '
        padding_needed = box_width - 2 - len(header_text)  # -2 for the │ characters
        header = '│' + header_text + ' ' * padding_needed + '│'
        screen.addstr(box_y + 1, box_x, header, box_color)

        # Draw the separator line
        separator = '├' + '─' * (box_width - 2) + '┤'
        screen.addstr(box_y + 2, box_x, separator, box_color)

        # Draw frequency, usage, and temperature info for each core
        for core_index, average_freq in enumerate(average_frequencies):
            # Calculate what percentage this represents of maximum frequency
            frequency_percentage = (average_freq / maximum_frequency) * 100
            
            # Get usage percentage for this core
            usage_percentage = average_usage[core_index]
            
            # Get temperature for this core
            if average_temperatures and core_index < len(average_temperatures):
                temp_value = average_temperatures[core_index]
                if temp_value is not None:
                    temp_str = f'{temp_value:>3.0f}°C'
                else:
                    temp_str = ' N/A '
            else:
                temp_str = ' N/A '
            
            # Get minimum average frequency for this core and convert to percentage
            min_avg = minimum_averages[core_index]
            min_pct_str = f'{(min_avg / maximum_frequency * 100):>3.0f}%' if min_avg is not None else '---'

            # Format the line with fixed width to ensure straight right border
            content_text = f'  {core_index:<2} {average_freq:>4.0f} {frequency_percentage:>2.0f}% {usage_percentage:>5.1f}% {temp_str} {min_pct_str} '
            padding_needed = box_width - 2 - len(content_text)  # -2 for the │ characters
            info_line = '│' + content_text + ' ' * padding_needed + '│'

            line_y = box_y + 3 + core_index
            if line_y < screen_height:
                # Choose color based on the most critical alert condition
                if average_temperatures and core_index < len(average_temperatures):
                    temp_value = average_temperatures[core_index]
                    if temp_value is not None and temp_value >= TEMPERATURE_CRITICAL_THRESHOLD:
                        line_color = curses.color_pair(2) | curses.A_BOLD  # Bold red for critical temp
                    elif temp_value is not None and temp_value >= TEMPERATURE_WARNING_THRESHOLD:
                        line_color = curses.color_pair(2)  # Red for warning temp
                    elif usage_percentage > CPU_USAGE_WARNING_THRESHOLD:
                        line_color = curses.color_pair(6) | curses.A_BOLD  # Bold yellow for warning usage
                    else:
                        line_color = text_color  # Normal color
                else:
                    # No temperature data, fall back to usage-based coloring
                    if usage_percentage > CPU_USAGE_WARNING_THRESHOLD:
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


# ============================================================================
# TEMPERATURE GRAPH HELPER FUNCTIONS
# ============================================================================

def temperature_to_graph_index(temperature):
    """
    Convert a temperature value to a graph character index (0-7).
    
    Maps temperatures from 40-100°C to Unicode bar character indices.
    Values outside range are clamped to 0-7.
    
    Args:
        temperature: Temperature in Celsius
    
    Returns:
        int: Index from 0-7 for Unicode bar characters ▁▂▃▄▅▆▇█
    """
    if temperature is None:
        return 0  # Minimum character for None values
    
    # Clamp temperature to scale range
    clamped_temp = max(TEMPERATURE_SCALE_MIN, min(TEMPERATURE_SCALE_MAX, temperature))
    
    # Convert to 0-1 range
    temp_range = TEMPERATURE_SCALE_MAX - TEMPERATURE_SCALE_MIN
    normalized = (clamped_temp - TEMPERATURE_SCALE_MIN) / temp_range
    
    # Convert to 0-7 index
    return int(normalized * 7)

def get_temperature_graph_characters():
    """
    Get the Unicode characters used for temperature graphs.
    
    Returns:
        list: Unicode bar characters from low to high
    """
    return ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

def temperature_history_to_graph(temperature_history):
    """
    Convert a deque of temperature readings to a graph string.
    
    Args:
        temperature_history: deque of temperature values (floats or None)
    
    Returns:
        str: String of Unicode bar characters representing temperature history
    """
    if not temperature_history:
        return ""
    
    chars = get_temperature_graph_characters()
    graph_string = ""
    
    for temp in temperature_history:
        char_index = temperature_to_graph_index(temp)
        graph_string += chars[char_index]
    
    return graph_string

def get_temperature_graph_color(alert_active=False):
    """
    Get the appropriate color for temperature graphs.
    
    Args:
        alert_active: Whether we're in alert mode
    
    Returns:
        int: Curses color pair number
    """
    if alert_active:
        return 3  # Red color pair
    else:
        return 4  # Cyan color pair


# ============================================================================
# GRAPH DRAWING FUNCTIONS  
# ============================================================================

def draw_frequency_graphs(screen, graph_area, frequency_histories, current_frequencies, usage_histories, current_usage, temperature_histories, current_temperatures, maximum_frequency, is_alert_mode, stats_box_width):
    """
    Draw the real-time frequency, usage, and temperature graphs for each CPU core.

    Args:
        screen: The curses screen object
        graph_area: Tuple of (x, y, width, height) for graph placement
        frequency_histories: List of deque objects with frequency history
        current_frequencies: List of current frequency values
        usage_histories: List of deque objects with usage history
        current_usage: List of current usage percentages
        temperature_histories: List of deque objects with temperature history
        current_temperatures: List of current temperature values (or None)
        maximum_frequency: Maximum frequency capability
        is_alert_mode: Whether we're in alert mode (affects colors)
    """
    graph_x, graph_y, graph_width, graph_height = graph_area
    number_of_cores = len(frequency_histories)

    # Unicode block characters for drawing the frequency bars (low to high)
    frequency_bars = '▁▂▃▄▅▆▇█'

    # Calculate how many rows each core gets for its graphs (frequency + usage + temperature = 3 lines)
    rows_per_core = max(ROWS_PER_CORE_WITH_TEMPERATURE, graph_height // number_of_cores)

    # Choose graph colors based on alert mode
    if is_alert_mode:
        freq_graph_color = curses.color_pair(2)  # Red during alerts
        usage_graph_color = curses.color_pair(2)  # Red during alerts
        temp_graph_color = curses.color_pair(2)   # Red during alerts
        label_color = curses.color_pair(4)  # White on red during alerts
    else:
        freq_graph_color = curses.color_pair(1)  # Green for frequency
        usage_graph_color = curses.color_pair(5)  # Cyan for usage
        temp_graph_color = curses.color_pair(4)   # Cyan for temperature (different shade)
        label_color = curses.color_pair(6)  # Yellow normally

    # Draw frequency, usage, and temperature graphs for each CPU core
    for core_index, core_freq_history in enumerate(frequency_histories):
        # Calculate the vertical position for this core's graphs (frequency + usage + temperature)
        freq_y_position = graph_y + core_index * rows_per_core
        usage_y_position = freq_y_position + 1
        temp_y_position = freq_y_position + 2

        # Skip if this would go off the bottom of the screen
        screen_height, screen_width = screen.getmaxyx()
        if temp_y_position >= screen_height - 1:
            break

        # Draw the core label on the frequency line (e.g., "C0 ")
        core_label = f'C{core_index} '
        screen.addstr(freq_y_position, graph_x, core_label, label_color | curses.A_BOLD)
        
        # Draw usage indicator on the usage line
        usage_label = '   U'
        screen.addstr(usage_y_position, graph_x, usage_label, label_color)
        
        # Draw temperature indicator on the temperature line
        temp_label = '   T'
        screen.addstr(temp_y_position, graph_x, temp_label, label_color)

        # Calculate how much horizontal space we have for the graphs
        frequency_display_sample = f' {current_frequencies[core_index]:>7.0f}/{maximum_frequency:.0f} MHz'
        usage_display_sample = f' {current_usage[core_index]:>5.1f}%'
        
        # Temperature display (handle None values)
        current_temp = None
        if (current_temperatures and core_index < len(current_temperatures) and 
            current_temperatures[core_index] is not None):
            current_temp = current_temperatures[core_index]
            temp_display_sample = f' {current_temp:>3.0f}°C'
        else:
            temp_display_sample = f' N/A '
            
        space_needed_for_freq_display = len(frequency_display_sample)
        space_needed_for_usage_display = len(usage_display_sample)
        space_needed_for_temp_display = len(temp_display_sample)

        # Use the largest of the three display widths for consistent alignment
        space_needed_for_display = max(space_needed_for_freq_display, 
                                     space_needed_for_usage_display,
                                     space_needed_for_temp_display)
        
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

        # TEMPERATURE GRAPH - Get the most recent temperature samples
        if temperature_histories and core_index < len(temperature_histories):
            core_temp_history = temperature_histories[core_index]
            recent_temp_samples = list(core_temp_history)[-available_graph_width:]
            padding_needed = available_graph_width - len(recent_temp_samples)

            # Draw the temperature history as bars
            for sample_index, temp_sample in enumerate(recent_temp_samples):
                bar_x_position = graph_x + len(temp_label) + padding_needed + sample_index
                
                # Convert temperature to graph index using our helper function
                bar_character_index = temperature_to_graph_index(temp_sample)
                bar_character = frequency_bars[bar_character_index]

                if (bar_x_position < graph_width and 
                    temp_y_position < screen_height - 1 and 
                    bar_x_position >= 0):
                    screen.addstr(temp_y_position, bar_x_position, bar_character, temp_graph_color)

        # Draw current values after the graphs
        freq_display_x = len(core_label) + available_graph_width + 1
        usage_display_x = len(usage_label) + available_graph_width + 1
        temp_display_x = len(temp_label) + available_graph_width + 1

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

        # Draw temperature display
        if (temp_display_x + len(temp_display_sample) < screen_width and 
            temp_y_position < screen_height - 1):
            screen.addstr(temp_y_position, temp_display_x, temp_display_sample, label_color)


def main_display_loop(screen, frequency_histories, usage_histories, temperature_histories, maximum_frequency, minimum_averages):
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
        # Step 1: Get the current frequency, usage, and temperature of each CPU core
        current_frequencies, _ = get_cpu_frequencies()
        current_usage = get_cpu_usage()
        current_temperatures = get_cpu_temperatures()

        # Step 2: Add the new frequency, usage, and temperature readings to our history
        for core_index, current_frequency in enumerate(current_frequencies):
            frequency_histories[core_index].append(current_frequency)
            usage_histories[core_index].append(current_usage[core_index])
            
            # Add temperature data if available
            if current_temperatures and core_index < len(current_temperatures):
                temperature_histories[core_index].append(current_temperatures[core_index])

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
        
        # Calculate temperature averages for display
        average_temperatures = None
        if any(len(temp_hist) > 0 for temp_hist in temperature_histories):
            average_temperatures = []
            for temp_history in temperature_histories:
                if len(temp_history) > 0:
                    avg_temp = sum(temp_history) / len(temp_history)
                    average_temperatures.append(avg_temp)
                else:
                    average_temperatures.append(None)

        # Step 6: Set red background only for critical conditions (throttling OR critical temperature)
        critical_alert = False
        
        # Check for throttling (frequency below 50% of max)
        if alert_type == "throttling":
            critical_alert = True
        
        # Check for critical temperature (any core above 90°C)
        if average_temperatures:
            for temp in average_temperatures:
                if temp is not None and temp >= TEMPERATURE_CRITICAL_THRESHOLD:
                    critical_alert = True
                    break
        
        if critical_alert:
            # Red background for critical conditions only
            screen.bkgd(' ', curses.color_pair(3))
        else:
            # Reset to normal background when no critical alerts
            screen.bkgd(' ', 0)  # Reset to default background

        # Step 7: Calculate layout dimensions

        # Statistics box (right side of screen) - wider to accommodate usage and temperature columns
        stats_box_width = 48
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
            average_temperatures,
            maximum_frequency,
            alert_active,
            minimum_averages
        )

        # Draw the alert banner if we're in alert mode
        if alert_active:
            draw_alert_banner(screen, screen_width, alert_type)

        # Draw the frequency, usage, and temperature graphs for each core
        draw_frequency_graphs(
            screen,
            (graph_area_x, graph_area_y, graph_area_width, graph_area_height),
            frequency_histories,
            current_frequencies,
            usage_histories,
            current_usage,
            temperature_histories,
            current_temperatures,
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
    
    # Create temperature history storage for each core
    temperature_histories = [
        deque(maxlen=HISTORY_SECONDS) for _ in range(number_of_cores)
    ]
    
    # Create minimum average frequency tracking for each core (starts as None until window is full)
    minimum_averages = [None for _ in range(number_of_cores)]

    # Launch the terminal interface
    # curses.wrapper handles terminal setup/cleanup automatically
    try:
        curses.wrapper(
            lambda screen: main_display_loop(screen, frequency_histories, usage_histories, temperature_histories, maximum_frequency, minimum_averages)
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
