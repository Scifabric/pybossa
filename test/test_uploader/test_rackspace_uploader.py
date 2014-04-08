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
"""This module tests the Uploader class."""

from base import web, model, Fixtures, db, redis_flushall
from pybossa.uploader.rackspace import RackspaceUploader
from mock import patch
from werkzeug.datastructures import FileStorage


class TestRackspaceUploader:

    """Test PyBossa Rackspace Uploader module."""

    def setUp(self):
        """SetUp method."""
        self.app = web.app.test_client()
        model.rebuild_db()
        redis_flushall()
        Fixtures.create()

    def tearDown(self):
        """Tear Down method."""
        db.session.remove()
        redis_flushall()

    @classmethod
    def teardown_class(cls):
        """Tear Down class."""
        model.rebuild_db()
        redis_flushall()

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials', return_value=True)
    def test_rackspace_uploader_init(self, Mock):
        """Test RACKSPACE UPLOADER init works."""
        new_extensions = set(['pdf', 'doe'])
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles.get_container',
                   return_value='pybossa'):
            u = RackspaceUploader("username",
                                  "apikey",
                                  "ORD",
                                  allowed_extensions=new_extensions)
            for ext in new_extensions:
                err_msg = "The .%s extension should be allowed" % ext
                assert ext in u.allowed_extensions, err_msg
