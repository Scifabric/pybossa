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
        conn_kwargs = {
            'db': app.config.get('REDIS_DB') or 0,
            'password': app.config.get('REDIS_PWD'),
            'socket_timeout': app.config.get('REDIS_SOCKET_TIMEOUT', 0.1),
            'retry_on_timeout': app.config.get('REDIS_RETRY_ON_TIMEOUT', True)
        }
        if app.config.get('REDIS_MASTER_DNS') and \
            app.config.get('REDIS_SLAVE_DNS') and \
            app.config.get('REDIS_PORT'):
            self.master = StrictRedis(host=app.config['REDIS_MASTER_DNS'],
                port=app.config['REDIS_PORT'], **conn_kwargs)
            self.slave = StrictRedis(host=app.config['REDIS_SLAVE_DNS'],
                port=app.config['REDIS_PORT'], **conn_kwargs)
        else:
            self.connection = sentinel.Sentinel(app.config['REDIS_SENTINEL'],
                                                **conn_kwargs)
            redis_master = app.config.get('REDIS_MASTER') or 'mymaster'
            self.master = self.connection.master_for(redis_master)
            self.slave = self.connection.slave_for(redis_master)
