#!/usr/bin/env python3
"""
Debug script to track down the CPU usage issue.
"""

import cpu_freq_monitor
import psutil
import time

def debug_cpu_usage():
    print("=== CPU Usage Debug ===")
    
    # Test 1: Direct psutil calls
    print("\n1. Testing direct psutil calls:")
    psutil.cpu_percent(percpu=True)  # Initialize
    time.sleep(0.1)
    direct_usage = psutil.cpu_percent(percpu=True)
    print(f"   Direct psutil: {direct_usage[:4]}...")
    
    # Test 2: Our function
    print("\n2. Testing our get_cpu_usage function:")
    usage = cpu_freq_monitor.get_cpu_usage()
    print(f"   Our function: {usage[:4]}...")
    
    # Test 3: Initialize and call again
    print("\n3. Re-initialize and test again:")
    psutil.cpu_percent(percpu=True)  # Re-initialize
    time.sleep(1.0)
    usage2 = cpu_freq_monitor.get_cpu_usage()
    print(f"   After 1s wait: {usage2[:4]}...")
    
    # Test 4: Check the exact implementation
    print("\n4. Testing exact main loop sequence:")
    
    # Initialize like main_display_loop does
    psutil.cpu_percent(percpu=True)
    
    for i in range(3):
        print(f"\n   Loop iteration {i+1}:")
        
        # Get frequencies
        frequencies, max_freq = cpu_freq_monitor.get_cpu_frequencies()
        print(f"     Frequencies: {[f'{f:.0f}' for f in frequencies[:4]]}...")
        
        # Get usage
        usage = cpu_freq_monitor.get_cpu_usage()
        print(f"     Usage: {usage[:4]}...")
        
        time.sleep(1.0)

if __name__ == "__main__":
    debug_cpu_usage()