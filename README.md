# CPU Frequency Monitor

A real-time CPU frequency monitoring tool that displays per-core frequency information with visual graphs and alerts for potential throttling.

## Features

- Real-time frequency monitoring for all CPU cores
- Visual graphs using Unicode block characters
- 60-second rolling average display
- Throttling alerts when average frequency drops below 50% of maximum
- Color-coded interface with alert highlighting
- Compact terminal-based interface

## Requirements

- Python 3.x
- psutil library

## Installation

1. Clone or download this repository
2. Install the required dependency:
   ```bash
   pip install psutil
   ```

## Usage

Run the monitor:
```bash
python3 cpu_freq_monitor.py
```

The interface displays:
- **Left side**: Real-time frequency graphs for each CPU core
- **Right side**: 60-second average frequencies and percentages
- **Top**: Warning banner when throttling is detected

Press `Ctrl+C` to exit.

## Configuration

You can modify these constants at the top of the file:
- `HISTORY`: Number of seconds of history to track (default: 60)
- `UPDATE_HZ`: Updates per second (default: 1)
- `WARN_PCT`: Alert threshold as percentage of max frequency (default: 0.50)

## Alert System

The monitor triggers visual alerts when any core's 60-second average frequency falls below 50% of the maximum frequency, which may indicate:
- Thermal throttling
- Power management
- System load balancing
- Hardware issues

## License

This project is provided as-is for monitoring CPU performance.