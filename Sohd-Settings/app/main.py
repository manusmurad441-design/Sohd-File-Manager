"""Sohd Settings 0.1 native desktop settings application."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QAction, QFont, QKeySequence, QPalette, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from settings_core import (
    audio_information,
    installed_applications,
    load_settings,
    network_information,
    save_settings,
    screen_information,
    set_audio_mute,
    set_audio_volume,
    toggle_audio_mute,
    storage_information,
    system_information,
)

APP_NAME = "Sohd Settings"
APP_VERSION = "0.1.0"
SDK_PATH = os.environ.get("SOHD_SDK", "/home/ubuntu/Sohd-App-Format/bin/sohd")


def readable_size(value: int) -> str:
    size = float(value)
    for suffix in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or suffix == "TB":
            return f"{size:.1f} {suffix}" if suffix != "B" else f"{int(size)} B"
        size /= 1024
    return str(value)


def form_from_dict(values: dict[str, str]) -> QWidget:
    widget = QWidget()
    form = QFormLayout(widget)
    for key, value in values.items():
        label = QLabel(value)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow(key, label)
    return widget


class SettingsWindow(QMainWindow):
    def __init__(self, self_test: bool = False):
        super().__init__()
        self.self_test = self_test
        self.values = load_settings()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1050, 700)
        self.navigation = QListWidget(self)
        self.navigation.setMinimumWidth(190)
        self.pages = QStackedWidget(self)
        self._build_pages()
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        splitter = QHBoxLayout()
        splitter.setContentsMargins(12, 12, 12, 12)
        splitter.addWidget(self.navigation)
        splitter.addWidget(self.pages, 1)
        container = QWidget(self)
        container.setLayout(splitter)
        self.setCentralWidget(container)
        self._build_menu()
        self.navigation.setCurrentRow(0)
        self.statusBar().showMessage("Settings ready")
        if self_test:
            QTimer.singleShot(700, self._finish_self_test)

    def _add_page(self, title: str, widget: QWidget) -> None:
        self.navigation.addItem(QListWidgetItem(title))
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        self.pages.addWidget(scroll)

    @staticmethod
    def _page_layout(title: str, description: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(heading)
        detail = QLabel(description)
        detail.setWordWrap(True)
        detail.setStyleSheet("color: #687385;")
        layout.addWidget(detail)
        return page, layout

    def _build_pages(self) -> None:
        self._build_appearance()
        self._build_display()
        self._build_sound()
        self._build_network()
        self._build_storage()
        self._build_system()
        self._build_apps()
        self._build_language()
        self._build_about()

    def _build_appearance(self) -> None:
        page, layout = self._page_layout("Appearance", "Change the appearance of this Sohd Settings window. Changes are applied immediately and persisted locally.")
        group = QGroupBox("Theme", page)
        form = QFormLayout(group)
        self.theme = QComboBox(group)
        self.theme.addItems(["System", "Light", "Dark"])
        self.theme.setCurrentText(self.values.get("theme", "System"))
        self.theme.currentTextChanged.connect(self._theme_changed)
        form.addRow("Theme", self.theme)
        self.scale = QSpinBox(group)
        self.scale.setRange(80, 160)
        self.scale.setSingleStep(10)
        self.scale.setValue(int(self.values.get("font_scale", 100)))
        self.scale.valueChanged.connect(self._scale_changed)
        form.addRow("UI font scale", self.scale)
        layout.addWidget(group)
        layout.addStretch()
        self._add_page("Appearance", page)

    def _build_display(self) -> None:
        page, layout = self._page_layout("Display", "Information and controls for the display detected by Qt. Display geometry is read from the current desktop session.")
        self.display_info = QLabel()
        self.display_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.display_info)
        refresh = QPushButton("Refresh display information")
        refresh.clicked.connect(self.refresh_display)
        layout.addWidget(refresh)
        layout.addStretch()
        self._add_page("Display", page)
        self.refresh_display()

    def _build_sound(self) -> None:
        page, layout = self._page_layout("Sound", "Reads and changes the default host audio sink through PipeWire or PulseAudio tools when available.")
        self.sound_info = QLabel()
        self.sound_info.setWordWrap(True)
        layout.addWidget(self.sound_info)
        controls = QGroupBox("Default output", page)
        form = QFormLayout(controls)
        self.volume = QSlider(Qt.Orientation.Horizontal, controls)
        self.volume.setRange(0, 100)
        self.volume.setValue(int(self.values.get("volume", 50)))
        self.volume.valueChanged.connect(self.change_volume)
        form.addRow("Volume", self.volume)
        self.mute_button = QPushButton("Toggle mute", controls)
        self.mute_button.clicked.connect(self.toggle_mute)
        form.addRow("Mute", self.mute_button)
        layout.addWidget(controls)
        refresh = QPushButton("Refresh audio information")
        refresh.clicked.connect(self.refresh_sound)
        layout.addWidget(refresh)
        layout.addStretch()
        self._add_page("Sound", page)
        self.refresh_sound()

    def _build_network(self) -> None:
        page, layout = self._page_layout("Network", "Shows the active host network state using NetworkManager or iproute2. Connection configuration remains controlled by the host system.")
        self.network_info = QLabel()
        self.network_info.setWordWrap(True)
        self.network_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.network_info)
        refresh = QPushButton("Refresh network status")
        refresh.clicked.connect(self.refresh_network)
        layout.addWidget(refresh)
        layout.addStretch()
        self._add_page("Network", page)
        self.refresh_network()

    def _build_storage(self) -> None:
        page, layout = self._page_layout("Storage", "Reports real filesystem capacity for the root filesystem and the Settings application data location.")
        self.storage_info_label = QLabel()
        self.storage_bar = QProgressBar()
        self.storage_bar.setRange(0, 100)
        layout.addWidget(self.storage_info_label)
        layout.addWidget(self.storage_bar)
        refresh = QPushButton("Refresh storage information")
        refresh.clicked.connect(self.refresh_storage)
        layout.addWidget(refresh)
        layout.addStretch()
        self._add_page("Storage", page)
        self.refresh_storage()

    def _build_system(self) -> None:
        page, layout = self._page_layout("System information", "Read-only information collected from the local operating system and Python runtime.")
        self.system_info = QLabel()
        self.system_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.system_info)
        refresh = QPushButton("Refresh system information")
        refresh.clicked.connect(self.refresh_system)
        layout.addWidget(refresh)
        layout.addStretch()
        self._add_page("System information", page)
        self.refresh_system()

    def _build_apps(self) -> None:
        page, layout = self._page_layout("Application management", "Lists applications registered in the local Sohd installation root. Launch and uninstall use the existing local Sohd SDK.")
        self.app_list = QListWidget()
        self.app_list.setMinimumHeight(220)
        layout.addWidget(self.app_list)
        buttons = QHBoxLayout()
        refresh = QPushButton("Refresh applications")
        refresh.clicked.connect(self.refresh_apps)
        launch = QPushButton("Launch selected")
        launch.clicked.connect(self.launch_selected)
        uninstall = QPushButton("Uninstall selected")
        uninstall.clicked.connect(self.uninstall_selected)
        for button in (refresh, launch, uninstall):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        layout.addStretch()
        self._add_page("Applications", page)
        self.refresh_apps()

    def _build_language(self) -> None:
        page, layout = self._page_layout("Language", "Select the language preference stored for Sohd Settings. The current 0.1 interface is English; the preference is persisted for future localized resources.")
        group = QGroupBox("Application language", page)
        form = QFormLayout(group)
        self.language = QComboBox(group)
        self.language.addItem("English (en)", "en")
        self.language.addItem("العربية (ar)", "ar")
        selected = self.values.get("language", "en")
        index = self.language.findData(selected)
        self.language.setCurrentIndex(max(0, index))
        self.language.currentIndexChanged.connect(self.language_changed)
        form.addRow("Language", self.language)
        self.language_status = QLabel()
        form.addRow("Status", self.language_status)
        layout.addWidget(group)
        layout.addStretch()
        self._add_page("Language", page)
        self.language_changed(self.language.currentIndex())

    def _build_about(self) -> None:
        page, layout = self._page_layout("About Sohdow", "Information about the Sohd Settings application and its local-only design.")
        about = QLabel(f"<b>{APP_NAME} {APP_VERSION}</b><br><br>Part of the Sohdow 0.1 application ecosystem.<br>Built with PyQt6 and Python standard-library services.<br><br>Package ID: org.sohdow.settings<br>Runtime: python3<br><br>No store, account, telemetry, paid API, or cloud service is required.")
        about.setWordWrap(True)
        layout.addWidget(about)
        license_button = QPushButton("Open project license")
        license_button.clicked.connect(lambda: self._open_local_file(Path(__file__).resolve().parents[1] / "LICENSE"))
        layout.addWidget(license_button)
        layout.addStretch()
        self._add_page("About Sohdow", page)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(QAction("Refresh current section", self, shortcut=QKeySequence("F5"), triggered=self.refresh_current))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Quit", self, shortcut=QKeySequence("Ctrl+Q"), triggered=self.close))

    def _save(self, key: str, value) -> None:
        self.values[key] = value
        save_settings(self.values)
        self.statusBar().showMessage(f"Saved {key}", 2000)

    def _theme_changed(self, theme: str) -> None:
        self._save("theme", theme)
        self.apply_theme(theme)

    def apply_theme(self, theme: str) -> None:
        palette = QPalette()
        if theme == "Dark":
            palette.setColor(QPalette.ColorRole.Window, QColor("#20252b"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#edf2f7"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#15191e"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#edf2f7"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#303842"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#edf2f7"))
        elif theme == "Light":
            palette = QApplication.style().standardPalette()
        else:
            palette = QApplication.style().standardPalette()
        QApplication.instance().setPalette(palette)

    def _scale_changed(self, value: int) -> None:
        self._save("font_scale", value)
        font = QApplication.instance().font()
        font.setPointSizeF(max(8.0, 10.0 * value / 100.0))
        QApplication.instance().setFont(font)

    def refresh_display(self) -> None:
        screen = QApplication.primaryScreen()
        self.display_info.setText("<br>".join(f"<b>{key}:</b> {value}" for key, value in screen_information(screen).items()) if screen else "No display is available.")

    def refresh_sound(self) -> None:
        data = audio_information()
        self.sound_info.setText(f"<b>Source:</b> {data['source']}<br>{data['status'].replace(chr(10), '<br>')}")

    def change_volume(self, value: int) -> None:
        ok, message = set_audio_volume(value)
        self._save("volume", value)
        if not ok:
            self.statusBar().showMessage(message, 3000)

    def toggle_mute(self) -> None:
        ok, message = toggle_audio_mute()
        self.statusBar().showMessage(message, 3000)
        self.refresh_sound()

    def refresh_network(self) -> None:
        data = network_information()
        self.network_info.setText(f"<b>Source:</b> {data['source']}<br>{data['status'].replace(chr(10), '<br>')}")

    def refresh_storage(self) -> None:
        data = storage_information("/")
        used_percent = int(data["used"] * 100 / data["total"]) if data["total"] else 0
        self.storage_bar.setValue(used_percent)
        self.storage_info_label.setText(f"Root filesystem: {readable_size(data['used'])} used of {readable_size(data['total'])}; {readable_size(data['free'])} free ({used_percent}%).")

    def refresh_system(self) -> None:
        self.system_info.setText("<br>".join(f"<b>{key}:</b> {value}" for key, value in system_information().items()))

    def refresh_apps(self) -> None:
        self.app_list.clear()
        for app in installed_applications():
            item = QListWidgetItem(f"{app['id']}  —  version {app['version']}")
            item.setData(Qt.ItemDataRole.UserRole, app)
            self.app_list.addItem(item)
        if self.app_list.count() == 0:
            self.app_list.addItem("No applications are registered in the local Sohd root.")

    def _selected_app(self) -> dict | None:
        item = self.app_list.currentItem()
        value = item.data(Qt.ItemDataRole.UserRole) if item else None
        return value if isinstance(value, dict) else None

    def launch_selected(self) -> None:
        app = self._selected_app()
        if not app:
            self.statusBar().showMessage("Select an installed application first", 3000)
            return
        result = subprocess.Popen([SDK_PATH, "run", app["id"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.statusBar().showMessage(f"Launched {app['id']} (process {result.pid})", 3000)

    def uninstall_selected(self) -> None:
        app = self._selected_app()
        if not app:
            self.statusBar().showMessage("Select an installed application first", 3000)
            return
        answer = QMessageBox.question(self, "Uninstall application", f"Uninstall {app['id']}?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        result = subprocess.run([SDK_PATH, "uninstall", app["id"]], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            self.statusBar().showMessage(f"Uninstalled {app['id']}", 3000)
            self.refresh_apps()
        else:
            QMessageBox.critical(self, "Uninstall failed", result.stderr.strip() or "The Sohd SDK could not uninstall this application.")

    def language_changed(self, index: int) -> None:
        code = self.language.itemData(index)
        self._save("language", code)
        if code == "ar":
            self.language_status.setText("العربية محفوظة. ستحتاج الموارد المترجمة إلى إصدار لاحق.")
        else:
            self.language_status.setText("English is active for this 0.1 interface.")

    def refresh_current(self) -> None:
        index = self.pages.currentIndex()
        [self.refresh_display, self.refresh_sound, self.refresh_network, self.refresh_storage, self.refresh_system, self.refresh_apps][index]() if 0 <= index < 6 else None

    @staticmethod
    def _open_local_file(path: Path) -> None:
        if path.is_file():
            subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _finish_self_test(self) -> None:
        self.close()
        QApplication.instance().quit()


if __name__ == "__main__":
    self_test = "--self-test" in sys.argv
    if self_test:
        sys.argv.remove("--self-test")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    window = SettingsWindow(self_test)
    window.apply_theme(window.values.get("theme", "System"))
    window._scale_changed(int(window.values.get("font_scale", 100)))
    window.show()
    raise SystemExit(app.exec())
