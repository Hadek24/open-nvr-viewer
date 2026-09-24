# Open NVR Viewer

A lightweight Linux oriented GUI application in Python for viewing NVR camera streams using RTSP.

## What does it solve?

The project began as a personal laboratory initiative to replace a complex video surveillance client with a simpler application, focusing on the features actually needed for daily monitoring. Additionally, the original application lacked a version compatible with Linux.

## Features

Current version — v1.3.0

* PyQt6 graphical interface
* ffmpeg-based video playback
* RTSP streams from IP cameras / NVR systems
* Configurable number of camera channels
* 1x1, 2x2, 3x3 and 4x4 grid layouts
* Individual camera/channel selection
* Substream for multi-camera view
* Mainstream when maximizing a camera
* Persistent grid configuration using JSON
* Double-click to maximize/restore a camera
* The ability to reconnect to the cameras.
* Graphical improvement of the application.

### v1.3.0
* Graphical improvement of the application.

## Requirements

* Linux
* Python 3
* PyQt6
* ffmpeg installed and available in the PATH
* A compatible NVR/camera system providing RTSP streams

## Installation

Clone the repository:
```bash
git clone https://github.com/Hadek24/open-nvr-viewer.git
cd open-nvr-viewer
```

### Install the required system packages:

```bash
sudo apt update
sudo apt install ffmpeg python3-pyqt6
```

## How to use it?

1. Ensure configuration parameters are set in `config.json` (NVR IP address, credentials, ports, and total channels).
2. Launch the application:

```bash
python3 main.py
```

**Usage & Features:**

* Configurable Grid Layouts: Choose between 1x1, 2x2, 3x3, and 4x4 viewing grids from the top bar.
* Dynamic Camera Assignment: Assign any available camera (supports up to 16 channels) or leave slots empty using individual dropdown selectors.
* Optimized Bandwidth (Sub-stream): By default, grid slots load the low-resolution sub-stream to minimize CPU and network overhead.
* Full-Screen Focus (Main-stream): Double-clicking any camera widget isolates that feed and automatically elevates it to the high-resolution main-stream. Double-click again to return to the grid.
* Manual Reconnection: If a stream disconnects or fails, use the selector or action buttons; connection retries require user initiation by design.

## Configuration

The application uses a local `config.json` file for the NVR connection and application settings.

Create it from the example configuration:
```bash
cp config.example.json config.json
```

Example (`config.json`):
```json
{
    "NVR_USER": "your_user",
    "NVR_PASS": "your_password",
    "NVR_IP": "192.168.1.100",
    "NVR_PORT": "554",
    "TOTAL_CHANNELS": 16,
    "LAST_GRID_SIZE": 2,
    "GRID_MAPPINGS": {
        "1": ["1"],
        "2": ["1", "2", "3", "4"],
        "3": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
        "4": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16"]
    }
}

```

> ⚠️ **Important:** `config.json` contains credentials and is intentionally excluded from the Git repository. Do not commit real passwords or other sensitive information.

## RTSP

The application uses RTSP channel URLs following the standard channel/stream structure:
```text
rtsp://USER:PASSWORD@NVR_IP:PORT/Streaming/Channels/CHANNEL0STREAM
```

For example:
* **Channel 1 + substream:** `.../Streaming/Channels/102`
* **Channel 1 + mainstream:** `.../Streaming/Channels/101`

The multi-camera grid uses the substream to reduce resource usage, while the maximized camera uses the mainstream.

**Note:** Currently, it only supports this type of format; other formats will be added later in the project.

## Project Structure

```text
open-nvr-viewer/
├── main.py
├── config.example.json
├── config.json          # Local only - not tracked by Git
├── LICENSE 
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── camera_widget.py
│   ├── main_window.py
│   ├── styles.py
│   ├── title_bar.py
│   ├── video_frame.py
│   └── video_thread.py
├── .gitignore
└── README.md
```

## Project Status

This is an actively developed personal project.
The current priority is stability and reliability before adding additional features.

## Known limitations

* Currently supports only the /Streaming/Channels/ RTSP URL structure; other NVR URL schemes are not yet implemented.

## License

Distributed under the MIT license.

Note: The use of the software is the operator's responsibility. The author assumes no liability for misuse or failures in production environments.
