#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2024 TinyPedal developers, see contributors.md file
#
#  This file is part of TinyPedal.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Vehicle class editor
"""

import time
import random

from PySide2.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QDialogButtonBox,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox
)

from ..api_control import api
from ..setting import cfg, copy_setting
from ..module_control import wctrl
from .. import formatter as fmt
from ._common import (
    BaseEditor,
    DoubleClickEdit,
    QVAL_COLOR,
    QSS_EDITOR_BUTTON,
    QSS_EDITOR_LISTBOX,
    update_preview_color,
)


class VehicleClassEditor(BaseEditor):
    """Vehicle class editor"""

    def __init__(self, master):
        super().__init__(master)
        self.setWindowTitle(f"Vehicle Class Editor - {cfg.filename.classes}")
        self.setMinimumSize(400, 400)

        self.option_classes = []
        self.classes_temp = copy_setting(cfg.user.classes)

        # Classes list box
        self.listbox_classes = QListWidget(self)
        self.listbox_classes.setStyleSheet(QSS_EDITOR_LISTBOX)
        self.refresh_list()

        # Button
        button_add = QPushButton("Add")
        button_add.clicked.connect(self.add_class)
        button_add.setStyleSheet(QSS_EDITOR_BUTTON)

        button_reset = QDialogButtonBox(QDialogButtonBox.Reset)
        button_reset.clicked.connect(self.reset_setting)
        button_reset.setStyleSheet(QSS_EDITOR_BUTTON)

        button_apply = QDialogButtonBox(QDialogButtonBox.Apply)
        button_apply.clicked.connect(self.applying)
        button_apply.setStyleSheet(QSS_EDITOR_BUTTON)

        button_save = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Close)
        button_save.accepted.connect(self.saving)
        button_save.rejected.connect(self.close)
        button_save.setStyleSheet(QSS_EDITOR_BUTTON)

        # Set layout
        layout_main = QVBoxLayout()
        layout_button = QHBoxLayout()

        layout_button.addWidget(button_add)
        layout_button.addWidget(button_reset)
        layout_button.addStretch(1)
        layout_button.addWidget(button_apply)
        layout_button.addWidget(button_save)

        layout_main.addWidget(self.listbox_classes)
        layout_main.addLayout(layout_button)
        self.setLayout(layout_main)

    def refresh_list(self):
        """Refresh classes list"""
        self.listbox_classes.clear()
        self.option_classes.clear()
        already_modified = self.is_modified()

        for idx, key in enumerate(self.classes_temp):
            layout_item = QHBoxLayout()
            layout_item.setContentsMargins(4,4,4,4)
            layout_item.setSpacing(4)

            line_edit_key = self.__add_option_string(key, layout_item)
            for sub_key, sub_item in self.classes_temp[key].items():
                line_edit_sub_key = self.__add_option_string(sub_key, layout_item)
                color_edit = self.__add_option_color(sub_item, layout_item, 80)
                self.__add_delete_button(idx, layout_item)
                self.option_classes.append((line_edit_key, line_edit_sub_key, color_edit))

            classes_item = QWidget()
            classes_item.setLayout(layout_item)
            item = QListWidgetItem()
            self.listbox_classes.addItem(item)
            self.listbox_classes.setItemWidget(item, classes_item)

        if not already_modified:
            self.set_unmodified()

    def __add_option_string(self, key, layout):
        """Key string"""
        line_edit = QLineEdit()
        line_edit.textChanged.connect(self.set_modified)
        # Load selected option
        line_edit.setText(key)
        # Add layout
        layout.addWidget(line_edit)
        return line_edit

    def __add_option_color(self, key, layout, width):
        """Color string"""
        color_edit = DoubleClickEdit(mode="color", init=key)
        color_edit.setFixedWidth(width)
        color_edit.setMaxLength(9)
        color_edit.setValidator(QVAL_COLOR)
        color_edit.textChanged.connect(self.set_modified)
        color_edit.textChanged.connect(
            lambda color_str, option=color_edit:
            update_preview_color(color_str, option))
        # Load selected option
        color_edit.setText(key)
        # Add layout
        layout.addWidget(color_edit)
        return color_edit

    def __add_delete_button(self, idx, layout):
        """Delete button"""
        button = QPushButton("X")
        button.setFixedWidth(20)
        button.pressed.connect(
            lambda index=idx: self.delete_class(index))
        layout.addWidget(button)

    def delete_class(self, index):
        """Delete class entry"""
        target = self.option_classes[index][0].text()
        if not self.confirm_deletion(f"Delete class '{target}' ?"):
            return

        self.update_classes_temp()
        self.classes_temp.pop(target)
        self.set_modified()
        self.refresh_list()

    def add_class(self):
        """Add new class entry"""
        self.update_classes_temp()
        # New class entry
        new_veh_class = {
            "New Class Name":
            {"NAME": fmt.random_color_class(str(random.random()))}
        }
        # Get all vehicle class from active session
        veh_total = api.read.vehicle.total_vehicles()
        if veh_total > 0:
            session_veh_class = {
                api.read.vehicle.class_name(index):
                {"NAME": fmt.random_color_class(api.read.vehicle.class_name(index))}
                for index in range(veh_total)
            }
            # Update new class to class temp
            for key, item in session_veh_class.items():
                if key not in self.classes_temp:
                    self.classes_temp.update({key: item})
        # Add new class entry
        self.classes_temp.update(new_veh_class)
        self.set_modified()
        self.refresh_list()
        # Move focus to new class row
        self.listbox_classes.setCurrentRow(len(self.classes_temp) - 1)

    def reset_setting(self):
        """Reset setting"""
        message_text = (
            "Are you sure you want to reset class preset to default? <br><br>"
            "Changes are only saved after clicking Apply or Save Button."
        )
        reset_msg = QMessageBox.question(
            self, "Reset Class Preset", message_text,
            buttons=QMessageBox.Yes | QMessageBox.No)
        if reset_msg == QMessageBox.Yes:
            self.classes_temp = copy_setting(cfg.default.classes)
            self.set_modified()
            self.refresh_list()

    def applying(self):
        """Save & apply"""
        self.save_setting()

    def saving(self):
        """Save & close"""
        self.save_setting()
        self.accept()  # close

    def update_classes_temp(self):
        """Update temporary changes to classes temp first"""
        self.classes_temp.clear()
        for edit in self.option_classes:
            key_name = edit[0].text()
            sub_key_name = edit[1].text()
            sub_item_name = edit[2].text()
            self.classes_temp[key_name] = {sub_key_name: sub_item_name}

    def save_setting(self):
        """Save setting"""
        self.update_classes_temp()
        self.refresh_list()
        cfg.user.classes = copy_setting(self.classes_temp)
        cfg.save(0, "classes")
        while cfg.is_saving:  # wait saving finish
            time.sleep(0.01)
        wctrl.reload()
        self.set_unmodified()
