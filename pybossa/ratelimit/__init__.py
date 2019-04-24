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
# Cache global variables for timeouts
"""
Rate limit module for limiting the requests in the API.

This module exports:
    * RateLimit class: for limiting the requests
    * ratelimit decorator: for decorating the views

"""
import time
from functools import update_wrapper, wraps
from flask import request, g
from werkzeug.exceptions import TooManyRequests
from pybossa.core import sentinel, anonymizer
from pybossa.error import ErrorStatus
from flask_login import current_user
from flask import current_app

error = ErrorStatus()


class RateLimit(object):

    """
    Limit the number of requests.

    It uses a Redis pipe from the master node (configured via Sentinel) to
    limit the number of requests.

    """

    expiration_window = 10

    def __init__(self, key_prefix, limit, per, send_x_headers):
        self.reset = (int(time.time()) // per) * per + per
        self.key = key_prefix + str(self.reset)
        self.limit = limit
        self.per = per
        self.send_x_headers = send_x_headers

        if not current_user.is_anonymous and current_user.admin:
            self.limit *= current_app.config.get("ADMIN_RATE_MULTIPLIER", 1)

        p = sentinel.master.pipeline()
        p.incr(self.key)
        p.expireat(self.key, self.reset + self.expiration_window)

        self.current = min(p.execute()[0], limit)

    remaining = property(lambda x: x.limit - x.current)
    over_limit = property(lambda x: x.current >= x.limit)


def get_view_rate_limit():
    """Return the rate limit values."""
    return getattr(g, '_view_rate_limit', None)


def default_scope_func():
    if current_app.config.get('RATE_LIMIT_BY_USER_ID'):
        if current_user.is_authenticated:
            return current_user.id
    return anonymizer.ip(request.remote_addr or '127.0.0.1')


def ratelimit(limit, per, send_x_headers=True,
              scope_func=default_scope_func,
              key_func=lambda: request.endpoint,
              path=lambda: request.path):
    """
    Decorator for limiting the access to a route.

    Returns the function if within the limit, otherwise TooManyRequests error

    """
    def decorator(f):
        @wraps(f)
        def rate_limited(*args, **kwargs):
            try:
                key = 'rate-limit/%s/%s/' % (key_func(), scope_func())
                rlimit = RateLimit(key, limit, per, send_x_headers)
                g._view_rate_limit = rlimit
                # if over_limit is not None and rlimit.over_limit:
                if rlimit.over_limit:
                    raise TooManyRequests
                return f(*args, **kwargs)
            except Exception as e:
                return error.format_exception(e, target=path(),
                                              action=f.__name__)
        return update_wrapper(rate_limited, f)
    return decorator
