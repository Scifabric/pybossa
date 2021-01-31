# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2021 Scifabric LTD.
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
from mock import patch
from default import with_context, Test
from pybossa.extensions import Sentinel


class TestSentinel(Test):

    @with_context
    def test_is_configured(self):
        """Test sentinel is configured."""
        sentinel = Sentinel()
        sentinel.init_app(self.flask_app)
        assert sentinel.connection is not None
        assert sentinel.connection
        # We get the redis-client for mymaster
        redis_client = sentinel.connection.master_for('mymaster')
        redis_client.set('foo', 'bar')
        assert redis_client.get('foo') == b'bar'
        assert sentinel.master.get('foo') == b'bar'
        assert sentinel.slave.get('foo') == b'bar'
        sentinel.master.delete('foo')
        assert redis_client.get('foo') is None

    @with_context
    def test_is_not_configured(self):
        """Test sentinel is not configured."""
        sentinel = Sentinel()
        with patch.dict(self.flask_app.config, {'REDIS_SENTINEL': None}):
            sentinel.init_app(self.flask_app)
            assert sentinel.connection is None
            assert sentinel.master.set('foo', 'bar')
            assert sentinel.master.get('foo') == b'bar'
            assert sentinel.slave.get('foo') == b'bar'
            sentinel.master.delete('foo')
            assert sentinel.master.get('foo') is None
            assert sentinel.slave.get('foo') is None
