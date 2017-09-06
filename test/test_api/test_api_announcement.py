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
from factories import AnnouncementFactory
from factories import UserFactory, HelpingMaterialFactory, ProjectFactory
from pybossa.repositories import AnnouncementRepository
from mock import patch
from nose.tools import assert_raises

announcement_repo = AnnouncementRepository(db)


class TestAnnouncementAPI(TestAPI):

    @with_context
    def test_query_announcement(self):
        """Test API query for announcement endpoint works"""
        owner = UserFactory.create()
        user = UserFactory.create()
        # project = ProjectFactory(owner=owner)
        announcements = AnnouncementFactory.create_batch(9)
        announcement = AnnouncementFactory.create()

        # As anon
        url = '/api/announcement'
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert len(data) == 10, data

        # # As user
        res = self.app_get_json(url + '?api_key=' + user.api_key)
        data = json.loads(res.data)
        # TODO: project_id is tried to load with api_key. Do not load it?
        assert data['exception_cls'] == 'AttributeError', data

        # # As owner
        res = self.app_get_json(url + '?api_key=' + owner.api_key)
        data = json.loads(res.data)
        # TODO: project_id is tried to load with api_key. Do not load it?
        assert data['exception_cls'] == 'AttributeError', data

        # Valid field but wrong value
        res = self.app.get(url + "?title=wrongvalue")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get(url + '?title=' + announcement.title  + '&body=' + announcement.body)
        data = json.loads(res.data)
        # One result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['title'] == announcement.title, data
        assert data[0]['body'] == announcement.body, data
        assert data[0]['media_url'] == announcement.media_url, data

        # Limits
        res = self.app.get(url + "?limit=1")
        data = json.loads(res.data)
        for item in data:
            assert item['title'] == announcement.title, item
        assert len(data) == 1, data

        # Keyset pagination
        res = self.app.get(url + '?limit=1&last_id=' + str(announcements[8].id))
        data = json.loads(res.data)
        assert len(data) == 1, len(data)
        assert data[0]['id'] == announcement.id

        # Errors
        res = self.app.get(url + "?something")
        err = json.loads(res.data)
        err_msg = "AttributeError exception should be raised"
        res.status_code == 415, err_msg
        assert res.status_code == 415, err_msg
        assert err['action'] == 'GET', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == 'AttributeError', err_msg

        # Desc filter
        url = "/api/announcement?orderby=wrongattribute"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should be 415."
        assert data['status'] == 'failed', data
        assert data['status_code'] == 415, data
        assert 'has no attribute' in data['exception_msg'], data

        # Desc filter
        url = "/api/announcement?orderby=id"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        announcements.append(announcement)
        announcements_by_id = sorted(announcements, key=lambda x: x.id, reverse=False)
        for i in range(len(announcements)):
            assert announcements_by_id[i].id == data[i]['id']

        # Desc filter
        url = "/api/announcement?orderby=id&desc=true"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        announcements_by_id = sorted(announcements, key=lambda x: x.id, reverse=True)
        for i in range(len(announcements)):
            assert announcements_by_id[i].id == data[i]['id']
