# Open NVR Viewer

Open NVR Viewer is a lightweight desktop application for viewing RTSP camera streams from Network Video Recorders (NVRs). It provides a graphical interface for managing NVR profiles, selecting camera channels, and displaying multiple streams in a configurable grid.

## What does it solve?

The project began as a personal laboratory initiative to replace a complex video surveillance client with a simpler application, focusing on the features actually needed for daily monitoring. Additionally, the original application lacked a version compatible with Linux.

## Features

Current version — v2.2.0

Version 2.2.0 extends the configuration workflow introduced in version 2.0.0 with encrypted configuration backups, backup verification, and configuration restoration.

### Camera monitoring

* Display RTSP camera streams in a configurable grid.
* Support for grid layouts from 1×1 to 4×4.
* Select and assign camera channels to individual grid positions.
* Double-click a camera to maximize or restore its view.
* Use substreams for grid viewing and mainstreams when maximizing a camera, where supported by the configured NVR.
* Automatically reconnect to camera streams when a connection is interrupted.
* Preserve the selected grid layout and camera assignments between sessions.
* Monitor application resource usage through the status bar.

### NVR configuration and profiles

The configuration workflow is managed through the graphical interface.

* Create, edit, activate, and delete NVR profiles.
* Configure the NVR address, port, username, password, and channel count.
* Select between multiple saved NVR profiles.
* Assign an RTSP URL template to each NVR profile.
* Manage custom RTSP templates from Configuration > RTSP; built-in generic examples are read-only in the GUI and are not guaranteed to work with every NVR.
* Keep profiles and RTSP templates together in config.json so encrypted backups include both. 
* Confirm passwords when creating or changing profile credentials.
* Create and delete the configuration file from the application.
* Check whether a configuration file exists and open its containing directory.
* Start the application without an existing configuration file.

### Configuration backup and restoration

* Export the configuration and saved profile credentials to an encrypted backup file.
* Protect backups with a user-defined master password.
* Verify backup integrity and validate its contents before restoration.
* Restore saved profiles and credentials from a valid backup.
* Automatically restart the application after a successful restoration so the restored configuration is loaded.

### Connectivity tests

The profile test currently checks:

* Ping: basic host reachability.
* TCP port: whether a TCP connection can be established to the configured address and port.

## Requirements

* Linux
* Python 3.10 or later.
* PyQt6
* Psutil.
* Cryptography for encrypted backups.
* Keyring support for secure credential storage
* FFmpeg libraries.
* A compatible NVR/camera system providing RTSP streams

## Installation

### Option 1: Download a release

Download the Linux release package from the GitHub Releases page.

Extract the ZIP archive and launch the packaged application using the instructions provided with the release.

The published Linux package is built with PyInstaller. Package behavior should be verified against the specific release before use.

### Option 2: Run from source

Clone the repository:
```bash
git clone https://github.com/Hadek24/open-nvr-viewer.git
cd open-nvr-viewer
```

Install the required system packages:
```bash
sudo apt update
sudo apt install ffmpeg libxcb-cursor0 python3-pyqt6 python3-psutil python3-keyring python3-cryptography
```

Alternatively, install the Python dependencies using pip:
```bash
pip install -r requirements.txt
```

Launch the application:
```bash
python3 main.py
```
Depending on your Linux distribution, you may need to install additional system libraries required by PyQt6.

## First-time setup

1. Launch Open NVR Viewer.
2. Open the Configuration tab.
3. If no configuration file exists, use the configuration controls to create one.
4. Open Configuration > RTSP and review the available URL templates, creating a custom template if needed.
5. Create an NVR profile, enter its connection details, and select an RTSP template.
6. Confirm the password and save the profile.
7. Activate the profile you want to use.
8. Run the available connectivity tests.
9. Return to the main view and select a grid layout.

The application can start without an existing configuration file. However, an NVR profile must be configured before the application can connect to an NVR.

## Configuration and credential storage
The main configuration file is named config.json. It contains separate top-level sections for NVR profiles and RTSP templates. Profiles store a template ID, while the template catalog stores each URL format.

RTSP URL templates can use these variables: `{username}`, `{password}`, `{ip}`, `{port}`, `{channel}`, `{stream}`, `{stream_index}`, `{stream_padded}`, and `{channel_code}`. The application substitutes these values when opening each camera stream.

* `{username}`, `{password}`, `{ip}`, and `{port}`: values from the selected NVR profile.
* `{channel}`: the selected channel number.
* `{stream}`: `1` for the main stream and `2` for the substream.
* `{stream_index}`: `0` for the main stream and `1` for the substream, for formats that use zero-based stream indexes.
* `{stream_padded}`: `01` for the main stream and `02` for the substream.
* `{channel_code}`: the channel number followed by `0` and the stream number, matching the URL format currently used by ONV.

User-defined templates are included in encrypted configuration backups. 

NVR passwords are stored using the operating system's credential storage through Python's keyring library rather than being saved as plaintext passwords in the JSON configuration file.

The application provides controls for creating, opening, and deleting its configuration file. Users do not need to create or edit the JSON file manually during normal operation.

Security note: protect access to your operating system account and credential store. Do not commit local configuration files or credentials to a public repository.

## Encrypted configuration backups

Open NVR Viewer supports exporting, verifying, and restoring encrypted configuration backups.

* Export: Save the configuration and associated profile credentials to an encrypted .nvrbackup file.
* Verify: Check the backup's integrity and validate its contents without changing the current configuration.
* Import: Restore the configuration and profile credentials from a valid backup.

Backups are protected with a user-defined master password. The application uses Scrypt for password-based key derivation and AES-256-GCM for authenticated encryption.

Restoring a backup replaces the current configuration and updates the saved profile credentials. After a successful restoration, the application restarts to load the restored configuration.

Keep the backup file and its master password secure. A backup cannot be restored without the correct master password.

## RTSP

The application is designed for NVRs that expose streams through the /Streaming/Channels/ RTSP path convention.

```text
rtsp://<username>:<password>@<nvr-address>:<port>/Streaming/Channels/<channel><stream>
```

For example, on devices using this convention:

* Channel 1, substream: /Streaming/Channels/102
* Channel 1, mainstream: /Streaming/Channels/101

The exact stream mapping depends on the NVR manufacturer and configuration.

Make sure RTSP access is enabled on the NVR and that the configured account has permission to view the required channels.

## Project Structure

```text
open-nvr-viewer/
├── CODE_OF_CONDUCT.md
├── LICENSE
├── main.py
├── README.md
├── requirements.txt
├── resources
│   └── app_icon.png
└── src
    ├── __init__.py
    ├── camera_widget.py
    ├── config.py
    ├── configuration_tab.py
    ├── configuration_tab_section
    │   ├── __init__.py
    │   ├── config_file.py
    │   ├── connection_test.py
    │   └── profiles.py
    ├── main_window.py
    ├── resource_utils.py
    ├── status_bar.py
    ├── styles.py
    ├── title_bar.py
    ├── video_frame.py
    └── video_thread.py
```

## Project Status

Open NVR Viewer is an actively developed personal project. The application is intended to provide a straightforward way to monitor NVR camera streams and manage connection profiles through a desktop interface.

## Known limitations

* The current implementation is designed around the /Streaming/Channels/ RTSP path convention.
* Compatibility with direct IP cameras that do not use this path has not been fully tested.
* Connectivity tests currently cover ping and TCP port reachability only.
* Successful ping or TCP connectivity does not guarantee that RTSP authentication or video playback will work.
* The application has primarily been developed for Linux. Other platforms may require additional testing.
* The Playback tab is present but not implemented yet.

## License

Distributed under the MIT license.

Note: The use of the software is the operator's responsibility. The author assumes no liability for misuse or failures in production environments.
