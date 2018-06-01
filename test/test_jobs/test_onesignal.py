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
from pybossa.jobs import push_notification
from default import Test, with_context
from mock import patch, MagicMock, call
from factories import ProjectFactory, UserFactory, CategoryFactory
from pybossa.core import project_repo
from flask import url_for


class TestOnesignal(Test):

    def setUp(self):
        super(TestOnesignal, self).setUp()
        CategoryFactory.create()

    @with_context
    @patch('pybossa.jobs.PybossaOneSignal')
    def test_push_notification_onesignal_no_config(self, mock_onesignal):
        """Test push_notification with no config works."""

        user = UserFactory.create()

        project = ProjectFactory.create(owner=user)

        blog = dict(title="hello", body="world", project_id=project.id)

        url = '/api/blogpost?api_key=%s' % user.api_key

        res = self.app.post(url, data=json.dumps(blog))
       
        assert res.status_code == 200, res.data
        assert mock_onesignal.called is False

    @with_context
    @patch('pybossa.jobs.PybossaOneSignal')
    @patch('pybossa.model.event_listeners.webpush_queue.enqueue')
    def test_push_notification(self, mock_queue, mock_onesignal):
        """Test push_notification with config works."""

        user = UserFactory.create()

        project = ProjectFactory.create(owner=user)

        blog = dict(title="hello", body="world", project_id=project.id)

        url = '/api/blogpost?api_key=%s' % user.api_key

        res = self.app.post(url, data=json.dumps(blog))

        blogdata = json.loads(res.data)
       
        assert res.status_code == 200, res.data

        contents = {"en": "New update!"}
        headings = {"en": blog['title']}
        launch_url = url_for('project.show_blogpost',
                             short_name=project.short_name,
                             id=blogdata['id'],
                             _external=True)
        web_buttons = [{"id": "read-more-button",
                        "text": "Read more",
                        "icon": "http://i.imgur.com/MIxJp1L.png",
                        "url": launch_url }]

        mock_queue.assert_called_with(push_notification,
                                      project_id=project.id,
                                      contents=contents,
                                      headings=headings,
                                      web_buttons=web_buttons,
                                      launch_url=launch_url)

    @with_context
    @patch('pybossa.jobs.PybossaOneSignal.push_msg')
    def test_push_notification_method(self, mock_onesignal):
        """Test push_notification method alone."""
        project = ProjectFactory.create()
        mock_onesignal.return_value = "msg"

        contents = {"en": "New update!"}
        headings = {"en": 'title'}
        launch_url = 'https://hola.com'
        web_buttons = [{"id": "read-more-button",
                        "text": "Read more",
                        "icon": "http://i.imgur.com/MIxJp1L.png",
                        "url": launch_url}]

        with patch.dict(self.flask_app.config, {'ONESIGNAL_APP_ID': 'id',
                                                'ONESIGNAL_API_KEY': 'key'}):
            res = push_notification(project.id,
                                    contents=contents,
                                    headings=headings,
                                    web_buttons=web_buttons,
                                    launch_url=launch_url)

            assert mock_onesignal.called
            assert res == "msg", res
