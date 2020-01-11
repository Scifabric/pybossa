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

from redis import sentinel, StrictRedis


class Sentinel(object):

    def __init__(self, app=None):
        self.app = app
        self.master = StrictRedis()
        self.slave = self.master
        if app is not None:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        socket_timeout = app.config.get('REDIS_SOCKET_TIMEOUT', None)
        retry_on_timeout = app.config.get('REDIS_RETRY_ON_TIMEOUT', True)
        self.connection = sentinel.Sentinel(app.config['REDIS_SENTINEL'],
                                            socket_timeout=socket_timeout,
                                            retry_on_timeout=retry_on_timeout)
        redis_db = app.config.get('REDIS_DB') or 0
        redis_master = app.config.get('REDIS_MASTER') or 'mymaster'
        self.master = self.connection.master_for(redis_master, db=redis_db)
        self.slave = self.connection.slave_for(redis_master, db=redis_db)
