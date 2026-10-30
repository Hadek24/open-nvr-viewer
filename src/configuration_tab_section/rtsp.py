"""RTSP template management for Open NVR Viewer.

Built-in templates are displayed for selection but cannot be edited or deleted
through the GUI. User-defined templates are stored in the ``rtsp_templates``
section of config.json, alongside NVR profiles, so encrypted backups include
both the template catalog and profile references automatically.
"""

from uuid import uuid4

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
)

from src.config import (
    BUILTIN_RTSP_TEMPLATES,
    get_config_path,
    load_raw_config,
    save_raw_config,
    ensure_rtsp_templates,
)
from src.styles import (
    configuration_action_button_style,
    configuration_scroll_area_style,
    configuration_section_title_style,
    configuration_section_description_style,
    configuration_subsection_title_style,
    configuration_field_label_style,
    configuration_field_style,
    configuration_separator_style,
    rtsp_template_table_style,
)


class RTSPSection(QWidget):
    """List, create, edit, and delete user-defined RTSP URL templates."""

    templates_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.editing_template_id = None
        self.creating_template = False

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.StyledPanel)
        self.scroll_area.setStyleSheet(configuration_scroll_area_style)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(10)
        self.scroll_area.setWidget(self.content)
        self.main_layout.addWidget(self.scroll_area)

        self.title = QLabel("RTSP URL Templates")
        self.title.setStyleSheet(configuration_section_title_style)
        self.description = QLabel(
            "Manage the RTSP URL formats used by NVR profiles. Built-in "
            "templates are generic examples and may not work with every NVR. "
            "They are read-only; custom templates can be created, edited, "
            "or deleted. Available variables: {username}, {password}, "
            "{ip}, {port}, {channel}, {stream}, {stream_index}, "
            "{stream_padded}, and {channel_code}."
        )
        self.description.setWordWrap(True)
        self.description.setStyleSheet(configuration_section_description_style)
        self.content_layout.addWidget(self.title)
        self.content_layout.addWidget(self.description)

        self.separator = QLabel()
        self.separator.setFixedHeight(1)
        self.separator.setStyleSheet(configuration_separator_style)
        self.content_layout.addSpacing(8)
        self.content_layout.addWidget(self.separator)
        self.content_layout.addSpacing(8)

        self.list_title = QLabel("Available RTSP Templates")
        self.list_title.setStyleSheet(configuration_subsection_title_style)
        self.content_layout.addWidget(self.list_title)

        self.template_table = QTableWidget(0, 2)
        self.template_table.setHorizontalHeaderLabels(
            ["RTSP URL name", "RTSP URL format"]
        )
        self.template_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.template_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.template_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.template_table.setStyleSheet(rtsp_template_table_style)
        self.template_table.verticalHeader().setVisible(False)
        self.template_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.template_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.template_table.setMinimumHeight(170)
        self.template_table.currentCellChanged.connect(self.show_selected_template)
        self.content_layout.addWidget(self.template_table)

        self.actions_layout = QHBoxLayout()
        self.new_button = QPushButton("New")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        for button in (self.new_button, self.edit_button, self.delete_button):
            button.setStyleSheet(configuration_action_button_style)
            button.setFixedWidth(100)
            self.actions_layout.addWidget(button)
        self.actions_layout.addStretch()
        self.content_layout.addLayout(self.actions_layout)

        # Separador entre la administración de plantillas y los detalles RTSP.
        self.separator = QLabel()
        self.separator.setFixedHeight(1)
        self.separator.setStyleSheet(configuration_separator_style)

        self.content_layout.addSpacing(8)
        self.content_layout.addWidget(self.separator)
        self.content_layout.addSpacing(8)

        self.editor_title = QLabel("RTSP URL Details")
        self.editor_title.setStyleSheet(configuration_subsection_title_style)
        self.content_layout.addSpacing(8)
        self.content_layout.addWidget(self.editor_title)

        self.name_label = QLabel("RTSP URL name:")
        self.name_label.setStyleSheet(configuration_field_label_style)
        self.name_field = QLineEdit()
        self.name_field.setStyleSheet(configuration_field_style)

        self.url_label = QLabel("RTSP URL format:")
        self.url_label.setStyleSheet(configuration_field_label_style)
        self.url_field = QLineEdit()
        self.url_field.setStyleSheet(configuration_field_style)

        self.content_layout.addWidget(self.name_label)
        self.content_layout.addWidget(self.name_field)
        self.content_layout.addWidget(self.url_label)
        self.content_layout.addWidget(self.url_field)

        self.editor_status = QLabel(
            "Select a template to view its details, or choose New to create one."
        )
        self.editor_status.setWordWrap(True)
        self.editor_status.setStyleSheet(configuration_section_description_style)
        self.content_layout.addWidget(self.editor_status)

        self.editor_buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Create")
        self.cancel_button = QPushButton("Cancel")
        for button in (self.save_button, self.cancel_button):
            button.setStyleSheet(configuration_action_button_style)
            button.setFixedWidth(100)
            self.editor_buttons_layout.addWidget(button)
        self.editor_buttons_layout.addStretch()
        self.content_layout.addLayout(self.editor_buttons_layout)
        self.content_layout.addStretch()

        self.new_button.clicked.connect(self.start_create)
        self.edit_button.clicked.connect(self.start_edit)
        self.delete_button.clicked.connect(self.delete_selected)
        self.save_button.clicked.connect(self.save_template)
        self.cancel_button.clicked.connect(self.cancel_edit)

        self.set_editor_enabled(False)
        self.refresh_templates()

    def _read_config(self, require_existing=False):
        """Load config.json and ensure the built-in template catalog exists."""
        config = load_raw_config()
        if not isinstance(config, dict):
            if require_existing:
                QMessageBox.information(
                    self,
                    "Configuration Required",
                    "Generate the configuration file before managing RTSP templates.\n\n"
                    f"Expected location: {get_config_path()}",
                )
            return None

        if ensure_rtsp_templates(config):
            save_raw_config(config)
        return config

    def _selected_template(self):
        """Return the selected template dictionary, if a row is selected."""
        row = self.template_table.currentRow()
        if row < 0:
            return None
        item = self.template_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole + 1) if item else None

    def refresh_templates(self, select_id=None):
        """Refresh the table while preserving selection by stable template ID."""
        config = self._read_config()
        if config is None:
            templates = [item.copy() for item in BUILTIN_RTSP_TEMPLATES]
        else:
            templates = config.get("rtsp_templates", [])

        self.template_table.blockSignals(True)
        self.template_table.setRowCount(0)
        selected_row = -1

        for template in templates:
            if not isinstance(template, dict):
                continue
            row = self.template_table.rowCount()
            self.template_table.insertRow(row)
            template_id = template.get("id")
            name = template.get("name", "Unnamed template")
            url_template = template.get("url_template", "")
            template_type = template.get("type", "custom")
            suffix = " [Built-in]" if template_type == "builtin" else " [Custom]"

            name_item = QTableWidgetItem(f"{name}{suffix}")
            name_item.setData(Qt.ItemDataRole.UserRole, template_id)
            name_item.setData(Qt.ItemDataRole.UserRole + 1, template.copy())
            url_item = QTableWidgetItem(url_template)
            url_item.setToolTip(url_template)
            self.template_table.setItem(row, 0, name_item)
            self.template_table.setItem(row, 1, url_item)

            if template_id == select_id:
                selected_row = row

        self.template_table.blockSignals(False)
        if selected_row >= 0:
            self.template_table.setCurrentCell(selected_row, 0)
        elif self.template_table.rowCount():
            self.template_table.setCurrentCell(0, 0)
        else:
            self.clear_editor()
        self.update_action_state()

    def show_selected_template(
        self, current_row, current_column=0, previous_row=-1, previous_column=0
    ):
        """Show selected template details without enabling accidental changes."""
        if self.creating_template or self.editing_template_id:
            return
        if current_row < 0:
            self.clear_editor()
            self.update_action_state()
            return

        item = self.template_table.item(current_row, 0)
        template = item.data(Qt.ItemDataRole.UserRole + 1) if item else {}
        template = template or {}
        self.name_field.setText(template.get("name", ""))
        self.url_field.setText(template.get("url_template", ""))
        self.name_field.setReadOnly(True)
        self.url_field.setReadOnly(True)
        self.editor_status.setText(
            "Built-in template — read-only. Create a custom template if you need a different format."
            if template.get("type") == "builtin"
            else "Custom template. Select Edit to modify it."
        )
        self.update_action_state()

    def update_action_state(self):
        """Enable edit/delete only for selected custom templates."""
        template = self._selected_template()
        is_custom = bool(template and template.get("type") != "builtin")
        self.edit_button.setEnabled(
            is_custom and not self.creating_template and not self.editing_template_id
        )
        self.delete_button.setEnabled(
            is_custom and not self.creating_template and not self.editing_template_id
        )
        self.new_button.setEnabled(
            not self.creating_template and not self.editing_template_id
        )

    def set_editor_enabled(self, enabled):
        """Enable or lock the editable fields and editor action buttons."""
        self.name_field.setReadOnly(not enabled)
        self.url_field.setReadOnly(not enabled)
        self.save_button.setEnabled(enabled)
        self.cancel_button.setEnabled(enabled)

    def clear_editor(self):
        """Clear editor fields and return to view-only mode."""
        self.name_field.clear()
        self.url_field.clear()
        self.set_editor_enabled(False)
        self.editor_status.setText(
            "Select a template to view its details, or choose New to create one."
        )

    def start_create(self):
        """Enter creation mode for a new user-defined template."""
        if self._read_config(require_existing=True) is None:
            return
        self.creating_template = True
        self.editing_template_id = None
        self.template_table.setEnabled(False)
        self.name_field.clear()
        self.url_field.clear()
        self.editor_status.setText(
            "Enter a name and a URL format, then select Create."
        )
        self.save_button.setText("Create")
        self.set_editor_enabled(True)
        self.update_action_state()
        self.name_field.setFocus()

    def start_edit(self):
        """Enter edit mode for a selected custom template."""
        template = self._selected_template()
        if not template or template.get("type") == "builtin":
            return
        self.editing_template_id = template.get("id")
        self.creating_template = False
        self.template_table.setEnabled(False)
        self.name_field.setReadOnly(False)
        self.url_field.setReadOnly(False)
        self.editor_status.setText("Edit the template and select Save Changes.")
        self.save_button.setText("Save Changes")
        self.set_editor_enabled(True)
        self.update_action_state()
        self.name_field.setFocus()

    def save_template(self):
        """Validate and persist a newly created or edited custom template."""
        name = self.name_field.text().strip()
        url_template = self.url_field.text().strip()

        if not name or not url_template:
            QMessageBox.warning(
                self,
                "RTSP Template",
                "Both the template name and URL format are required.",
            )
            return
        if not url_template.lower().startswith("rtsp://"):
            QMessageBox.warning(
                self,
                "RTSP Template",
                "The URL format must start with rtsp://.",
            )
            return

        config = self._read_config(require_existing=True)
        if config is None:
            return
        templates = config.setdefault("rtsp_templates", [])

        if any(
            isinstance(item, dict)
            and item.get("name", "").casefold() == name.casefold()
            and item.get("id") != self.editing_template_id
            for item in templates
        ):
            QMessageBox.warning(
                self,
                "RTSP Template",
                "A template with this name already exists.",
            )
            return

        if self.creating_template:
            template_id = f"custom-{uuid4().hex}"
            templates.append({
                "id": template_id,
                "name": name,
                "url_template": url_template,
                "type": "custom",
            })
        else:
            template = next(
                (item for item in templates
                 if isinstance(item, dict)
                 and item.get("id") == self.editing_template_id),
                None,
            )
            if template is None or template.get("type") == "builtin":
                QMessageBox.warning(
                    self,
                    "RTSP Template",
                    "The selected custom template could not be found.",
                )
                self.cancel_edit()
                return
            template["name"] = name
            template["url_template"] = url_template
            template_id = self.editing_template_id

        save_raw_config(config)
        self.creating_template = False
        self.editing_template_id = None
        self.template_table.setEnabled(True)
        self.save_button.setText("Create")
        self.set_editor_enabled(False)
        self.refresh_templates(select_id=template_id)
        self.templates_changed.emit()
        QMessageBox.information(
            self,
            "RTSP Template",
            "The template was saved successfully. Changes to a template used "
            "by the active profile will take effect after restarting the application.",
        )

    def delete_selected(self):
        """Delete a custom template only when no profile uses it."""
        template = self._selected_template()
        if not template or template.get("type") == "builtin":
            return

        config = self._read_config(require_existing=True)
        if config is None:
            return
        profiles = config.get("profiles", {})
        template_id = template.get("id")
        users = [
            profile.get("name", profile_id)
            for profile_id, profile in profiles.items()
            if isinstance(profile, dict)
            and profile.get("RTSP_TEMPLATE_ID") == template_id
        ]
        if users:
            QMessageBox.warning(
                self,
                "RTSP Template In Use",
                "This template is assigned to the following profile(s):\n\n"
                + "\n".join(users)
                + "\n\nAssign another template to those profiles before deleting it.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Delete RTSP Template",
            f"Delete the custom template '{template.get('name', '')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        config["rtsp_templates"] = [
            entry for entry in config.get("rtsp_templates", [])
            if not isinstance(entry, dict) or entry.get("id") != template_id
        ]
        save_raw_config(config)
        self.refresh_templates()
        self.templates_changed.emit()

    def cancel_edit(self):
        """Cancel creation/editing and restore view-only mode."""
        self.creating_template = False
        self.editing_template_id = None
        self.template_table.setEnabled(True)
        self.save_button.setText("Create")
        self.set_editor_enabled(False)
        self.refresh_templates()
        self.update_action_state()

