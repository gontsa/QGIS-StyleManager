import os
from qgis.PyQt.QtCore import QCoreApplication, QTranslator, QLocale

from .style_manager import StyleExporterImporterPlugin

_translator = None

def classFactory(iface):
    global _translator
    locale = QLocale.system().name()  # e.g. 'uk_UA', 'en_US'
    locale_short = locale[:2]         # e.g. 'uk', 'en'

    plugin_dir = os.path.dirname(__file__)
    for name in (locale, locale_short):
        ts_path = os.path.join(plugin_dir, 'i18n', f'i18n_{name}.qm')
        if os.path.isfile(ts_path):
            _translator = QTranslator()
            _translator.load(ts_path)
            QCoreApplication.installTranslator(_translator)
            break

    return StyleExporterImporterPlugin(iface)
