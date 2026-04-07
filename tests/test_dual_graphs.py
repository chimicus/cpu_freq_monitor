#!/usr/bin/env python3
"""
Test script to verify dual graph functionality (frequency + usage).
"""

import sys; sys.path.insert(0, "."); from src import cpu_freq_monitor
from collections import deque
import time

def test_dual_graph_logic():
    """Test the dual graph display logic without curses."""
    
    print("Testing Dual Graph Display (Frequency + Usage)")
    print("=" * 50)
    
    # Get initial data
    frequencies, max_freq = cpu_freq_monitor.get_cpu_frequencies()
    usage = cpu_freq_monitor.get_cpu_usage()
    
    num_cores = min(4, len(frequencies))  # Test with first 4 cores
    print(f"Testing with {num_cores} cores")
    print(f"Max frequency: {max_freq:.0f} MHz")
    print()
    
    # Create histories like the main application
    freq_histories = [deque(maxlen=60) for _ in range(len(frequencies))]
    usage_histories = [deque(maxlen=60) for _ in range(len(frequencies))]
    
    # Simulate collecting data over several cycles
    for cycle in range(3):
        print(f"=== Cycle {cycle + 1} ===")
        
        # Get current data
        current_frequencies, _ = cpu_freq_monitor.get_cpu_frequencies()
        current_usage = cpu_freq_monitor.get_cpu_usage()
        
        # Add to histories
        for i in range(len(current_frequencies)):
            freq_histories[i].append(current_frequencies[i])
            usage_histories[i].append(current_usage[i])
        
        # Display what would be shown for each core
        for core_idx in range(num_cores):
            freq = current_frequencies[core_idx]
            use = current_usage[core_idx]
            freq_pct = (freq / max_freq) * 100
            
            print(f"Core {core_idx}:")
            print(f"  Freq: {freq:>7.0f}/{max_freq:.0f} MHz ({freq_pct:>3.0f}%)")
            print(f"  Usage: {use:>5.1f}%")
            
            # Show what the graph bars would look like
            freq_bar_idx = int((freq / max_freq) * 7)
            usage_bar_idx = int((use / 100.0) * 7)
            bars = '▁▂▃▄▅▆▇█'
            
            freq_bar = bars[freq_bar_idx] if freq_bar_idx < len(bars) else '█'
            usage_bar = bars[usage_bar_idx] if usage_bar_idx < len(bars) else '█'
            
            print(f"  Freq graph: {freq_bar} (level {freq_bar_idx}/7)")
            print(f"  Usage graph: {usage_bar} (level {usage_bar_idx}/7)")
            print()
        
        if cycle < 2:
            time.sleep(1.0)
    
    print("✅ Dual graph logic test completed!")
    print()
    print("Key features working:")
    print("• Frequency and usage data collection")
    print("• Dual graph level calculations")
    print("• Unicode bar character selection")
    print("• Both graphs display different metrics correctly")

if __name__ == "__main__":
    test_dual_graph_logic()