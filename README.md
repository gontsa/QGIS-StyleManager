# QGIS Style Manager

A QGIS 4.0+ plugin for exporting and importing layer styles (QML files) with project-based organization.

## Features

- **Export styles** for multiple selected layers at once
- **Import style** for the active layer
- **Project-based storage** — styles are automatically saved to `styles_dir/ProjectName/`
- **Configurable keyboard shortcuts** via Settings dialog (persisted between sessions)
- **Default styles directory** — set once, no more folder dialogs
- **i18n support** — English by default, Ukrainian translation included

## Requirements

- QGIS 4.0.0 or later
- Python 3.x

## Installation

### From ZIP

1. Download the latest release ZIP from [Releases](https://github.com/gontsa/QGIS-StyleManager/releases)
2. In QGIS: **Plugins → Manage and Install Plugins → Install from ZIP**
3. Select the downloaded ZIP and click **Install Plugin**

### Manual

```bash
# Linux / macOS
cp -r StyleManager ~/.local/share/QGIS/QGIS4/profiles/default/python/plugins/

# Windows
xcopy StyleManager %APPDATA%\QGIS\QGIS4\profiles\default\python\plugins\StyleManager\
```

Then enable the plugin in **Plugins → Manage and Install Plugins**.

## Usage

### Export styles

1. Select one or more layers in the Layers panel
2. Click **Style Manager → Export Styles** or use the shortcut (`Ctrl+Shift+E` by default)
3. If a default styles directory is set — styles are saved automatically to `styles_dir/ProjectName/`
4. Otherwise a folder selection dialog appears

### Import style

1. Make the target layer active
2. Click **Style Manager → Import Style** or use the shortcut (`Ctrl+Shift+I` by default)
3. Select a `.qml` file — the style is applied immediately

### Settings

**Style Manager → Settings…** lets you configure:

| Setting | Description |
|---|---|
| Export shortcut | Keyboard shortcut for export (default `Ctrl+Shift+E`) |
| Import shortcut | Keyboard shortcut for import (default `Ctrl+Shift+I`) |
| Default styles directory | Root folder for project-based style storage |

### Project-based directory structure

When a default styles directory is set, the plugin organises files automatically:

```
styles_dir/
├── ProjectA/
│   ├── rivers_line_style.qml
│   └── lakes_polygon_style.qml
└── ProjectB/
    └── roads_line_style.qml
```

> **Note:** the project must be saved before exporting, as the project name is used for the subfolder.

## Translations

Translation files are located in `i18n/`. To add a new language:

1. Copy `i18n/i18n_uk.ts` to `i18n/i18n_XX.ts` (where `XX` is the language code)
2. Translate the strings using Qt Linguist or a text editor
3. Compile:
   ```bash
   /usr/lib/qt6/bin/lrelease i18n/i18n_XX.ts -qm i18n/i18n_XX.qm
   ```

The plugin auto-detects the system locale and loads the matching `.qm` file.

## Development

```bash
git clone https://github.com/gontsa/QGIS-Style-Manager.git
cd QGIS-Style-Manager

# Symlink into QGIS plugins folder for live development
ln -s $(pwd)/StyleManager ~/.local/share/QGIS/QGIS4/profiles/default/python/plugins/StyleManager
```

To update translation sources after editing strings in the code:

```bash
pylupdate6 style_manager.py -ts i18n/i18n_uk.ts
/usr/lib/qt6/bin/lrelease i18n/i18n_uk.ts -qm i18n/i18n_uk.qm
```

## License

This plugin is free software; you can redistribute it and/or modify it under the terms of the [GNU General Public License v2](LICENSE).
