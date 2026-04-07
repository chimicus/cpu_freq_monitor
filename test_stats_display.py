#!/usr/bin/env python3
"""
Test what the statistics box would display without curses.
"""

import cpu_freq_monitor
from collections import deque

def test_stats_display():
    """Test the exact data that would be shown in the statistics box."""
    
    print("Testing Statistics Box Display")
    print("=" * 40)
    
    # Get initial data
    frequencies, max_freq = cpu_freq_monitor.get_cpu_frequencies()
    usage = cpu_freq_monitor.get_cpu_usage()
    
    num_cores = len(frequencies)
    
    # Create histories and add data (like main loop does)
    freq_histories = [deque(maxlen=60) for _ in range(num_cores)]
    usage_histories = [deque(maxlen=60) for _ in range(num_cores)]
    min_averages = [None for _ in range(num_cores)]
    
    # Add current data to histories
    for i in range(num_cores):
        freq_histories[i].append(frequencies[i])
        usage_histories[i].append(usage[i])
    
    # Calculate averages like the detect_alerts function does
    alert_active, alert_type, avg_frequencies, avg_usage = cpu_freq_monitor.detect_alerts(
        freq_histories, usage_histories, max_freq
    )
    
    print(f"Alert Status: {alert_active} ({alert_type})")
    print()
    print("Statistics Box Content:")
    print(" Core  Freq  %  Usage%  Min%")
    print("------|-----|---|-------|----")
    
    for i in range(min(8, num_cores)):
        freq_pct = (avg_frequencies[i] / max_freq) * 100
        usage_pct = avg_usage[i]
        min_pct_str = "---"
        
        print(f"  {i:2d}  {avg_frequencies[i]:>4.0f} {freq_pct:>2.0f}% {usage_pct:>5.1f}%  {min_pct_str}")
    
    if num_cores > 8:
        print(f"... and {num_cores - 8} more cores")
    
    print()
    print("Raw data for debugging:")
    print(f"Raw frequencies: {[f'{f:.0f}' for f in frequencies[:4]]}...")
    print(f"Raw usage: {usage[:4]}...")
    print(f"Avg frequencies: {[f'{f:.0f}' for f in avg_frequencies[:4]]}...")
    print(f"Avg usage: {avg_usage[:4]}...")

if __name__ == "__main__":
    test_stats_display()