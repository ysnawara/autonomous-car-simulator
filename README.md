# Autonomous Car Simulator

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green.svg)](https://opencv.org)
[![Pygame](https://img.shields.io/badge/Pygame-2.5+-red.svg)](https://pygame.org)

A 2D top-down autonomous car simulation demonstrating vision-based lane following using the **Pure Pursuit** controller.

![Simulation Demo](assets/AutoCarGif.gif)


## Features

- **2D Race Track** with black road and green boundary lines
- **Bicycle Model** car physics for realistic steering
- **Vision-Based Pure Pursuit** controller for lane following
- **Real-time Visualization** of controller behavior
- **OpenCV Vision System** for lane detection from camera POV
- **Speed Controller** that slows for curves
- **Lap Counter** with trail visualization

## How It Works

### Vision-Based Pure Pursuit
The car navigates using only what it "sees" through a virtual camera:

1. **Camera POV** - Extracts a first-person perspective view from the car's position
2. **Lane Detection** - Uses OpenCV to detect green boundary lines in HSV color space
3. **Lane Center** - Calculates the center of the lane from detected boundaries
4. **Pure Pursuit Steering** - Adjusts steering based on lane center deviation and look-ahead distance

The controller operates without pre-programmed waypoints—it reacts purely to visual input, similar to how a human driver would navigate.

## Installation

```bash
cd autonomous-car-simulator
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

### Controls

| Key | Action |
|-----|--------|
| `R` | Reset simulation |
| `SPACE` | Pause/Resume |
| `ESC` | Quit |

**Interactive Sliders:**
- **Speed** - Adjust car velocity in real-time
- **Look-Ahead** - Tune the controller's look-ahead distance

## Project Structure

```
autonomous-car-simulator/
├── main.py          # Main simulation loop
├── config.py        # Configuration settings
├── track.py         # Track generation and rendering
├── car.py           # Bicycle model car physics
├── controllers.py   # Vision-based Pure Pursuit implementation
├── vision.py        # OpenCV lane detection
├── requirements.txt
└── README.md
```


## Tuning Parameters

In `config.py`:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `LOOK_AHEAD_DISTANCE` | Pure Pursuit look-ahead | 70 px |
| `MAX_SPEED` | Maximum car speed | 50.0 |
| `MAX_STEERING_ANGLE` | Maximum steering | 45° |
| `VISION_RANGE` | Camera view distance | 150 px |


## License

MIT License - see [LICENSE](LICENSE)


