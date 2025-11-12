# Quick Start Guide

## Hardware Connection
1. Connect GridEYE to Raspberry Pi I2C pins
2. Power on Raspberry Pi

## Installation
```bash
cd people-counter
chmod +x install.sh
./install.sh
sudo reboot
```

## First Run
```bash
cd people-counter
python3 src/main.py
```

## That's it!
- Keep doorway clear for first 25 seconds (background calculation)
- Watch the visualization window
- Press 'q' to quit

## Tips
- Mount sensor 120-140cm from floor
- Point perpendicular to doorway
- Works best with narrow doors (90cm)