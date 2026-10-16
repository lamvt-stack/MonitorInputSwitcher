# Artifact Inventory

This file lists what should be checked into GitHub and what is generated locally at build or runtime.

## Check Into GitHub

These files are required for a clean checkout of the project:

- `MonitorInputSwitcher.cpp`: main application source
- `mis_monitor.h`: monitor enumeration and DDC/CI helpers
- `mis_config.h`: configuration persistence and autostart helpers
- `mis_cli.h`: command-line parsing and console output helpers
- `mis_icons.h`: embedded built-in icon set used by the app
- `build.bat`: builds both executables
- `app.rc`: embeds the application and tray icons
- `app.ico`: main application icon
- `tray-light.ico`: tray icon variant for dark taskbars
- `tray-dark.ico`: tray icon variant for light taskbars
- `make_icons.py`: regenerates the built-in icon set
- `make_app_icons.py`: regenerates the app/tray icon assets
- `README.md`: project overview and quick start
- `BUILDING.md`: build instructions
- `ARTIFACTS.md`: this inventory
- `LICENSE`: MIT license text
- `.gitignore`, `.gitattributes`, `.editorconfig`: repository hygiene and text handling

## Optional But Useful

These files are useful reference assets, but not required for a successful build:

- `preview.png`
- `app-icons-preview.png`
- `app-256.png`
- `business-256.png`
- `cloud-256.png`
- `creative-256.png`
- `desktop-256.png`
- `developer-256.png`
- `documents-256.png`
- `education-256.png`
- `finance-256.png`
- `gaming-256.png`
- `home-256.png`
- `internet-256.png`
- `laptop-256.png`
- `media-256.png`
- `music-256.png`
- `network-256.png`
- `photo-256.png`
- `reading-256.png`
- `security-256.png`
- `server-256.png`
- `streaming-256.png`
- `tray-dark-256.png`
- `tray-light-256.png`
- `video-call-256.png`
- `work-256.png`

## Generated Locally

These files are created on your machine and should not be committed:

- `MonitorInputSwitcher.exe`: GUI build
- `mis-cli.exe`: console build
- `MonitorInputSwitcher.ini`: per-user settings file created at runtime
- `*.obj`, `*.o`, `*.res`, `*.exe`, `*.pdb`, `*.ilk`, `*.exp`, `*.lib`, `*.manifest`: build products

## External Dependencies

The application links only against standard Windows libraries:

- `user32`
- `gdi32`
- `shell32`
- `advapi32`
- `comdlg32`
- `comctl32`
- `msimg32`
- `dxva2`

The build toolchain must provide either:

- MSVC plus the Windows SDK, or
- MinGW-w64 with `g++` and `windres`

## Optional Python Dependencies

Only the icon-generation scripts need Python packages:

- `numpy`
- `Pillow`
