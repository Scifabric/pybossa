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

from base import web, model, Fixtures, db, redis_flushall
from mock import Mock, MagicMock, PropertyMock
from pyrax.fakes import FakeContainer



def setup_package():
    model.rebuild_db()
    redis_flushall()


def teardown_package():
    db.session.remove()
    model.rebuild_db()
    redis_flushall()


#fake_container = Mock(spec=FakeContainer)
fake_container = MagicMock()
cdn_uri_mock = PropertyMock(return_value='http://rackspace.com')
type(fake_container).cdn_uri = cdn_uri_mock
cdn_enabled_mock = PropertyMock(return_value=True)
type(fake_container).cdn_enabled = cdn_enabled_mock

cloudfiles_mock = MagicMock()
cloudfiles_mock.get_container.return_value = fake_container
