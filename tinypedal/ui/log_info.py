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
Log window
"""

from PySide2.QtGui import QTextCursor
from PySide2.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QDialogButtonBox,
    QTextBrowser,
    QPushButton,
)

from .. import log_stream
from ._common import BaseDialog


class LogInfo(BaseDialog):
    """Create log info dialog"""

    def __init__(self, master):
        super().__init__(master)
        self.set_utility_title("Log")

        # Text view
        self.log_view = QTextBrowser()
        self.log_view.setStyleSheet("font-size: 12px;")
        self.log_view.setMinimumSize(550, 300)
        self.refresh_log()

        # Button
        button_refresh = QPushButton("Refresh")
        button_refresh.clicked.connect(self.refresh_log)
        button_clear = QPushButton("Clear")
        button_clear.clicked.connect(self.clear_log)
        button_close = QDialogButtonBox(QDialogButtonBox.Close)
        button_close.rejected.connect(self.reject)

        # Layout
        layout_button = QHBoxLayout()
        layout_button.addWidget(button_refresh)
        layout_button.addWidget(button_clear)
        layout_button.addWidget(button_close)
        layout_button.setContentsMargins(5,5,5,5)

        layout_main = QVBoxLayout()
        layout_main.addWidget(self.log_view)
        layout_main.addLayout(layout_button)
        layout_main.setContentsMargins(3,3,3,7)
        self.setLayout(layout_main)

    def refresh_log(self):
        """Refresh log"""
        self.log_view.setText(log_stream.getvalue())
        self.log_view.moveCursor(QTextCursor.End)

    def clear_log(self):
        """Clear log"""
        log_stream.truncate(0)
        log_stream.seek(0)
        self.refresh_log()
