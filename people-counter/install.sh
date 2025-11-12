#!/bin/bash

echo "Installing People Counter System..."

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y libatlas-base-dev libjasper-dev libqtgui4 libqt4-test
sudo apt-get install -y i2c-tools

# Enable I2C
sudo raspi-config nonint do_i2c 0

# Install Python dependencies
pip3 install -r requirements.txt

# Create necessary directories
mkdir -p data/background
mkdir -p data/logs

echo "Installation complete!"
echo "Please reboot your Raspberry Pi: sudo reboot"
```

## Requirements File

Create `requirements.txt`:
```
numpy==1.21.0
opencv-python==4.5.3.56
adafruit-circuitpython-amg88xx==1.2.8
adafruit-blinka==8.0.0
PyYAML==6.0
scipy==1.7.0
matplotlib==3.4.2