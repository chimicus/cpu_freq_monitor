# CPU Monitor Enhancement TODO

## Current Features ✅ COMPLETED
- Real-time CPU frequency monitoring for all cores
- 60-second rolling averages with visual frequency graphs
- Throttling alerts when frequency drops below 50% of maximum
- Color-coded terminal interface with Unicode block character graphs
- Minimum average percentage tracking
- **✅ NEW: CPU usage percentage monitoring with dual graphs**
- **✅ NEW: Enhanced alert system (throttling + high usage + warning levels)**
- **✅ NEW: Dual graph display with frequency and usage graphs per core**
- **✅ NEW: Independent color coding (green frequency, cyan usage)**
- **✅ NEW: Comprehensive test suite with 24+ unit and integration tests**

## Planned Enhancements

### 1. Multi-Metric Data Collection
- [x] **✅ COMPLETED: Add CPU usage percentage monitoring**
  - ✅ Integrate `psutil.cpu_percent(percpu=True)` for per-core usage data
  - ✅ Store usage history alongside frequency history
  - ✅ Add usage statistics to the statistics box

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
- [x] **✅ PARTIALLY COMPLETED: Redesign statistics box for dual metrics**
  - ✅ Expand columns: `Core | Freq | % | Usage% | Min%` 
  - ✅ Add usage percentages
  - ✅ Show usage percentage with color coding (red >90%, yellow >70%, green <70%)
  - ❌ TODO: Add temperature column when temperature monitoring is implemented

- [x] **✅ PARTIALLY COMPLETED: Create dual-metric graphing system**
  - ✅ Implemented dual graphs (frequency + usage) displayed simultaneously
  - ✅ Different colors for each metric type (green frequency, cyan usage)
  - ✅ Independent scaling: frequency (0-100% of max), usage (0-100%)
  - ❌ TODO: Add toggle functionality to switch between frequency/temperature/usage graphs
  - ❌ TODO: Add keyboard shortcuts: 'f' for frequency, 't' for temperature, 'u' for usage

- [x] **✅ COMPLETED: Enhanced alert system**
  - ✅ Multi-condition alerts: throttling (frequency) + high load (usage) + warning levels
  - ✅ Priority-based alert display (throttling > high usage > warning usage)
  - ✅ Alert banner showing specific issues: "HIGH LOAD: 4 cores >90%" or "CPU WARNING: 2 cores >70%"

### 5. Configuration Updates
- [x] **✅ PARTIALLY COMPLETED: Add new configuration constants**
  - ❌ TODO: `TEMPERATURE_WARNING_THRESHOLD = 80`  # °C
  - ❌ TODO: `TEMPERATURE_CRITICAL_THRESHOLD = 90` # °C  
  - ✅ `CPU_USAGE_HIGH_THRESHOLD = 90`       # %
  - ✅ `CPU_USAGE_WARNING_THRESHOLD = 70`    # %
  - ❌ TODO: `ROUND_ROBIN_INTERVAL_MS = 333`       # milliseconds between metric samples

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

---

## ✅ RECENTLY COMPLETED FEATURES

### Dual Graph CPU Usage Monitoring (Completed)
**What we implemented:**
- **Real-time CPU usage tracking**: Added `get_cpu_usage()` function with proper psutil initialization
- **Dual graph display**: Each core now shows two lines:
  ```
  C0 ▁▂▃▄▅▆▇█▇▆▅▄ 2500/3000 MHz
     U ▁▂▃▄▃▂▁▂▃▄  25.5%
  ```
- **Independent scaling**: Frequency graphs scale 0-100% of max frequency, usage graphs scale 0-100% CPU utilization
- **Color differentiation**: Green for frequency graphs, cyan for usage graphs (red for both during alerts)
- **Enhanced statistics box**: Now displays both frequency and usage percentages with color coding
- **Smart alert system**: 
  - Throttling detection (frequency-based)
  - High CPU usage alerts (>90%)
  - Warning level alerts (>70%)
  - Priority-based alert handling
- **Comprehensive testing**: 24+ unit tests, integration tests, and functional tests

### Technical Implementation Details
- **Data collection**: Fixed psutil initialization issue that was causing 0.0% usage readings
- **Main loop enhancement**: Added usage data collection alongside frequency monitoring
- **Graph rendering**: Modified `draw_frequency_graphs()` to render both frequency and usage with proper spacing
- **Alert detection**: Enhanced `detect_alerts()` to handle multiple alert conditions with priority
- **History tracking**: Dual deque structures maintain 60-second rolling averages for both metrics

### Test Coverage
- `test_dual_graph_functionality.py`: 12 comprehensive unit tests
- `test_graph_drawing_integration.py`: Integration tests with mocked curses  
- `test_dual_graphs.py`: Functional tests with real CPU data
- All existing tests still passing + new test coverage

**Next Priority**: Temperature monitoring and round-robin sampling implementation