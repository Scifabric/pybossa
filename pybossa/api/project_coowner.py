# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2017 SciFabric LTD.
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
PyBossa api module for domain object ProjectCoowner via an API.
This package adds GET, POST, PUT and DELETE methods for:
    * projectcoowners
"""

import json
from api_base import APIBase
from pybossa.model.project_coowner import ProjectCoowner


class ProjectCoownerAPI(APIBase):

    """Class API for domain object ProjectCoowner."""

    __class__ = ProjectCoowner

    def _create_dict_from_model(self, model):
        """Replaces the User object with the user.id."""
        obj = model.dictize()
        obj['coowner_id'] = obj['coowner_id'].id
        return obj

    def _create_json_response(self, query_result, oid):
        """Consolidates return objects to 1 object per project
        with a list of coowner_ids.

            original = [{"project_id": 2, "coowner_id": 3},
                        {"project_id": 2, "coowner_id": 5},
                        {"project_id": 3, "coowner_id": 1}]

            consolidated = [{'coowner_ids': [3, 5], 'project_id': 2},
                            {'coowner_ids': [1], 'project_id': 3}]

        """
        json_obj = super(ProjectCoownerAPI, self)._create_json_response(query_result, oid)
        obj = json.loads(json_obj)
        projects = list(set([i['project_id'] for i in obj]))
        consolidated_obj = [{'project_id': project, 'coowner_ids': [coowner['coowner_id']
                            for coowner in obj if coowner['project_id'] == project]}
                            for project in projects]
        return json.dumps(consolidated_obj)
