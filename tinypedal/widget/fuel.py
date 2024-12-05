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
Fuel Widget
"""

from .. import calculation as calc
from ..module_info import minfo
from ._base import Overlay
from ._painter import FuelLevelBar

WIDGET_NAME = "fuel"


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Overlay.__init__(self, config, WIDGET_NAME)
        layout = self.set_grid_layout(gap=self.wcfg["bar_gap"])
        self.set_primary_layout(layout=layout)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        text_def = "-.--"
        bar_padx = self.set_padding(self.wcfg["font_size"], self.wcfg["bar_padding"])
        self.bar_width = max(self.wcfg["bar_width"], 3)
        style_width = font_m.width * self.bar_width + bar_padx

        self.decimals = tuple(
            map(self.decimal_range, (
            self.wcfg["decimal_places_end"],  # 0
            self.wcfg["decimal_places_remain"],  # 1
            self.wcfg["decimal_places_refuel"],  # 2
            self.wcfg["decimal_places_used"],  # 3
            self.wcfg["decimal_places_delta"],  # 4
            self.wcfg["decimal_places_early"],  # 5
            self.wcfg["decimal_places_laps"],  # 6
            self.wcfg["decimal_places_minutes"],  # 7
            self.wcfg["decimal_places_save"],  # 8
            self.wcfg["decimal_places_pits"],  # 9
        )))

        # Base style
        self.setStyleSheet(self.set_qss(
            font_family=self.wcfg["font_name"],
            font_size=self.wcfg["font_size"],
            font_weight=self.wcfg["font_weight"])
        )

        # Create layout
        layout_upper = self.set_grid_layout()
        layout_lower = self.set_grid_layout()
        layout.addLayout(layout_upper, self.wcfg["column_index_upper"], 0)
        layout.addLayout(layout_lower, self.wcfg["column_index_lower"], 0)

        # Caption
        if self.wcfg["show_caption"]:
            bar_style_desc = self.set_qss(
                fg_color=self.wcfg["font_color_caption"],
                bg_color=self.wcfg["bkg_color_caption"],
                font_size=int(self.wcfg['font_size'] * 0.8)
            )
            caption_upper = (
                self.wcfg["caption_text_end"],
                self.wcfg["caption_text_remain"],
                self.wcfg["caption_text_refuel"],
                self.wcfg["caption_text_used"],
                self.wcfg["caption_text_delta"],
            )
            caption_lower = (
                self.wcfg["caption_text_early"],
                self.wcfg["caption_text_laps"],
                self.wcfg["caption_text_minutes"],
                self.wcfg["caption_text_save"],
                self.wcfg["caption_text_pits"],
            )

            row_idx_upper = 2 * self.wcfg["swap_upper_caption"]
            for index, text_caption in enumerate(caption_upper):
                cap_temp = self.set_qlabel(
                    text=text_caption,
                    style=bar_style_desc,
                    fixed_width=style_width,
                )
                layout_upper.addWidget(cap_temp, row_idx_upper, index)

            row_idx_lower = 2 - 2 * self.wcfg["swap_lower_caption"]
            for index, text_caption in enumerate(caption_lower):
                cap_temp = self.set_qlabel(
                    text=text_caption,
                    style=bar_style_desc,
                    fixed_width=style_width,
                )
                layout_lower.addWidget(cap_temp, row_idx_lower, index)

        # Estimated end remaining
        bar_style_end = self.set_qss(
            fg_color=self.wcfg["font_color_end"],
            bg_color=self.wcfg["bkg_color_end"]
        )
        self.bar_end = self.set_qlabel(
            text=text_def,
            style=bar_style_end,
            fixed_width=style_width,
        )

        # Remaining
        self.bar_style_curr = (
            self.set_qss(
                fg_color=self.wcfg["font_color_remain"],
                bg_color=self.wcfg["bkg_color_remain"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_remain"],
                bg_color=self.wcfg["warning_color_low_fuel"])
        )
        self.bar_curr = self.set_qlabel(
            text=text_def,
            style=self.bar_style_curr[0],
            fixed_width=style_width,
        )

        # Total needed
        self.bar_style_need = (
            self.set_qss(
                fg_color=self.wcfg["font_color_refuel"],
                bg_color=self.wcfg["bkg_color_refuel"]),
            self.set_qss(
                fg_color=self.wcfg["font_color_refuel"],
                bg_color=self.wcfg["warning_color_low_fuel"])
        )
        self.bar_need = self.set_qlabel(
            text=text_def,
            style=self.bar_style_need[0],
            fixed_width=style_width,
        )

        # Estimated consumption
        bar_style_used = self.set_qss(
            fg_color=self.wcfg["font_color_used"],
            bg_color=self.wcfg["bkg_color_used"]
        )
        self.bar_used = self.set_qlabel(
            text=text_def,
            style=bar_style_used,
            fixed_width=style_width,
        )

        # Delta consumption
        bar_style_delta = self.set_qss(
            fg_color=self.wcfg["font_color_delta"],
            bg_color=self.wcfg["bkg_color_delta"]
        )
        self.bar_delta = self.set_qlabel(
            text=text_def,
            style=bar_style_delta,
            fixed_width=style_width,
        )

        # Estimate pit stop counts when pitting at end of current lap
        bar_style_early = self.set_qss(
            fg_color=self.wcfg["font_color_early"],
            bg_color=self.wcfg["bkg_color_early"]
        )
        self.bar_early = self.set_qlabel(
            text=text_def,
            style=bar_style_early,
            fixed_width=style_width,
        )

        # Estimated laps can last
        bar_style_laps = self.set_qss(
            fg_color=self.wcfg["font_color_laps"],
            bg_color=self.wcfg["bkg_color_laps"]
        )
        self.bar_laps = self.set_qlabel(
            text=text_def,
            style=bar_style_laps,
            fixed_width=style_width,
        )

        # Estimated minutes can last
        bar_style_mins = self.set_qss(
            fg_color=self.wcfg["font_color_minutes"],
            bg_color=self.wcfg["bkg_color_minutes"]
        )
        self.bar_mins = self.set_qlabel(
            text=text_def,
            style=bar_style_mins,
            fixed_width=style_width,
        )

        # Estimated one less pit consumption
        bar_style_save = self.set_qss(
            fg_color=self.wcfg["font_color_save"],
            bg_color=self.wcfg["bkg_color_save"]
        )
        self.bar_save = self.set_qlabel(
            text=text_def,
            style=bar_style_save,
            fixed_width=style_width,
        )

        # Estimate pit stop counts when pitting at end of current stint
        bar_style_pits = self.set_qss(
            fg_color=self.wcfg["font_color_pits"],
            bg_color=self.wcfg["bkg_color_pits"]
        )
        self.bar_pits = self.set_qlabel(
            text=text_def,
            style=bar_style_pits,
            fixed_width=style_width,
        )

        # Fuel level bar
        if self.wcfg["show_fuel_level_bar"]:
            self.bar_level = FuelLevelBar(
                width=(font_m.width * self.bar_width + bar_padx) * 5,
                height=max(self.wcfg["fuel_level_bar_height"], 1),
                start_mark_width=max(self.wcfg["starting_fuel_level_mark_width"], 1),
                refill_mark_width=max(self.wcfg["refueling_level_mark_width"], 1),
                input_color=self.wcfg["highlight_color_fuel_level"],
                bg_color=self.wcfg["bkg_color_fuel_level"],
                start_mark_color=self.wcfg["starting_fuel_level_mark_color"],
                refill_mark_color=self.wcfg["refueling_level_mark_color"],
                show_start_mark=self.wcfg["show_starting_fuel_level_mark"],
                show_refill_mark=self.wcfg["show_refueling_level_mark"],
            )
            layout.addWidget(self.bar_level, self.wcfg["column_index_middle"], 0)

        # Set layout
        layout_upper.addWidget(self.bar_end, 1, 0)
        layout_upper.addWidget(self.bar_curr, 1, 1)
        layout_upper.addWidget(self.bar_need, 1, 2)
        layout_upper.addWidget(self.bar_used, 1, 3)
        layout_upper.addWidget(self.bar_delta, 1, 4)
        layout_lower.addWidget(self.bar_early, 1, 0)
        layout_lower.addWidget(self.bar_laps, 1, 1)
        layout_lower.addWidget(self.bar_mins, 1, 2)
        layout_lower.addWidget(self.bar_save, 1, 3)
        layout_lower.addWidget(self.bar_pits, 1, 4)

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if self.state.active:
            is_low_fuel = minfo.fuel.estimatedLaps <= self.wcfg["low_fuel_lap_threshold"]

            # Estimated end remaining
            amount_end = f"{self.fuel_units(minfo.fuel.amountEndStint):.{self.decimals[0]}f}"
            self.update_fuel(self.bar_end, amount_end)

            # Remaining
            amount_curr = f"{self.fuel_units(minfo.fuel.amountCurrent):.{self.decimals[1]}f}"
            self.update_fuel(self.bar_curr, amount_curr, self.bar_style_curr[is_low_fuel])

            # Total needed
            amount_need = f"{calc.sym_max(self.fuel_units(minfo.fuel.amountNeeded), 9999):+.{self.decimals[2]}f}"
            self.update_fuel(self.bar_need, amount_need, self.bar_style_need[is_low_fuel])

            # Estimated consumption
            used_last = f"{self.fuel_units(minfo.fuel.estimatedConsumption):.{self.decimals[3]}f}"
            self.update_fuel(self.bar_used, used_last)

            # Delta consumption
            delta_fuel = f"{self.fuel_units(minfo.fuel.deltaConsumption):+.{self.decimals[4]}f}"
            self.update_fuel(self.bar_delta, delta_fuel)

            # Estimate pit stop counts when pitting at end of current lap
            est_pits_early = f"{calc.zero_max(minfo.fuel.estimatedNumPitStopsEarly, 99.99):.{self.decimals[5]}f}"
            self.update_fuel(self.bar_early, est_pits_early)

            # Estimated laps can last
            est_runlaps = f"{min(minfo.fuel.estimatedLaps, 9999):.{self.decimals[6]}f}"
            self.update_fuel(self.bar_laps, est_runlaps)

            # Estimated minutes can last
            est_runmins = f"{min(minfo.fuel.estimatedMinutes, 9999):.{self.decimals[7]}f}"
            self.update_fuel(self.bar_mins, est_runmins)

            # Estimated one less pit consumption
            fuel_save = f"{calc.zero_max(self.fuel_units(minfo.fuel.oneLessPitConsumption), 99.99):.{self.decimals[8]}f}"
            self.update_fuel(self.bar_save, fuel_save)

            # Estimate pit stop counts when pitting at end of current stint
            est_pits_end = f"{calc.zero_max(minfo.fuel.estimatedNumPitStopsEnd, 99.99):.{self.decimals[9]}f}"
            self.update_fuel(self.bar_pits, est_pits_end)

            # Fuel level bar
            if self.wcfg["show_fuel_level_bar"]:
                level_capacity = minfo.fuel.capacity
                level_curr = minfo.fuel.amountCurrent
                level_start = minfo.fuel.amountStart
                level_refill = level_curr + minfo.fuel.amountNeeded
                level_state = round(level_start * level_refill, 3)
                if level_capacity and self.bar_level.last != level_state:
                    self.bar_level.last = level_state
                    self.bar_level.update_input(
                        level_curr / level_capacity,
                        level_start / level_capacity,
                        level_refill / level_capacity,
                    )

    # GUI update methods
    def update_fuel(self, target, data, color=None):
        """Update fuel data"""
        if target.last != data:
            target.last = data
            if color:  # low fuel warning
                target.setStyleSheet(color)
            target.setText(data[:self.bar_width].strip("."))

    # Additional methods
    def fuel_units(self, fuel):
        """2 different fuel unit conversion, default is Liter"""
        if self.cfg.units["fuel_unit"] == "Gallon":
            return calc.liter2gallon(fuel)
        return fuel

    @staticmethod
    def decimal_range(value):
        """Decimal place range"""
        return calc.zero_max(int(value), 3)
