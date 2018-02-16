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
from flask.ext.login import current_user
from werkzeug.exceptions import BadRequest, Conflict
from pybossa.model.task import Task
from pybossa.model.project import Project
from pybossa.core import result_repo
from api_base import APIBase
from pybossa.api.pwd_manager import get_pwd_manager
from pybossa.util import get_user_id_or_ip
from pybossa.core import task_repo
from pybossa.cache.projects import get_project_data
import json


class TaskAPI(APIBase):

    """Class for domain object Task."""

    __class__ = Task
    reserved_keys = set(['id', 'created', 'state', 'fav_user_ids'])

    def _forbidden_attributes(self, data):
        for key in data.keys():
            if key in self.reserved_keys:
                raise BadRequest("Reserved keys in payload")

    def _update_attribute(self, new, old):
        if (new.state == 'completed') and (old.n_answers <= new.n_answers):
            new.state = 'ongoing'

    def _preprocess_post_data(self, data):
        project_id = data["project_id"]
        info = data["info"]
        duplicate = task_repo.find_duplicate(project_id=project_id, info=info)
        if duplicate:
            message = {
                'reason': 'DUPLICATE_TASK',
                'task_id': duplicate
            }
            raise Conflict(json.dumps(message))
        if 'n_answers' not in data:
            project = Project(**get_project_data(project_id))
            data['n_answers'] = project.get_default_n_answers()

    def _verify_auth(self, item):
        if not current_user.is_authenticated():
            return False
        if current_user.admin or current_user.subadmin:
            return True
        project = Project(**get_project_data(item.project_id))
        pwd_manager = get_pwd_manager(project)
        return not pwd_manager.password_needed(project, get_user_id_or_ip())
