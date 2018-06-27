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
PYBOSSA api module for exposing domain object Task via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * tasks

"""
from flask import abort
from werkzeug.exceptions import BadRequest
from pybossa.model.task import Task
from pybossa.core import result_repo
from .api_base import APIBase


class TaskAPI(APIBase):

    """Class for domain object Task."""

    __class__ = Task
    reserved_keys = set(['id', 'created', 'state', 'fav_user_ids'])

    def _forbidden_attributes(self, data):
        for key in list(data.keys()):
            if key in self.reserved_keys:
                raise BadRequest("Reserved keys in payload")

    def _update_attribute(self, new, old):
        if (new.state == 'completed') and (old.n_answers <= new.n_answers):
            new.state = 'ongoing'
