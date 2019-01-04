# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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
from default import db, with_context
from test_api import TestAPI
from mock import patch
from factories import UserFactory

class TestDisqusSSO(TestAPI):

    @with_context
    def test_auth(self):
        """Test with user authenticated."""
        url = 'api/disqus/sso'
        user = UserFactory.create()

        DISQUS_PUBLIC_KEY = 'public'
        DISQUS_SECRET_KEY = 'secret'

        patch_dict = {'DISQUS_PUBLIC_KEY': DISQUS_PUBLIC_KEY,
                      'DISQUS_SECRET_KEY': DISQUS_SECRET_KEY}

        with patch.dict(self.flask_app.config, patch_dict):
            res = self.app.get(url + '?api_key=%s' % user.api_key)
            data = json.loads(res.data)
            assert res.status_code == 200, res.status_code
            assert data['remote_auth_s3'] is not None, data
            assert data['api_key'] is not None, data

    @with_context
    def test_anon(self):
        """Test with user authenticated."""
        url = 'api/disqus/sso'

        DISQUS_PUBLIC_KEY = 'public'
        DISQUS_SECRET_KEY = 'secret'

        patch_dict = {'DISQUS_PUBLIC_KEY': DISQUS_PUBLIC_KEY,
                      'DISQUS_SECRET_KEY': DISQUS_SECRET_KEY}

        with patch.dict(self.flask_app.config, patch_dict):
            res = self.app.get(url)
            data = json.loads(res.data)
            assert res.status_code == 200, (res.data, res.status_code)
            assert data['remote_auth_s3'] is not None, data
            assert data['api_key'] is not None, data

    @with_context
    def test_auth_no_keys(self):
        """Test auth with no keys."""
        url = 'api/disqus/sso'
        user = UserFactory.create()

        res = self.app.get(url + '?api_key=%s' % user.api_key)
        data = json.loads(res.data)
        assert res.status_code == 405, res.status_code
        assert data['status_code'] == 405, data
        assert data['status'] == 'failed', data
        assert data['exception_msg'] == 'Disqus keys are missing'

    @with_context
    def test_anon_no_keys(self):
        """Test anon with no keys."""
        url = 'api/disqus/sso'

        res = self.app.get(url)
        data = json.loads(res.data)
        assert res.status_code == 405, res.status_code
        assert data['status_code'] == 405, data
        assert data['status'] == 'failed', data
        assert data['exception_msg'] == 'Disqus keys are missing'
