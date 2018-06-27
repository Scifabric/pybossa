# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.
"""
PYBOSSA api module for exposing domain object ProjectStats via an API.
"""
import copy
from flask import request
from pybossa.model.project_stats import ProjectStats
from .api_base import APIBase


class ProjectStatsAPI(APIBase):

    """Class for domain object ProjectStats."""

    __class__ = ProjectStats

    def _select_attributes(self, stats_data):
        if not request.args.get('full'):
            tmp = copy.deepcopy(stats_data)
            tmp['info'].pop('hours_stats', None)
            tmp['info'].pop('dates_stats', None)
            tmp['info'].pop('users_stats', None)
            return tmp
        return stats_data
