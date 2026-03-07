from qgis.PyQt.QtWidgets import (QAction, QFileDialog, QDialog, QFormLayout, QVBoxLayout,
                                  QHBoxLayout, QKeySequenceEdit, QDialogButtonBox, QLabel,
                                  QPushButton, QLineEdit, QGroupBox)
from qgis.PyQt.QtGui import QIcon, QKeySequence
from qgis.PyQt.QtCore import QCoreApplication, QSettings, Qt
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProject, Qgis
import os

DEFAULT_SHORTCUT_EXPORT = 'Ctrl+Shift+X'
DEFAULT_SHORTCUT_IMPORT = 'Ctrl+Shift+I'


def tr(message):
    """Standalone tr() for use inside ShortcutsDialog (no iface access)."""
    return QCoreApplication.translate('StyleExporterImporterPlugin', message)


class SettingsDialog(QDialog):
    def __init__(self, parent, export_shortcut, import_shortcut, styles_dir):
        super().__init__(parent)
        self.setWindowTitle(tr('Style Manager — Settings'))
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        # ── Shortcuts ────────────────────────────────────────────────────────
        sc_group = QGroupBox(tr('Keyboard shortcuts'))
        sc_layout = QFormLayout(sc_group)

        self.export_edit = QKeySequenceEdit(QKeySequence(export_shortcut), self)
        self.import_edit = QKeySequenceEdit(QKeySequence(import_shortcut), self)

        sc_layout.addRow(tr('Export styles:'), self.export_edit)
        sc_layout.addRow(tr('Import style:'), self.import_edit)

        reset_btn = QPushButton(tr('Reset to defaults'))
        reset_btn.clicked.connect(self.reset_defaults)
        sc_layout.addRow(reset_btn)

        layout.addWidget(sc_group)

        # ── Styles directory ─────────────────────────────────────────────────
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

    def reset_defaults(self):
        self.export_edit.setKeySequence(QKeySequence(DEFAULT_SHORTCUT_EXPORT))
        self.import_edit.setKeySequence(QKeySequence(DEFAULT_SHORTCUT_IMPORT))

    def get_values(self):
        return (
            self.export_edit.keySequence().toString(),
            self.import_edit.keySequence().toString(),
            self.dir_edit.text().strip(),
        )


class StyleExporterImporterPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.actions = []
        self.menu = self.tr('&Style Manager')
        self.settings = QSettings()
        self.action_export = None
        self.action_import = None

    def tr(self, message):
        return QCoreApplication.translate('StyleExporterImporterPlugin', message)

    # ── Settings helpers ──────────────────────────────────────────────────────

    def _load_settings(self):
        export_sc  = self.settings.value('StyleManager/shortcut_export', DEFAULT_SHORTCUT_EXPORT)
        import_sc  = self.settings.value('StyleManager/shortcut_import', DEFAULT_SHORTCUT_IMPORT)
        styles_dir = self.settings.value('StyleManager/styles_dir', '')
        return export_sc, import_sc, styles_dir

    def _apply_shortcut(self, action, shortcut_str):
        action.setShortcut(QKeySequence(shortcut_str))
        action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)

    def _menu_text(self, label, shortcut_str):
        return f'{label}  [{shortcut_str}]'

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
        export_sc, import_sc, _ = self._load_settings()

        self.action_export = self.add_action(
            os.path.join(plugin_dir, 'icons', 'icon_export.svg'),
            text=self._menu_text(self.tr('Export Styles'), export_sc),
            callback=self.run_export)
        self._apply_shortcut(self.action_export, export_sc)

        self.action_import = self.add_action(
            os.path.join(plugin_dir, 'icons', 'icon_import.svg'),
            text=self._menu_text(self.tr('Import Style'), import_sc),
            callback=self.run_import)
        self._apply_shortcut(self.action_import, import_sc)

        self.add_action(
            os.path.join(plugin_dir, 'icons', 'icon_settings.svg'),
            text=self.tr('Settings…'),
            callback=self.open_settings,
            add_to_toolbar=False)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    # ── Settings dialog ───────────────────────────────────────────────────────

    def open_settings(self):
        export_sc, import_sc, styles_dir = self._load_settings()
        dlg = SettingsDialog(self.iface.mainWindow(), export_sc, import_sc, styles_dir)

        if dlg.exec():
            new_export, new_import, new_dir = dlg.get_values()
            self.settings.setValue('StyleManager/shortcut_export', new_export)
            self.settings.setValue('StyleManager/shortcut_import', new_import)
            self.settings.setValue('StyleManager/styles_dir', new_dir)

            self._apply_shortcut(self.action_export, new_export)
            self.action_export.setText(self._menu_text(self.tr('Export Styles'), new_export))

            self._apply_shortcut(self.action_import, new_import)
            self.action_import.setText(self._menu_text(self.tr('Import Style'), new_import))

            self.iface.messageBar().pushMessage(
                'Style Manager', self.tr('Settings saved.'),
                level=Qgis.Success, duration=3)

    # ── Export / Import ───────────────────────────────────────────────────────

    def _get_project_name(self):
        name = QgsProject.instance().baseName()
        return ''.join(c for c in name if c.isalnum() or c in ' _-').strip()

    def _get_output_dir(self, styles_dir):
        if styles_dir:
            project_name = self._get_project_name()
            if not project_name:
                self.iface.messageBar().pushMessage(
                    self.tr('Warning'),
                    self.tr('Project is not saved. Please save the project first.'),
                    level=Qgis.Warning, duration=5)
                return None
            output_dir = os.path.join(styles_dir, project_name)
            os.makedirs(output_dir, exist_ok=True)
            return output_dir
        else:
            return QFileDialog.getExistingDirectory(
                self.iface.mainWindow(), self.tr('Select output directory')) or None

    def run_export(self):
        selected_layers = self.iface.layerTreeView().selectedLayers()

        if not selected_layers:
            self.iface.messageBar().pushMessage(
                self.tr('Error'), self.tr('No layers selected'), level=Qgis.Warning)
            return

        _, _, styles_dir = self._load_settings()
        output_dir = self._get_output_dir(styles_dir)
        if not output_dir:
            return

        exported_count = 0
        for layer in selected_layers:
            if isinstance(layer, QgsVectorLayer):
                file_name = f'{layer.name()}_{self.get_vector_layer_type(layer)}_style.qml'
            elif isinstance(layer, QgsRasterLayer):
                file_name = f'{layer.name()}_raster_style.qml'
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

    def run_import(self):
        active_layer = self.iface.activeLayer()
        if not active_layer:
            self.iface.messageBar().pushMessage(
                self.tr('Error'), self.tr('No active layer selected'), level=Qgis.Warning)
            return

        _, _, styles_dir = self._load_settings()
        file_path, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(), self.tr('Select style file'),
            styles_dir, self.tr('QGIS Layer Style File (*.qml)'))
        if not file_path:
            return

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

    # ── Helpers ───────────────────────────────────────────────────────────────

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
