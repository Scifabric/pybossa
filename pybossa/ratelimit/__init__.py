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
# Cache global variables for timeouts
import os
import time
from functools import update_wrapper, wraps
from redis.sentinel import Sentinel
from flask import request, g
from werkzeug.exceptions import TooManyRequests
from pybossa.error import ErrorStatus

try:
    import settings_local as settings
except ImportError: # pragma: no cover
    os.environ['PYBOSSA_RATELIMIT_DISABLED'] = '1'

sentinel = Sentinel(settings.REDIS_SENTINEL, socket_timeout=0.1)
error = ErrorStatus()


class RateLimit(object):
    expiration_window = 10

    def __init__(self, key_prefix, limit, per, send_x_headers):
        self.reset = (int(time.time()) // per) * per + per
        self.key = key_prefix + str(self.reset)
        self.limit = limit
        self.per = per
        self.send_x_headers = send_x_headers

        master = sentinel.master_for(settings.REDIS_MASTER)

        p = master.pipeline()
        p.incr(self.key)
        p.expireat(self.key, self.reset + self.expiration_window)
        self.current = min(p.execute()[0], limit)

    remaining = property(lambda x: x.limit - x.current)
    over_limit = property(lambda x: x.current >= x.limit)


#def on_over_limit(limit):
#    return error.format_exception(TooManyRequests, action=limit.key)
#    #return 'You hit the rate limit', 429


def get_view_rate_limit():
    return getattr(g, '_view_rate_limit', None)


def ratelimit(limit, per=300, send_x_headers=True,
              #over_limit=on_over_limit,
              scope_func=lambda: request.remote_addr,
              key_func=lambda: request.endpoint,
              path=lambda: request.path):
    def decorator(f):
        @wraps(f)
        def rate_limited(*args, **kwargs):
            try:
                key = 'rate-limit/%s/%s/' % (key_func(), scope_func())
                rlimit = RateLimit(key, limit, per, send_x_headers)
                g._view_rate_limit = rlimit
                #if over_limit is not None and rlimit.over_limit:
                if rlimit.over_limit:
                    raise TooManyRequests
                return f(*args, **kwargs)
            except Exception as e:
                return error.format_exception(e, target=path(),
                                              action=f.__name__)
        return update_wrapper(rate_limited, f)
    return decorator
