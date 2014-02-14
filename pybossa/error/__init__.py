# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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
PyBossa error module for processing error status.

This package adds GET, POST, PUT and DELETE errors for the API:
    * applications,
    * tasks and
    * task_runs

"""
import json
from flask import Response


class ErrorStatus(object):

    """
    Class for formatting error status in JSON format.

    This class has the following methods:
        * format_exception: returns a Flask Response with the error.

    """

    error_status = {"Forbidden": 403,
                    "NotFound": 404,
                    "Unauthorized": 401,
                    "MethodNotAllowed": 405,
                    "TypeError": 415,
                    "ValueError": 415,
                    "DataError": 415,
                    "AttributeError": 415,
                    "IntegrityError": 415,
                    "TooManyRequests": 429}

    def format_exception(self, e, target, action):
        """
        Format the exception to a valid JSON object.

        Returns a Flask Response with the error.

        """
        exception_cls = e.__class__.__name__
        if self.error_status.get(exception_cls):
            status = self.error_status.get(exception_cls)
        else: # pragma: no cover
            status = 500
        if exception_cls == 'Forbidden' or exception_cls == 'Unauthorized':
            e.message = e.description
        error = dict(action=action.upper(),
                     status="failed",
                     status_code=status,
                     target=target,
                     exception_cls=exception_cls,
                     exception_msg=e.message)
        return Response(json.dumps(error), status=status,
                        mimetype='application/json')
