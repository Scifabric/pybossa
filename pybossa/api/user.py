# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
PyBossa api module for domain object USER via an API.

This package adds GET method for:
    * users

"""
from api_base import APIBase
from pybossa.model import User
import json
from flask import request, abort, Response
from flask.views import MethodView
from werkzeug.exceptions import NotFound
from pybossa.util import jsonpify, crossdomain
from pybossa.core import db
from pybossa.auth import require
from pybossa.hateoas import Hateoas
from pybossa.ratelimit import ratelimit
from pybossa.error import ErrorStatus

cors_headers = ['Content-Type', 'Authorization']



class UserAPI(APIBase):

    """
    Class for the domain object User.

    """

    __class__ = User


def _get(self):
    print self
    print "Aqui pasa algoooooooooooooooooooo-------------------"
    return Response(json.dumps({'hola':'quease'}),
                                    mimetype='application/json')

@jsonpify
@crossdomain(origin='*', headers=cors_headers)
@ratelimit(limit=300, per=15 * 60)
def get(self, id):
    return Response(json.dumps({'hola':'quease'}),
                                    mimetype='application/json')
