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
Mapping module
"""

import logging
from functools import partial

from ._base import DataModule
from ..module_info import minfo
from ..api_control import api
from .. import calculation as calc
from .. import svg

MODULE_NAME = "module_mapping"

logger = logging.getLogger(__name__)
round4 = partial(round, ndigits=4)


class Realtime(DataModule):
    """Mapping data"""

    def __init__(self, config):
        super().__init__(config, MODULE_NAME)
        self.filepath = self.cfg.path.track_map

    def update_data(self):
        """Update module data"""
        reset = False
        update_interval = self.active_interval

        recorder = MapRecorder(self.filepath)

        while not self._event.wait(update_interval):
            if self.state.active:

                if not reset:
                    reset = True
                    update_interval = self.active_interval

                    recorder.map.load(api.read.check.track_id())
                    if recorder.map.exist:
                        update_interval = self.idle_interval
                        minfo.mapping.coordinates = recorder.map.raw_coords
                        minfo.mapping.coordinatesHash = hash(minfo.mapping.coordinates)
                        minfo.mapping.elevations = recorder.map.raw_dists
                        minfo.mapping.elevationsHash = hash(minfo.mapping.elevations)
                        minfo.mapping.sectors = recorder.map.sectors_index
                    else:
                        recorder.reset()
                        minfo.mapping.coordinates = None
                        minfo.mapping.coordinatesHash = None
                        minfo.mapping.elevations = None
                        minfo.mapping.elevationsHash = None
                        minfo.mapping.sectors = None

                if not recorder.map.exist:
                    recorder.update()
                    if recorder.map.exist:
                        reset = False  # load recorded map in next loop
            else:
                if reset:
                    reset = False
                    update_interval = self.idle_interval


class MapRecorder:
    """Map data recorder"""

    def __init__(self, filepath):
        self.map = MapData(filepath)
        self._recording = False
        self._validating = False
        self._last_lap_stime = -1  # last lap start time
        self._last_sector_idx = -1
        self._pos_last = 0  # last checked player vehicle position

    def reset(self):
        """Reset to defaults"""
        self._recording = False
        self._validating = False
        self._last_sector_idx = -1
        self._last_lap_stime = -1
        self._pos_last = 0

    def update(self):
        """Update map data"""
        # Read telemetry
        lap_stime = api.read.timing.start()
        lap_etime = api.read.timing.elapsed()
        laptime_valid = api.read.timing.last_laptime()
        sector_idx = api.read.lap.sector_index()
        pos_curr = round4(api.read.lap.distance())
        gps_curr = (round4(api.read.vehicle.position_longitudinal()),
                    round4(api.read.vehicle.position_lateral()))
        elv_curr = round4(api.read.vehicle.position_vertical())

        # Update map data
        self.__start(lap_stime)
        if self._validating:
            self.__validate(lap_etime, laptime_valid)
        if self._recording:
            self.__record_sector(sector_idx)
            self.__record_path(pos_curr, gps_curr, elv_curr)

    def __start(self, lap_stime):
        """Lap start & finish detection"""
        # Init reset
        if self._last_lap_stime == -1:
            self.map.reset()
            self._last_lap_stime = lap_stime
        # New lap
        if lap_stime > self._last_lap_stime:
            self.__record_end()
            self.map.reset()
            self._last_lap_stime = lap_stime
            self._pos_last = 0
            self._recording = True
            #logger.info("map recording")

    def __validate(self, lap_etime, laptime_valid):
        """Validate map data after crossing finish line"""
        laptime_curr = lap_etime - self._last_lap_stime
        if 1 < laptime_curr <= 8 and laptime_valid > 0:
            self.map.save()
            self.map.exist = True
            self._recording = False
            self._validating = False
        # Switch off validating after 8s
        elif 8 < laptime_curr < 10:
            self._validating = False

    def __record_sector(self, sector_idx):
        """Record sector index"""
        if self._last_sector_idx != sector_idx:
            if sector_idx == 1:
                self.map.sectors_index[0] = len(self.map.raw_coords) - 1
            elif sector_idx == 2:
                self.map.sectors_index[1] = len(self.map.raw_coords) - 1
            self._last_sector_idx = sector_idx

    def __record_path(self, pos_curr, gps_curr, elv_curr):
        """Record driving path"""
        # Update if position value is different & positive
        if 0 <= pos_curr != self._pos_last:
            if pos_curr > self._pos_last:  # position further
                self.map.raw_coords.append(gps_curr)
                self.map.raw_dists.append((pos_curr, elv_curr))
            self._pos_last = pos_curr  # reset last position

    def __record_end(self):
        """End recording"""
        if self.map.raw_coords:
            self.map.copy()
            self._validating = True


class MapData:
    """Map data"""

    def __init__(self, filepath):
        self.exist = False
        # Raw data
        self.raw_coords = None
        self.raw_dists = None
        self.sectors_index = None
        # File info
        self._filepath = filepath
        self._filename = None
        # Temp data
        self._temp_raw_coords = None
        self._temp_raw_dists = None
        self._temp_sectors_index = None

    def reset(self):
        """Reset map data"""
        self.exist = False
        self.raw_coords = []
        self.raw_dists = []
        self.sectors_index = [0,0]

    def copy(self):
        """Copy map data to temp and convert to tuple for hash"""
        self._temp_raw_coords = tuple(self.raw_coords)
        self._temp_raw_dists = tuple(self.raw_dists)
        self._temp_sectors_index = tuple(self.sectors_index)

    def load(self, filename):
        """Load map data file"""
        self._filename = filename
        # Load map file
        raw_coords, raw_dists, sectors_index = svg.load_track_map_file(
            f"{self._filepath}{self._filename}.svg"
        )
        if raw_coords and raw_dists:
            self.raw_coords = raw_coords
            self.raw_dists = raw_dists
            self.sectors_index = sectors_index
            self.exist = True
            #logger.info("map exist")
        else:
            self.exist = False
            #logger.info("map not exist")

    def save(self):
        """Store & convert raw coordinates to svg points data"""
        self.raw_coords = self._temp_raw_coords
        self.raw_dists = self._temp_raw_dists
        self.sectors_index = self._temp_sectors_index
        # Save to svg file
        svg.save_track_map_file(
            self._filename,
            self._filepath,
            self.raw_coords,
            self.raw_dists,
            calc.svg_view_box(self.raw_coords, 20),
            self.sectors_index
        )
        #logger.info("map saved, stopped map recording")
