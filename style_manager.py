from qgis.PyQt.QtWidgets import (QAction, QFileDialog, QDialog, QFormLayout, QVBoxLayout,
                                  QHBoxLayout, QDialogButtonBox, QLabel, QPushButton,
                                  QLineEdit, QGroupBox, QMessageBox)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProject, QgsSettings, Qgis
import os

DEFAULT_SHORTCUT_EXPORT = 'Ctrl+Shift+X'
DEFAULT_SHORTCUT_IMPORT = 'Ctrl+Shift+I'


def tr(message):
    return QCoreApplication.translate('StyleExporterImporterPlugin', message)


class SettingsDialog(QDialog):
    def __init__(self, parent, styles_dir):
        super().__init__(parent)
        self.setWindowTitle(tr('Style Manager — Settings'))
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        # ── Styles directory ──────────────────────────────────────────────────
        dir_group = QGroupBox(tr('Default styles directory'))
        dir_layout = QHBoxLayout(dir_group)

        self.dir_edit = QLineEdit(styles_dir, self)
        self.dir_edit.setPlaceholderText(tr('Leave empty to always ask'))

        browse_btn = QPushButton('…')
        browse_btn.setFixedWidth(32)
        browse_btn.clicked.connect(self.browse_dir)

        clear_btn = QPushButton(tr('Clear'))
        clear_btn.clicked.connect(lambda: self.dir_edit.clear())

        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(browse_btn)
        dir_layout.addWidget(clear_btn)

        layout.addWidget(dir_group)

        # ── Note about shortcuts ──────────────────────────────────────────────
        note = QLabel(tr('Keyboard shortcuts can be configured in\n'
                         'Settings → Keyboard Shortcuts → Style Manager'))
        note.setWordWrap(True)
        layout.addWidget(note)

        # ── OK / Cancel ───────────────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse_dir(self):
        current = self.dir_edit.text()
        path = QFileDialog.getExistingDirectory(self, tr('Select styles directory'), current)
        if path:
            self.dir_edit.setText(path)

    def get_values(self):
        return self.dir_edit.text().strip()


class StyleExporterImporterPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.actions = []
        self.menu = self.tr('&Style Manager')
        self.settings = QgsSettings()          # #1: QgsSettings instead of QSettings
        self.action_export = None
        self.action_import = None

    def tr(self, message):
        return QCoreApplication.translate('StyleExporterImporterPlugin', message)

    # ── Settings helpers ──────────────────────────────────────────────────────

    def _load_settings(self):
        styles_dir = self.settings.value('StyleManager/styles_dir', '', type=str)  # #1: explicit type=str
        return styles_dir

    # ── Plugin lifecycle ──────────────────────────────────────────────────────

    def add_action(self, icon_path, text, callback, add_to_menu=True, add_to_toolbar=True):
        icon = QIcon(icon_path)
        action = QAction(icon, text, self.iface.mainWindow())
        action.triggered.connect(callback)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        plugin_dir = os.path.dirname(__file__)

        self.action_export = self.add_action(
            os.path.join(plugin_dir, 'icons', 'icon_export.svg'),
            text=self.tr('Export Styles'),
            callback=self.run_export)
        self.iface.registerMainWindowAction(self.action_export, DEFAULT_SHORTCUT_EXPORT)

        self.action_import = self.add_action(
            os.path.join(plugin_dir, 'icons', 'icon_import.svg'),
            text=self.tr('Import Style'),
            callback=self.run_import)
        self.iface.registerMainWindowAction(self.action_import, DEFAULT_SHORTCUT_IMPORT)

        self.add_action(
            os.path.join(plugin_dir, 'icons', 'icon_settings.svg'),
            text=self.tr('Settings…'),
            callback=self.open_settings,
            add_to_toolbar=False)

    def unload(self):
        self.iface.unregisterMainWindowAction(self.action_export)
        self.iface.unregisterMainWindowAction(self.action_import)
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    # ── Settings dialog ───────────────────────────────────────────────────────

    def open_settings(self):
        styles_dir = self._load_settings()
        dlg = SettingsDialog(self.iface.mainWindow(), styles_dir)

        if dlg.exec():
            new_dir = dlg.get_values()
            self.settings.setValue('StyleManager/styles_dir', new_dir)
            self.iface.messageBar().pushMessage(
                'Style Manager', self.tr('Settings saved.'),
                level=Qgis.Success, duration=3)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _sanitize_filename(self, name):
        """#3: Remove characters invalid in filenames across platforms."""
        sanitized = ''.join(c for c in name if c.isalnum() or c in ' _-').strip()
        return sanitized or 'unnamed'

    def _get_project_name(self):
        name = QgsProject.instance().baseName()
        return self._sanitize_filename(name)

    def _get_output_dir(self, styles_dir):
        if styles_dir:
            raw_name = QgsProject.instance().baseName()
            if not raw_name:  # check raw name before sanitization — empty means unsaved
                self.iface.messageBar().pushMessage(
                    self.tr('Warning'),
                    self.tr('Project is not saved. Please save the project first.'),
                    level=Qgis.Warning, duration=5)
                return None
            project_name = self._sanitize_filename(raw_name)
            output_dir = os.path.join(styles_dir, project_name)
            os.makedirs(output_dir, exist_ok=True)  # guarded by try/except in run_export
            return output_dir
        else:
            return QFileDialog.getExistingDirectory(
                self.iface.mainWindow(), self.tr('Select output directory')) or None

    def get_vector_layer_type(self, layer):
        geometry_type = layer.geometryType()
        if geometry_type == Qgis.GeometryType.Point:
            return 'point'
        elif geometry_type == Qgis.GeometryType.Line:
            return 'line'
        elif geometry_type == Qgis.GeometryType.Polygon:
            return 'polygon'
        else:
            return 'unknown'

    def _get_layer_geometry_label(self, layer):
        """#5: Return geometry label for mismatch check."""
        if isinstance(layer, QgsRasterLayer):
            return 'raster'
        if isinstance(layer, QgsVectorLayer):
            return self.get_vector_layer_type(layer)
        return 'unknown'

    def _extract_geometry_type_from_filename(self, file_path):
        """#5: Parse geometry type from plugin naming convention."""
        base = os.path.basename(file_path).lower()
        for geom_type in ('point', 'line', 'polygon', 'raster'):
            if f'_{geom_type}_style.qml' in base:
                return geom_type
        return None

    # ── Export ────────────────────────────────────────────────────────────────

    def run_export(self):
        selected_layers = self.iface.layerTreeView().selectedLayers()

        if not selected_layers:
            self.iface.messageBar().pushMessage(
                self.tr('Error'), self.tr('No layers selected'), level=Qgis.Warning)
            return

        styles_dir = self._load_settings()

        # #2: wrap all I/O in try/except
        try:
            output_dir = self._get_output_dir(styles_dir)
            if not output_dir:
                return

            exported_count = 0
            for layer in selected_layers:
                if isinstance(layer, QgsVectorLayer):
                    # #3: sanitize layer name
                    safe_name = self._sanitize_filename(layer.name())
                    file_name = f'{safe_name}_{self.get_vector_layer_type(layer)}_style.qml'
                elif isinstance(layer, QgsRasterLayer):
                    safe_name = self._sanitize_filename(layer.name())
                    file_name = f'{safe_name}_raster_style.qml'
                else:
                    continue

                output_path = os.path.join(output_dir, file_name)
                error_msg, success = layer.saveNamedStyle(output_path)

                if success:
                    exported_count += 1
                    self.iface.messageBar().pushMessage(
                        self.tr('Success'), self.tr('Style saved: %s') % file_name,
                        level=Qgis.Success, duration=3)
                else:
                    self.iface.messageBar().pushMessage(
                        self.tr('Error'), self.tr('Failed to save style: %s — %s') % (file_name, error_msg),
                        level=Qgis.Warning, duration=3)

            self.iface.messageBar().pushMessage(
                self.tr('Export complete'),
                self.tr('Exported %d style(s) to: %s') % (exported_count, output_dir),
                level=Qgis.Info, duration=5)

        except PermissionError:
            self.iface.messageBar().pushMessage(
                self.tr('Error'),
                self.tr('Permission denied for the selected directory.'),
                level=Qgis.Critical, duration=5)
        except OSError as e:
            self.iface.messageBar().pushMessage(
                self.tr('Error'),
                self.tr('File system error: %s') % str(e),
                level=Qgis.Critical, duration=5)

    # ── Import ────────────────────────────────────────────────────────────────

    def run_import(self):
        active_layer = self.iface.activeLayer()
        if not active_layer:
            self.iface.messageBar().pushMessage(
                self.tr('Error'), self.tr('No active layer selected'), level=Qgis.Warning)
            return

        styles_dir = self._load_settings()
        file_path, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(), self.tr('Select style file'),
            styles_dir, self.tr('QGIS Layer Style File (*.qml)'))
        if not file_path:
            return

        # #5: geometry type mismatch warning
        style_type = self._extract_geometry_type_from_filename(file_path)
        layer_type = self._get_layer_geometry_label(active_layer)

        if style_type and layer_type != style_type:
            reply = QMessageBox.warning(
                self.iface.mainWindow(),
                self.tr('Geometry type mismatch'),
                self.tr('The style "%s" was exported for %s layers,\n'
                        'but the active layer "%s" is %s.\n\n'
                        'Apply anyway?') % (
                    os.path.basename(file_path), style_type,
                    active_layer.name(), layer_type),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return

        # #2: wrap I/O in try/except
        try:
            error_msg, success = active_layer.loadNamedStyle(file_path)

            if success:
                self.iface.messageBar().pushMessage(
                    self.tr('Success'),
                    self.tr('Style imported for layer: %s') % active_layer.name(),
                    level=Qgis.Success, duration=5)
                active_layer.triggerRepaint()
            else:
                self.iface.messageBar().pushMessage(
                    self.tr('Error'),
                    self.tr('Failed to import style for layer: %s — %s') % (active_layer.name(), error_msg),
                    level=Qgis.Warning, duration=5)

        except OSError as e:
            self.iface.messageBar().pushMessage(
                self.tr('Error'),
                self.tr('File system error: %s') % str(e),
                level=Qgis.Critical, duration=5)
