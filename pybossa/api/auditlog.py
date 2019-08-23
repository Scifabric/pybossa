# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2019 Scifabric LTD.
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
PYBOSSA api module for exposing domain object Auditlog via an API.
"""
from pybossa.model.auditlog import Auditlog
from api_base import APIBase
from werkzeug.exceptions import MethodNotAllowed


class AuditlogAPI(APIBase):

    """Class for domain object Auditlog."""

    __class__ = Auditlog

    def put(self, oid=None):
        raise MethodNotAllowed

    def post(self):
        raise MethodNotAllowed

    def delete(self, oid=None):
        raise MethodNotAllowed
