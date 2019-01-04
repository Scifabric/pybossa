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
import io
from default import db, with_context
from test_api import TestAPI
from factories import AnnouncementFactory
from factories import UserFactory
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
        announcements = AnnouncementFactory.create_batch(9)
        announcement = AnnouncementFactory.create()

        # As anon
        url = '/api/announcement'
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert len(data) == 10, data

        # As user
        res = self.app_get_json(url + '?api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 10, data

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

    @with_context
    def test_announcement_post(self):
        """Test API Announcement creation."""
        admin, user = UserFactory.create_batch(2)

        payload = dict(title='hello', body='world')

        # As anon
        url = '/api/announcement'
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(str(res.data, 'utf-8'))
        assert res.status_code == 401, data
        assert data['status_code'] == 401, data

        # As a user
        url = '/api/announcement?api_key=%s' % user.api_key
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 403, data
        assert data['status_code'] == 403, data

        # As admin
        url = '/api/announcement?api_key=%s' % admin.api_key
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 200, data
        assert data['title'] == 'hello', data
        assert data['body'] == 'world', data


    @with_context
    def test_update_announcement(self):
        """Test API Announcement update post (PUT)."""
        admin, user = UserFactory.create_batch(2)
        announcement = AnnouncementFactory.create()

        # As anon
        announcement.title = 'new'
        announcement.body = 'new body'
        url = '/api/announcement/%s' % announcement.id
        res = self.app.put(url, data=json.dumps(announcement.dictize()))
        data = json.loads(res.data)
        assert res.status_code == 401, res.status_code

        # As user
        announcement.title = 'new'
        announcement.body = 'new body'
        url = '/api/announcement/%s?api_key=%s' % (announcement.id, user.api_key)
        data = announcement.dictize()
        del data['id']
        del data['created']
        del data['updated']
        del data['user_id']
        res = self.app.put(url, data=json.dumps(data))
        data = json.loads(res.data)
        assert res.status_code == 403, (res.status_code, res.data)

        # TODO: as project owner too?

        # As admin
        announcement.title = 'new'
        announcement.body = 'new body'
        url = '/api/announcement/%s?api_key=%s' % (announcement.id, admin.api_key)
        payload = announcement.dictize()
        del payload['user_id']
        del payload['created']
        del payload['updated']
        del payload['id']
        payload['published'] = True
        res = self.app.put(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 200, data
        assert data['title'] == 'new', data
        assert data['body'] == 'new body', data
        assert data['updated'] != data['created'], data
        assert data['published'] is True, data


    @with_context
    @patch('pybossa.api.api_base.uploader.delete_file')
    def test_delete_announcement(self, mock_delete):
        """Test API Announcement delete post (DEL)."""
        mock_delete.return_value = True
        admin = UserFactory.create()
        user = UserFactory.create()
        announcement = AnnouncementFactory.create()
        announcement2 = AnnouncementFactory.create()

        # As anon
        url = '/api/announcement/%s' % announcement.id
        res = self.app.delete(url)
        data = json.loads(res.data)
        assert res.status_code == 401, res.status_code

        # As user
        url = '/api/announcement/%s?api_key=%s' % (announcement.id, user.api_key)
        res = self.app.delete(url)
        assert res.status_code == 403, res.status_code

        # As admin
        url = '/api/announcement/%s?api_key=%s' % (announcement2.id, admin.api_key)
        res = self.app.delete(url)
        assert res.status_code == 204, res.status_code


    @with_context
    def test_announcement_post_file(self):
        """Test API Announcement file upload creation."""
        admin, user = UserFactory.create_batch(2)

        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(file=img, hello='1')

        # As anon
        url = '/api/announcement'
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 401, data
        assert data['status_code'] == 401, data

        # As admin
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(
                       file=img,
                       title='title',
                       body='body')

        url = '/api/announcement?api_key=%s' % admin.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 200, data
        container = "user_%s" % admin.id
        assert data['info']['container'] == container, data
        assert data['info']['file_name'] == 'test_file.jpg', data
        assert 'test_file.jpg' in data['media_url'], data

        # As normal user
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(file=img)

        url = '/api/announcement?api_key=%s' % user.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data


    @with_context
    def test_announcement_put_file(self):
        """Test API Announcement file upload update."""
        admin, user = UserFactory.create_batch(2)
        announcement = AnnouncementFactory.create()

        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(file=img)

        # As anon
        url = '/api/announcement/%s' % announcement.id
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 401, data
        assert data['status_code'] == 401, data

        # As a user
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(file=img)

        url = '/api/announcement/%s?api_key=%s' % (announcement.id, user.api_key)
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data
        assert data['status_code'] == 403, data

        # As admin
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(file=img)

        url = '/api/announcement/%s?api_key=%s' % (announcement.id,
                                                   admin.api_key)
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 200, data
        container = "user_%s" % admin.id
        assert data['info']['container'] == container, data
        assert data['info']['file_name'] == 'test_file.jpg', data
        assert 'test_file.jpg' in data['media_url'], data
