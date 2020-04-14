# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2019 Scifabric LTD.
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
from default import Test, with_context
from helper.web import Helper
from factories import ProjectFactory, UserFactory
from mock import patch

class TestProjectContact(Helper):

    @with_context
    @patch('pybossa.view.projects.mail_queue.enqueue')
    def test_project_contact_success(self, enqueue):
        """Test Project Contact Success."""
        message = u'hello'

        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner, short_name='test-app', name='My New Project')

        # Obtain a CSRF key.
        csrf = self.get_csrf('/account/signin')

        # Make a request to the api.
        url = '/project/' + project.short_name + '/contact?api_key=' + user.api_key
        data = dict(message=message)
        res = self.app.post(url, headers={'X-CSRFToken': csrf}, content_type='application/json', data=json.dumps(data))

        # Verify status code from response.
        assert res.status_code == 200

        # Verify call to mail_queue.enqueue for sending the email.
        assert len(enqueue.call_args_list) == 1

        # Verify contents of email.
        str_message = str(enqueue.call_args_list[0])
        assert str_message.find('body') > -1
        assert str_message.find('Project Name: ' + project.name) > -1
        assert str_message.find('Project Short Name: ' + project.short_name) > -1
        assert str_message.find('Message: ' + message) > -1

        # Verify recipients.
        recipients_index = str_message.find('recipients')
        assert recipients_index > -1
        assert str_message.find(owner.email_addr) > recipients_index

        # Verify subject.
        subject_index = str_message.find('subject')
        assert subject_index > -1
        assert str_message.find(user.email_addr) > subject_index

        # Verify contents of response contains: { "success": True }
        data = json.loads(res.data)
        assert data.get('success') is True


    @with_context
    def test_project_contact_no_project(self):
        """Test Project Contact No Project."""
        admin, owner, user = UserFactory.create_batch(3)

        # Obtain a CSRF key.
        csrf = self.get_csrf('/account/signin')

        # Make a request to the api.
        url = '/project/invalid/contact?api_key=' + user.api_key
        data = dict(message=u'hello')
        res = self.app.post(url, headers={'X-CSRFToken': csrf}, content_type='application/json', data=json.dumps(data))

        # Verify status code from response.
        assert res.status_code == 404

    @with_context
    def test_project_contact_no_auth(self):
        """Test Project Contact No Auth."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner, short_name='test-app', name='My New Project')

        # Obtain a CSRF key.
        csrf = self.get_csrf('/account/signin')

        # Make a request to the api.
        url = '/project/' + project.short_name + '/contact?api_key=' + user.api_key
        res = self.app.get(url, headers={'X-CSRFToken': csrf})

        # Verify status code from response.
        assert res.status_code == 405
