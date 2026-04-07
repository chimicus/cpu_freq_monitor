# CPU Monitor Enhancement TODO

## Current Features
- Real-time CPU frequency monitoring for all cores
- 60-second rolling averages with visual frequency graphs
- Throttling alerts when frequency drops below 50% of maximum
- Color-coded terminal interface with Unicode block character graphs
- Minimum average percentage tracking

## Planned Enhancements

### 1. Multi-Metric Data Collection
- [ ] **Add CPU usage percentage monitoring**
  - Integrate `psutil.cpu_percent(percpu=True)` for per-core usage data
  - Store usage history alongside frequency history
  - Add usage statistics to the statistics box

- [ ] **Add CPU temperature monitoring**
  - Implement temperature reading via `psutil.sensors_temperatures()`
  - Handle different temperature sensor sources (coretemp, k10temp, etc.)
  - Store temperature history for each core
  - Add temperature alerts for high values (>80°C warning, >90°C critical)

### 2. Round-Robin Sampling Strategy
- [ ] **Implement 333ms round-robin sampling within 1-second cycles**
  - **t=0ms**: Sample CPU temperatures for all cores
  - **t=333ms**: Sample CPU usage percentages for all cores  
  - **t=666ms**: Sample CPU frequencies for all cores
  - **t=1000ms**: Repeat cycle
  - Maintain separate timing for each metric type
  - Ensure total cycle remains 1 second for UI refresh rate

### 3. Enhanced Data Structures
- [ ] **Expand history storage to support three metrics**
  - Create `MetricHistories` class to manage frequency, usage, and temperature deques
  - Maintain 60-second rolling windows for each metric type
  - Update minimum/maximum tracking for all three metrics

### 4. Enhanced Display System
- [ ] **Redesign statistics box for three metrics**
  - Expand columns: `Core | Freq | % | Temp | Usage | % | Alerts`
  - Add temperature units (°C) and usage percentages
  - Color-code temperature values (green <70°C, yellow 70-80°C, red >80°C)
  - Show usage percentage with color coding (red >90%, yellow >70%, green <70%)

- [ ] **Create multi-metric graphing system**
  - Add toggle functionality to switch between frequency/temperature/usage graphs
  - Implement graph legends showing current metric type
  - Use different Unicode characters or colors for each metric type
  - Add keyboard shortcuts: 'f' for frequency, 't' for temperature, 'u' for usage

- [ ] **Enhanced alert system**
  - Multi-condition alerts: throttling (frequency), overheating (temperature), high load (usage)
  - Priority-based alert display (critical temperature > high usage > throttling)
  - Alert banner showing specific issues: "HIGH TEMP: Core 2 at 95°C" or "HIGH LOAD: 4 cores >95%"

### 5. Configuration Updates
- [ ] **Add new configuration constants**
  - `TEMPERATURE_WARNING_THRESHOLD = 80`  # °C
  - `TEMPERATURE_CRITICAL_THRESHOLD = 90` # °C  
  - `CPU_USAGE_HIGH_THRESHOLD = 90`       # %
  - `CPU_USAGE_WARNING_THRESHOLD = 70`    # %
  - `ROUND_ROBIN_INTERVAL_MS = 333`       # milliseconds between metric samples

### 6. Error Handling & Compatibility
- [ ] **Temperature sensor compatibility**
  - Graceful fallback when temperature sensors unavailable
  - Support multiple sensor types across different hardware
  - Display "N/A" for unavailable temperature readings

- [ ] **Resource usage optimization**
  - Minimize psutil calls by batching metric collection
  - Optimize terminal refresh rates for three concurrent data streams
  - Handle varying metric update frequencies efficiently

### 7. User Interface Improvements
- [ ] **Add help overlay**
  - Keyboard shortcut help ('h' key)
  - Show metric switching commands
  - Display current sampling mode and cycle timing

- [ ] **Status line enhancements**
  - Show next metric to be sampled in round-robin cycle
  - Display system load average alongside CPU metrics
  - Add timestamp of last successful metric collection