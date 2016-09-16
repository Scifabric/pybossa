# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.
"""
PyBossa api module for exposing domain object Task via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * tasks

"""

from werkzeug.exceptions import BadRequest
from pybossa.model.task import Task
import json
from flask import request, abort, Response
from flask.ext.login import current_user
from pybossa.util import jsonpify, crossdomain
from pybossa.core import ratelimits
from pybossa.auth import ensure_authorized_to
from pybossa.ratelimit import ratelimit
from pybossa.core import result_repo, task_repo
from api_base import APIBase, cors_headers
from pybossa.error import ErrorStatus

error = ErrorStatus()

class TaskAPI(APIBase):

    """Class for domain object Task."""

    __class__ = Task
    reserved_keys = set(['id', 'created', 'state'])

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def get(self, oid):
        """Get an object.
        Returns an item from the DB with the request.data JSON object or all
        the items if oid == None
        :arg self: The class of the object to be retrieved
        :arg integer oid: the ID of the object in the DB
        :returns: The JSON item/s stored in the DB
        """
        try:
            ensure_authorized_to('read', self.__class__)
            query = self._db_query(oid)
            json_response = self._create_json_response(query, oid)
            data = json.loads(json_response)
            task_run = task_repo.get_task_run_by(project_id=data['project_id'], task_id=data['id'], user=current_user)
            data['info']['processed'] = True if task_run else False
            json_response = json.dumps(data)
            return Response(json_response, mimetype='application/json')
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='GET')

    def _forbidden_attributes(self, data):
        for key in data.keys():
            if key in self.reserved_keys:
                raise BadRequest("Reserved keys in payload")
