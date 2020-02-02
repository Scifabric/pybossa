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

from mock import Mock, MagicMock, PropertyMock


fake_container = MagicMock()
fake_container.make_public.return_value = True
cdn_ssl_uri_mock = PropertyMock(return_value='https://rackspace.com')
type(fake_container).cdn_ssl_uri = cdn_ssl_uri_mock
cdn_enabled_mock = PropertyMock(return_value=True)
type(fake_container).cdn_enabled = cdn_enabled_mock

cloudfiles_mock = MagicMock()
cloudfiles_mock.get_container.return_value = fake_container
