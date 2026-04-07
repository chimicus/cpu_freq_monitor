#!/usr/bin/env python3
"""
Debug the exact main program logic without curses to see what's really happening.
"""

import sys; sys.path.insert(0, "."); from src import cpu_freq_monitor
from collections import deque
import time

def simulate_exact_main_logic():
    """Simulate the exact logic from the main program."""
    
    print("=== Simulating Exact Main Program Logic ===")
    
    # Step 1: Initialize exactly like main() function
    try:
        initial_frequencies, maximum_frequency = cpu_freq_monitor.get_cpu_frequencies()
    except Exception as error:
        print(f"Error reading CPU frequencies: {error}")
        return

    number_of_cores = len(initial_frequencies)
    print(f"Starting CPU monitor for {number_of_cores} cores...")
    print(f"Maximum frequency: {maximum_frequency:.0f} MHz")
    print("Monitoring: Frequency & CPU Usage")
    print()

    # Create history storage exactly like main()
    frequency_histories = [deque(maxlen=60) for _ in range(number_of_cores)]
    usage_histories = [deque(maxlen=60) for _ in range(number_of_cores)]
    minimum_averages = [None for _ in range(number_of_cores)]

    # Simulate main_display_loop for a few iterations
    for iteration in range(3):
        print(f"\n--- Iteration {iteration + 1} ---")
        
        # Step 1: Get current data (exact same as main loop)
        print("Getting current frequencies and usage...")
        current_frequencies, _ = cpu_freq_monitor.get_cpu_frequencies()
        current_usage = cpu_freq_monitor.get_cpu_usage()
        
        print(f"Current frequencies: {[f'{f:.0f}' for f in current_frequencies[:4]]}...")
        print(f"Current usage: {current_usage[:4]}...")

        # Step 2: Add to histories (exact same as main loop)
        for core_index, current_frequency in enumerate(current_frequencies):
            frequency_histories[core_index].append(current_frequency)
        
        for core_index, usage in enumerate(current_usage):
            usage_histories[core_index].append(usage)

        # Step 2.5: Update minimum averages (exact same as main loop)
        for core_index, core_history in enumerate(frequency_histories):
            if len(core_history) > 0:
                current_average = sum(core_history) / len(core_history)
                if minimum_averages[core_index] is None:
                    minimum_averages[core_index] = current_average
                else:
                    minimum_averages[core_index] = min(minimum_averages[core_index], current_average)

        # Step 5: Check for alerts (exact same as main loop)
        alert_active, alert_type, average_frequencies, average_usage = cpu_freq_monitor.detect_alerts(
            frequency_histories, usage_histories, maximum_frequency
        )
        
        print(f"Alert status: {alert_active} ({alert_type})")
        print(f"Average frequencies: {[f'{f:.0f}' for f in average_frequencies[:4]]}...")
        print(f"Average usage: {average_usage[:4]}...")

        # Simulate what would be displayed in statistics box
        print("\nWould display in statistics box:")
        print(" Core  Freq  %  Usage%  Min%")
        print("------|-----|---|-------|----")
        
        for core_index in range(min(4, number_of_cores)):
            frequency_percentage = (average_frequencies[core_index] / maximum_frequency) * 100
            usage_percentage = average_usage[core_index]
            min_avg = minimum_averages[core_index]
            min_pct_str = f'{(min_avg / maximum_frequency * 100):>3.0f}%' if min_avg is not None else '---'
            
            # This is the EXACT formatting from the real code
            content_text = f'  {core_index:<2} {average_frequencies[core_index]:>4.0f} {frequency_percentage:>2.0f}% {usage_percentage:>5.1f}%  {min_pct_str} '
            print(f"{content_text}")
        
        print(f"\nSleeping 1 second...")
        time.sleep(1.0)
    
    print("\n=== End Simulation ===")

if __name__ == "__main__":
    simulate_exact_main_logic()