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
from pybossa.jobs import create_onesignal_app
from default import Test, with_context 
from mock import patch, MagicMock, call
from factories import ProjectFactory, UserFactory, CategoryFactory
from pybossa.core import project_repo


class TestOnesignal(Test):

    def setUp(self):
        super(TestOnesignal, self).setUp()
        CategoryFactory.create()

    @with_context
    @patch('pybossa.jobs.PybossaOneSignal')
    def test_create_onesignal_no_config(self, mock_onesignal):
        """Test create_onesignal with no config works."""

        project = ProjectFactory.create()

        client = MagicMock()
        client.create_app.return_value = (200, 'OK',
                                          {'basic_auth': 'auth', 'id': 1})
        mock_onesignal.return_value = client

        create_onesignal_app(project.id)

        assert client.called is False

    @with_context
    @patch('pybossa.jobs.PybossaOneSignal')
    @patch('pybossa.model.event_listeners.webpush_queue.enqueue')
    def test_create_onesignal(self, mock_queue, mock_onesignal):
        """Test create_onesignal with config works."""
        client = MagicMock()
        osdata = {'basic_auth': 'auth', 'id': 1}
        client.create_app.return_value = (200, 'OK', osdata)
        mock_onesignal.return_value = client

        with patch.dict(self.flask_app.config, {'ONESIGNAL_AUTH_KEY': 'key'}):
            user = UserFactory.create()
            project_data = dict(name='name', short_name='short_name',
                                description='desc',
                                long_description='long')
            url = '/api/project?api_key=%s' % user.api_key

            res = self.app.post(url, data=json.dumps(project_data))

            assert res.status_code == 200, res.data

            project = json.loads(res.data)

            mock_queue.assert_called_with(create_onesignal_app, project['id'])

            res = create_onesignal_app(project['id'])

            assert res[0] == 200, res
            assert res[1] == 'OK', res
            assert res[2]['id'] == 1, res

            new = project_repo.get(project['id'])

            assert new.info['onesignal'] == osdata, new.info
            assert new.info['onesignal_app_id'] == 1, new.info
