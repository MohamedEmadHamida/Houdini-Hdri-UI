# HDRI Browser

A modern dark-themed interface for browsing EXR images, loading thumbnails in parallel, and applying them as environment lights in Houdini.

## Features

- Modern dark theme with custom styles
- Path bar for selecting folders
- Scrollable grid layout for thumbnails
- Parallel loading of thumbnails using QThreadPool
- Clickable thumbnails to set environment light in Houdini
- Hover zoom preview for thumbnails
- Time test decorator for performance measurement
- Config flags for enabling/disabling features
- Rotation and intensity sliders for HDRI adjustment in Houdini

## Project Structure

```
hdri_browser/
│
├── main.py                          # Entry point
├── config/
│   └── settings.py                  # Configuration flags
│
├── core/                            # Business logic
│   ├── hdri_manager.py              # HDRI operations in Houdini
│   ├── thumbnail_loader.py          # Parallel thumbnail loading
│   ├── cache_manager.py             # Thumbnail caching
│   └── file_manager.py              # File operations
│
├── ui/                              # User interface
│   ├── main_window.py               # Main EXRBrowser window
│   ├── components/
│   │   ├── card.py                  # AnimatedCard widget
│   │   ├── thumbnail.py             # ClickableLabel with hover zoom
│   │   ├── pulsing_label.py         # Loading animation label
│   │   └── context_label.py         # Context indicator label
│   │
│   └── styles/
│       └── colors.py                # Color definitions
│
├── services/                        # External integrations
│   └── houdini_api.py               # Houdini API utilities
│
├── utils/                           # Utilities
│   ├── decorators.py                # Time test decorator
│   ├── helpers.py                   # Helper functions
│   └── constants.py                 # Constants
│
└── assets/                          # Static assets
```

## Dependencies

- PySide6
- OpenImageIO
- Numpy
- Houdini (optional)

## Installation

1. Install required packages:
```bash
pip install PySide6 OpenImageIO numpy
```

2. Run the application:
```bash
python main.py
```

## Configuration

Edit `config/settings.py` to enable/disable features:

- `ENABLE_HOUDINI`: Enable Houdini integration
- `ENABLE_ENV_LIGHT_CLICK`: Enable clicking thumbnails to apply HDRI
- `ENABLE_TOOLTIPS`: Show tooltips
- `ENABLE_TIME_TEST`: Enable performance timing
- `ENABLE_MULTITHREADING`: Use parallel thumbnail loading

## Usage

1. Launch the application
2. Use the path bar to select a folder containing EXR files
3. Click on thumbnails to apply them as environment lights in Houdini
4. Use the sliders to adjust rotation, intensity, and exposure
5. Click the random button for random HDRI selection

## Authors

- MohamedEmadHamida
- Mohamed Qatary

## License

Built with passion for the Houdini community 🤍