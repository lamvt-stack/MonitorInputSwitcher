# Monitor Input Switcher

Monitor Input Switcher is a small Windows utility that switches monitor inputs through DDC/CI and exposes each monitor as a floating desktop button. The same code base builds into a GUI app and a console twin for scripting.

## Features

- Switch one or more monitors to a chosen input source
- Show a lightweight floating button per saved monitor/input pair
- Support drag-to-move, per-button labels, icons, colors, and opacity
- Provide a console twin for batch files, shortcuts, and automation
- Store settings in a UTF-16 `.ini` file next to the executable

## Getting Started

This repository is ready for a normal GitHub upload. The files that should be committed are listed in [ARTIFACTS.md](ARTIFACTS.md), and the build steps are documented in [BUILDING.md](BUILDING.md).

## Build

Run [build.bat](build.bat) from a Windows command prompt in the repository root. The script auto-detects MSVC or MinGW-w64 and produces both `MonitorInputSwitcher.exe` and `mis-cli.exe`.

## Runtime Files

- `MonitorInputSwitcher.exe`: GUI application
- `mis-cli.exe`: console twin for command-line use
- `MonitorInputSwitcher.ini`: per-user settings file created next to the executable

## Repository Layout

- `MonitorInputSwitcher.cpp`: main application source
- `mis_monitor.h`, `mis_config.h`, `mis_cli.h`: refactored support headers
- `mis_icons.h`: built-in icon set used by the app
- `app.rc`, `app.ico`, `tray-light.ico`, `tray-dark.ico`: embedded resources
- `make_icons.py`, `make_app_icons.py`: optional asset regeneration scripts
- `README.md`, `BUILDING.md`, `ARTIFACTS.md`, `LICENSE`: project documentation

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
