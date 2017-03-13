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

from factories import UserFactory, BlogpostFactory, ProjectFactory

from pybossa.repositories import BlogRepository
blog_repo = BlogRepository(db)

class TestBlogpostAPI(TestAPI):

    @with_context
    def test_query_blogpost(self):
        """Test API query for blogpost endpoint works"""
        owner = UserFactory.create()
        user = UserFactory.create()
        project = ProjectFactory(owner=owner)
        blogposts = BlogpostFactory.create_batch(9)
        blogpost = BlogpostFactory.create(project=project)

        # As anon
        url = '/api/blogpost'
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 10, data
        assert data[9]['user_id'] == owner.id

        # As user
        res = self.app.get(url + '?api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # As owner
        res = self.app.get(url + '?api_key=' + owner.api_key)
        data = json.loads(res.data)
        assert len(data) == 1, data
        assert data[0]['user_id'] == owner.id

        # Valid field but wrong value
        res = self.app.get(url + "?title=wrongvalue")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get(url + '?title=' + blogpost.title  + '&body=' + blogpost.body)
        data = json.loads(res.data)
        # One result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['title'] == blogpost.title, data
        assert data[0]['body'] == blogpost.body, data

        # Limits
        res = self.app.get(url + "?limit=1")
        data = json.loads(res.data)
        for item in data:
            assert item['title'] == blogpost.title, item
        assert len(data) == 1, data

        # Keyset pagination
        res = self.app.get(url + '?limit=1&last_id=' + str(blogposts[8].id))
        data = json.loads(res.data)
        assert len(data) == 1, len(data)
        assert data[0]['id'] == blogpost.id



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
        url = "/api/blogpost?orderby=wrongattribute"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should be 415."
        assert data['status'] == 'failed', data
        assert data['status_code'] == 415, data
        assert 'has no attribute' in data['exception_msg'], data

        # Desc filter
        url = "/api/blogpost?orderby=id"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        blogposts.append(blogpost)
        blogposts_by_id = sorted(blogposts, key=lambda x: x.id, reverse=False)
        for i in range(len(blogposts)):
            assert blogposts_by_id[i].id == data[i]['id']

        # Desc filter
        url = "/api/blogpost?orderby=id&desc=true"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        blogposts_by_id = sorted(blogposts, key=lambda x: x.id, reverse=True)
        for i in range(len(blogposts)):
            assert blogposts_by_id[i].id == data[i]['id']

    @with_context
    def test_blogpost_post(self):
        """Test API Blogpost creation."""
        owner = UserFactory.create()
        user = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        project2 = ProjectFactory.create(owner=user)

        payload = dict(title='hello', body='world', project_id=None)

        # As anon
        url = '/api/blogpost'
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 401, data
        assert data['status_code'] == 401, data

        # As a user
        url = '/api/blogpost?api_key=%s' % user.api_key
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 415, data
        assert data['status_code'] == 415, data

        # As owner
        url = '/api/blogpost?api_key=%s' % owner.api_key
        payload['project_id'] = project.id
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 200, data
        assert data['title'] == 'hello', data
        assert data['body'] == 'world', data

        # As owner wrong 404 project_id
        url = '/api/blogpost?api_key=%s' % owner.api_key
        payload['project_id'] = -1
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # As owner using wrong project_id
        url = '/api/blogpost?api_key=%s' % owner.api_key
        payload['project_id'] = project2.id
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 403, data

        # As owner using wrong attribute
        url = '/api/blogpost?api_key=%s' % owner.api_key
        payload['project_id'] = project2.id
        payload['foo'] = 'bar'
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # As owner using reserved key 
        url = '/api/blogpost?api_key=%s' % owner.api_key
        payload['project_id'] = project.id
        payload['user_id'] = owner.id
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 400, data
        assert data['exception_msg'] == 'Reserved keys in payload', data

    @with_context
    def test_update_blogpost(self):
        """Test API Blogpost update post (PUT)."""
        user = UserFactory.create()
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        blogpost = BlogpostFactory.create(project=project)

        # As anon
        blogpost.title = 'new'
        blogpost.body = 'new body'
        url = '/api/blogpost/%s' % blogpost.id
        res = self.app.put(url, data=json.dumps(blogpost.dictize()))
        data = json.loads(res.data)
        assert res.status_code == 401, res.status_code

        # As user
        blogpost.title = 'new'
        blogpost.body = 'new body'
        url = '/api/blogpost/%s?api_key=%s' % (blogpost.id, user.api_key)
        res = self.app.put(url, data=json.dumps(blogpost.dictize()))
        data = json.loads(res.data)
        assert res.status_code == 403, res.status_code

        # As owner
        blogpost.title = 'new'
        blogpost.body = 'new body'
        url = '/api/blogpost/%s?api_key=%s' % (blogpost.id, owner.api_key)
        payload = blogpost.dictize()
        del payload['user_id']
        del payload['created']
        del payload['id']
        res = self.app.put(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert data['title'] == 'new', data
        assert data['body'] == 'new body', data

        # as owner with reserved key
        blogpost.title = 'new'
        blogpost.body = 'new body'
        url = '/api/blogpost/%s?api_key=%s' % (blogpost.id, owner.api_key)
        payload = blogpost.dictize()
        del payload['user_id']
        del payload['created']
        res = self.app.put(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 400, res.status_code
        assert data['exception_msg'] == 'Reserved keys in payload',  data


        # as owner with wrong key
        blogpost.title = 'new'
        blogpost.body = 'new body'
        url = '/api/blogpost/%s?api_key=%s' % (blogpost.id, owner.api_key)
        payload = blogpost.dictize()
        del payload['user_id']
        del payload['created']
        del payload['id']
        payload['foo'] = 'bar'
        res = self.app.put(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 415, res.status_code
        assert 'foo' in data['exception_msg'], data

    @with_context
    def test_delete_blogpost(self):
        """Test API Blogpost delete post (DEL)."""
        admin = UserFactory.create()
        owner = UserFactory.create()
        user = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        blogpost = BlogpostFactory.create(project=project)
        blogpost2 = BlogpostFactory.create(project=project)

        # As anon
        url = '/api/blogpost/%s' % blogpost.id
        res = self.app.delete(url)
        data = json.loads(res.data)
        assert res.status_code == 401, res.status_code

        # As user
        url = '/api/blogpost/%s?api_key=%s' % (blogpost.id, user.api_key)
        res = self.app.delete(url)
        assert res.status_code == 403, res.status_code

        # As owner
        url = '/api/blogpost/%s?api_key=%s' % (blogpost.id, owner.api_key)
        res = self.app.delete(url)
        assert res.status_code == 204, res.status_code

        # As admin
        url = '/api/blogpost/%s?api_key=%s' % (blogpost2.id, admin.api_key)
        res = self.app.delete(url)
        assert res.status_code == 204, res.status_code
