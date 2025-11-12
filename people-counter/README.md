# People Counter System with GridEYE AMG8833

Real-time people counting system using 8×8 GridEYE thermal sensor and Raspberry Pi 4B. Based on the research paper "Measuring People-Flow Through Doorways using Easy-to-Install IR Array Sensors".

## Features

- **Real-time Detection**: 10 FPS processing for accurate tracking
- **High Accuracy**: 93% accuracy in controlled environments
- **Privacy-Preserving**: Low-resolution thermal imaging (8×8 pixels)
- **Easy Installation**: Flexible mounting options (side or top of door)
- **Low Cost**: ~$50 total hardware cost
- **No Training Required**: Works out of the box

## Hardware Requirements

- Raspberry Pi 4B (or 3B+)
- Panasonic GridEYE AMG8833 IR Array Sensor
- MicroSD Card (16GB+ recommended)
- Power supply for Raspberry Pi
- (Optional) Case for mounting

## Installation

### 1. Hardware Setup

Connect GridEYE sensor to Raspberry Pi via I2C:

```
GridEYE    Raspberry Pi
VCC   -->  3.3V (Pin 1)
GND   -->  GND (Pin 6)
SDA   -->  GPIO 2 (Pin 3)
SCL   -->  GPIO 3 (Pin 5)
```

### 2. Software Installation

```bash
# Clone or download project
cd people-counter

# Make installation script executable
chmod +x install.sh

# Run installation (this will take 10-15 minutes)
./install.sh

# Reboot Raspberry Pi
sudo reboot
```

### 3. Verify Installation

```bash
# Check I2C device
sudo i2cdetect -y 1

# You should see device at address 0x69
```

## Configuration

Edit `config/config.yaml` to adjust parameters:

### Key Parameters

- **Sensor Frame Rate**: Default 10 Hz
- **Background Frames**: 250 frames for initialization
- **Temperature Threshold**: 0.25°C above background
- **Tracking Parameters**: Spatial, temporal, and temperature thresholds

### Mounting Recommendations

**Side Mounting (Recommended for narrow doors ~90cm):**
- Height: 120-140 cm from floor
- Distance: 60-120 cm from door frame
- Angle: Perpendicular to door (±20° tolerance)

**Top Mounting (Better for wide doors >180cm):**
- Above door frame
- Angled downward at ~30°
- Covers full doorway width

## Usage

### Basic Usage

```bash
# Navigate to project directory
cd people-counter

# Run the system
python3 src/main.py
```

### First Run - Background Initialization

On first run, the system will:
1. Collect 250 frames (~25 seconds at 10 Hz)
2. Calculate background temperature profile
3. Save background for future use

**Important**: Keep doorway clear during initialization!

### Keyboard Controls

- **q**: Quit application
- **r**: Reset entrance/exit counts
- **s**: Save current frame as image

### Command Line Options

```bash
# Use specific config file
python3 src/main.py --config path/to/config.yaml

# Force new background calculation
python3 src/main.py --no-saved-bg
```

## Understanding the System

### Processing Pipeline

1. **Sensor Reading**: GridEYE captures 8×8 thermal frames at 10 Hz
2. **Background Estimation**: Calculates baseline temperature profile
3. **Noise Filtering**: Multi-stage filter to detect human presence
   - Heat distribution analysis
   - Otsu's thresholding
   - Temperature filtering
4. **Body Extraction**: Identifies and separates individual bodies
5. **Tracking**: Tracks people across frames
6. **Direction Detection**: Determines entrance vs exit based on movement

### Accuracy Factors

**Positive Factors:**
- Proper mounting height (120-140 cm)
- Clear field of view
- Stable ambient temperature
- Single-file traffic

**Negative Factors:**
- Multiple people walking side-by-side (>2 people)
- Very fast movement (>3 m/s)
- Extreme temperature changes
- Distance from sensor (>180 cm)

## Visualization

The system displays two views:

**Left Panel**: Current thermal frame with:
- Green boxes around detected bodies
- Yellow dots at body centers
- Temperature readings
- Tracking information overlay

**Right Panel**: Difference from background
- Shows heat signatures
- Helps debug detection issues

**Info Overlay**:
- Total entrances
- Total exits
- Current occupancy
- Active tracks
- FPS counter

## Troubleshooting

### Sensor Not Detected

```bash
# Check I2C is enabled
sudo raspi-config
# Navigate to Interface Options -> I2C -> Enable

# Check device
sudo i2cdetect -y 1
```

### Low Accuracy

1. **Recalculate Background**:
   ```bash
   python3 src/main.py --no-saved-bg
   ```

2. **Adjust Mounting**:
   - Ensure sensor is 120-140 cm high
   - Check angle is perpendicular (±20°)
   - Verify clear field of view

3. **Tune Parameters**:
   - Adjust `temperature_threshold` in config
   - Modify `tracking.spatial_distance_threshold`

### False Detections

- Increase `temperature_threshold` (try 0.3-0.5°C)
- Increase `otsu_threshold` (try 1.0°C)
- Check for heat sources near doorway (heaters, sunlight)

### Missed Detections

- Decrease `temperature_threshold` (try 0.15-0.2°C)
- Verify background is recent and accurate
- Check sensor distance (<120 cm optimal)

## Performance Benchmarks

Based on paper results:

| Scenario | Accuracy |
|----------|----------|
| Narrow door (90cm) controlled | 96-100% |
| Wide door (180cm) controlled | 94-96% |
| Real-world (classroom) | 89-92% |
| Real-world (computer lab) | 90-92% |

## Data Logging

All events are logged to `data/logs/people_counter.log`:

```
2025-01-15 10:23:45 - Person 1 entered. Occupancy: 5
2025-01-15 10:24:12 - Person 2 exited. Occupancy: 4
```

## Advanced Features

### 1. Long-term Monitoring

```python
# Modify src/main.py to save periodic statistics
# Add to run() method:

if frame_count % 3600 == 0:  # Every hour at 10 FPS
    save_hourly_stats()
```

### 2. Remote Monitoring

```python
# Add MQTT or HTTP API to report occupancy
# Example: Send occupancy to home automation system
```

### 3. Multi-Sensor Setup

For large rooms, deploy multiple sensors:
- One sensor per doorway
- Aggregate counts from all sensors
- Central monitoring dashboard

## Project Structure

```
people-counter/
├── config/
│   └── config.yaml              # Configuration
├── src/
│   ├── sensor/
│   │   └── grideye_reader.py    # Sensor interface
│   ├── processing/
│   │   ├── background.py        # Background estimation
│   │   ├── noise_filter.py      # Noise filtering
│   │   ├── body_extractor.py    # Body detection
│   │   └── tracker.py           # People tracking
│   ├── utils/
│   │   └── visualization.py     # Visualization
│   └── main.py                  # Main application
├── data/
│   ├── background/              # Saved backgrounds
│   └── logs/                    # Log files
└── README.md
```

## Contributing

Improvements welcome! Focus areas:

- Multi-person detection accuracy
- Occlusion handling
- Integration with building management systems
- Mobile app for monitoring

## References

Based on research paper:
**"Measuring People-Flow Through Doorways using Easy-to-Install IR Array Sensors"**
by Mohammadmoradi et al., 2017

Key improvements over paper:
- Python 3 implementation
- Modular architecture
- Real-time visualization
- Configuration management
- Better error handling

## License

MIT License - Feel free to use and modify

## Support

For issues or questions:
1. Check troubleshooting section
2. Review logs in `data/logs/`
3. Verify hardware connections
4. Test with different mounting positions

## Performance Tips

1. **Raspberry Pi Optimization**:
   ```bash
   # Increase GPU memory
   sudo raspi-config
   # Advanced Options -> Memory Split -> 256
   ```

2. **Reduce Logging** (for better performance):
   - Set `log_level: WARNING` in config

3. **Disable Visualization** (headless operation):
   - Set `visualization.enable: false` in config

## Future Enhancements

- [ ] Machine learning for improved accuracy
- [ ] Web dashboard for remote monitoring
- [ ] Multi-sensor fusion
- [ ] Historical analytics
- [ ] Mobile alerts
- [ ] Integration with HVAC systems

---

**Happy Counting! 🚶‍♂️📊**    