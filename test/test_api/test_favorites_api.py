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
from nose.tools import assert_equal
from test_api import TestAPI

from factories import TaskFactory, UserFactory

from pybossa.repositories import TaskRepository

task_repo = TaskRepository(db)


class TestFavoritesAPI(TestAPI):

    url = '/api/favorites'

    @with_context
    def test_query_favorites_anon(self):
        """Test API Favorites works for anon."""
        user = UserFactory.create()
        TaskFactory.create(fav_user_ids=[user.id])
        res = self.app.get(self.url)
        data = json.loads(res.data)
        assert res.status_code == 401
        assert data['status_code'] == 401

    @with_context
    def test_query_get_favorites_auth(self):
        """Test API GET Favorites works for user."""
        user = UserFactory.create()
        user2 = UserFactory.create()
        tasks = TaskFactory.create_batch(30, fav_user_ids=[user.id])
        task = tasks[0]
        TaskFactory.create(fav_user_ids=[user2.id])
        res = self.app.get(self.url + '?api_key=%s' % user.api_key)
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert len(data) == 20, data
        data = data[0]
        assert data['id'] == task.id, (data, task)
        assert data['fav_user_ids'] == [user.id], data
        assert len(data['fav_user_ids']) == 1, data

        # limit
        res = self.app.get(self.url + '?limit=1&api_key=%s' % user.api_key)
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert len(data) == 1, len(data)
        assert data[0]['id'] == task.id, (data, task)
        assert data[0]['fav_user_ids'] == [user.id], data
        assert len(data[0]['fav_user_ids']) == 1, data

        # limit & offset
        res = self.app.get(self.url + '?limit=1&offset=1&api_key=%s' % user.api_key)
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert len(data) == 1, len(data)
        assert data[0]['fav_user_ids'] == [user.id], data
        assert len(data[0]['fav_user_ids']) == 1, data
        assert data[0]['id'] == tasks[1].id

        # last_id
        res = self.app.get(self.url + '?limit=1&last_id=%s&api_key=%s' %
                           (tasks[2].id, user.api_key))
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert len(data) == 1, len(data)
        assert data[0]['fav_user_ids'] == [user.id], data
        assert len(data[0]['fav_user_ids']) == 1, data
        assert data[0]['id'] == tasks[3].id, data[0]['id']

        # desc == true
        res = self.app.get(self.url + '?limit=1&desc=1&api_key=%s' % user.api_key)
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert len(data) == 1, len(data)
        assert data[0]['id'] == tasks[-1].id, data[0]['id']
        assert data[0]['fav_user_ids'] == [user.id], data
        assert len(data[0]['fav_user_ids']) == 1, data

        # orderby
        res = self.app.get(self.url + '?limit=1&orderby=created&api_key=%s' % user.api_key)
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert len(data) == 1, len(data)
        assert data[0]['id'] == tasks[0].id, data[0]['id']
        assert data[0]['fav_user_ids'] == [user.id], data
        assert len(data[0]['fav_user_ids']) == 1, data

        # orderby & desc
        res = self.app.get(self.url + '?limit=1&orderby=created&desc=1&api_key=%s' % user.api_key)
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert len(data) == 1, len(data)
        assert data[0]['id'] == tasks[-1].id, data[0]['id']
        assert data[0]['fav_user_ids'] == [user.id], data
        assert len(data[0]['fav_user_ids']) == 1, data



    @with_context
    def test_query_put_favorites_auth(self):
        """Test API PUT Favorites works for user."""
        user = UserFactory.create()
        user2 = UserFactory.create()
        TaskFactory.create(fav_user_ids=[user.id])
        TaskFactory.create(fav_user_ids=[user2.id])
        res = self.app.put(self.url + '/1?api_key=%s' % user.id)
        data = json.loads(res.data)
        assert res.status_code == 405, res.status_code
        assert data['status_code'] == 405, data

        res = self.app.put(self.url + '?api_key=%s' % user.id)
        assert res.status_code == 405, res.status_code

    @with_context
    def test_query_put_favorites_anon(self):
        """Test API PUT Favorites works for anon."""
        user = UserFactory.create()
        user2 = UserFactory.create()
        TaskFactory.create(fav_user_ids=[user.id])
        TaskFactory.create(fav_user_ids=[user2.id])
        res = self.app.put(self.url + '/1')
        data = json.loads(res.data)
        assert res.status_code == 405, res.status_code
        assert data['status_code'] == 405, data

        res = self.app.put(self.url)
        assert res.status_code == 405, res.status_code

    @with_context
    def test_query_post_favorites_auth(self):
        """Test API POST Favorites works for user."""
        user = UserFactory.create()
        user2 = UserFactory.create()
        task = TaskFactory.create()
        url = self.url + '?api_key=%s' % user.api_key
        res = self.app.post(url, data=json.dumps(dict(task_id=task.id)))
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert data['fav_user_ids'] == [user.id], data

        url = self.url + '?api_key=%s' % user2.api_key
        res = self.app.post(url, data=json.dumps(dict(task_id=task.id)))
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert user.id in data['fav_user_ids'], data
        assert user2.id in data['fav_user_ids'], data

        url = self.url + '?api_key=%s' % user2.api_key
        res = self.app.post(url, data=json.dumps(dict(task_id=4000000000)))
        data = json.loads(res.data)
        assert res.status_code == 404, res.status_code
        assert data['status_code'] == 404, data

        url = self.url + '?api_key=%s' % user2.api_key
        res = self.app.post(url, data=json.dumps(dict(task_id=task.id)))
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert user.id in data['fav_user_ids'], data
        assert user2.id in data['fav_user_ids'], data

    @with_context
    def test_query_post_wrong_datafavorites_auth(self):
        """Test API POST Favorites wrong data for user."""
        user = UserFactory.create()
        task = TaskFactory.create()
        url = self.url + '?api_key=%s' % user.api_key
        res = self.app.post(url, data=json.dumps(dict(task_id=task.id, id=3)))
        print((res.data))
        data = json.loads(res.data)
        assert res.status_code == 415, res.status_code
        assert data['status_code'] == 415, data


    @with_context
    def test_query_post_favorites_anon(self):
        """Test API POST Favorites works for anon."""
        res = self.app.post(self.url, data=json.dumps(dict(task_id=1)))
        data = json.loads(res.data)
        assert res.status_code == 401, res.status_code
        assert data['status_code'] == 401, res.status_code

    @with_context
    def test_query_delete_favorites_anon(self):
        """Test API DEL Favorites works for anon."""
        res = self.app.delete(self.url + '/1')
        data = json.loads(res.data)
        assert res.status_code == 401, res.status_code
        assert data['status_code'] == 401, res.status_code

        res = self.app.delete(self.url)
        assert res.status_code == 405, res.status_code

    @with_context
    def test_query_delete_favorites_auth(self):
        """Test API DEL Favorites works for user."""
        user = UserFactory.create()
        user2 = UserFactory.create()
        task = TaskFactory.create(fav_user_ids=[user.id, user2.id])

        url = self.url + '/%s?api_key=%s' % (task.id, user.api_key)
        res = self.app.delete(url)
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert user.id not in data['fav_user_ids'], data
        assert user2.id in data['fav_user_ids'], data

        url = self.url + '/%s?api_key=%s' % (task.id, user2.api_key)
        res = self.app.delete(url)
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert user.id not in data['fav_user_ids'], data
        assert user2.id not in data['fav_user_ids'], data

        url = self.url + '/%s?api_key=%s' % (task.id, user2.api_key)
        res = self.app.delete(url)
        data = json.loads(res.data)
        assert res.status_code == 404, res.status_code
