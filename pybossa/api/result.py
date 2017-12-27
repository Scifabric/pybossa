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
PYBOSSA api module for exposing domain object Result via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * tasks

"""
from werkzeug.exceptions import BadRequest
from pybossa.model.result import Result
from api_base import APIBase
from pybossa.core import task_repo, result_repo
from pybossa.model import make_timestamp


class ResultAPI(APIBase):

    """Class for domain object Result."""

    __class__ = Result
    reserved_keys = set(['id', 'created', 'project_id',
                         'task_run_ids', 'last_version'])

    def _forbidden_attributes(self, data):
        for key in data.keys():
            if key in self.reserved_keys:
                raise BadRequest("Reserved keys in payload")

    def _update_object(self, inst):
        if not inst.task_id:
            raise BadRequest('Invalid task id')
        task_id = inst.task_id
        results = result_repo.get_by(task_id=task_id)
        if results:
            raise BadRequest('Record is already present')
        task = task_repo.get_task(task_id)
        if not task or task.state != 'completed':
            raise BadRequest('Invalid task')
        inst.created = make_timestamp()
        inst.project_id = task.project_id
        inst.task_run_ids = [tr.id for tr in task.task_runs]
        inst.last_version = True