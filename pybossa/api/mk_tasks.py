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
PYBOSSA api module for exposing domain object TaskRun via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * task_runs

"""
import json
import time
from flask import request, Response, current_app
from flask_login import current_user
from pybossa.model.task_run import TaskRun
from werkzeug.exceptions import Forbidden, BadRequest

from .api_base import APIBase
from pybossa.util import get_mykaarma_username_from_full_name
from pybossa.util import get_user_id_or_ip, get_avatar_url
from pybossa.core import task_repo, sentinel, anonymizer, project_repo, flagged_task_repo
from pybossa.core import uploader
from pybossa.contributions_guard import ContributionsGuard
from pybossa.auth import jwt_authorize_project
from pybossa.auth import ensure_authorized_to, is_authorized
from pybossa.sched import can_post

##Adding user repos for saving user to database
from pybossa.model.user import User
from pybossa.core import user_repo
from pybossa.model.task import Task
from pybossa.model.flagged_task import FlaggedTask


class mkTaskAPI(APIBase):

    """Class API for domain object TaskRun."""

    __class__ = Task
    reserved_keys = set(['id', 'created', 'finish_time'])

    def check_can_post(self, project_id, task_id, user_ip_or_id):
        pass

    def _update_object(self,task):
        """Update task_run object with user id or ip."""
        pass
        
    def _forbidden_attributes(self, data):
        pass
        
    def _validate_project_and_task(self, taskrun, task):
        pass

    def _ensure_task_was_requested(self, task, guard):
        pass

    def _add_user_info(self):
                   
        pass

    def _add_created_timestamp(self, taskrun, task, guard):
        pass

    def _file_upload(self, data):
        """Method that must be overriden by the class to allow file uploads for
        only a few classes."""
        cls_name = self.__class__.__name__.lower()
        content_type_text =  'application/json'
        request_headers = request.headers.get('Content-Type')
        if request_headers is None:
            request_headers = []
        if ( (content_type_text in request_headers)
            and cls_name in self.allowed_classes_upload):
            data = dict()
            enc = json.loads(request.data)
            data['id'] = enc['task_id']
            task = task_repo.get_task(enc['task_id'])
            data['project_id'] = task.project_id
            task.state="completed"
            task.flagged=1
            task_repo.update(task)            
            data['state']='completed'
            data['flagged']=1
            data['project_id'] = 1
            flag_task = FlaggedTask(project_id=data['project_id'], task_id=data['id'], user_id=current_user.id, reason=enc['reason'])
            flagged_task_repo.save(flag_task)
            return data
        else:
            return None

    def _file_delete(self, request, obj):
        pass
                                         