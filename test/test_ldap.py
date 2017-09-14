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
import json
from default import with_context, Test
from mock import patch


class TestLDAP(Test):

    @with_context
    def test_register_404(self):
        """Test register is disabled for ldap."""
        with patch.dict(self.flask_app.config, {'LDAP_HOST': '127.0.0.1'}):
            url = '/account/register'
            res = self.app_get_json(url)
            data = json.loads(res.data)
            assert data['code'] == 404, data

    @with_context
    def test_account_signin(self):
        """Test signin."""
        with patch.dict(self.flask_app.config, {'LDAP_HOST': '127.0.0.1'}):
            url = '/account/signin'
            res = self.app_get_json(url)
            data = json.loads(res.data)
            assert data['form']['csrf'] is not None
            assert data['auth']['twitter'] is False
            assert data['auth']['facebook'] is False
            assert data['auth']['google'] is False
