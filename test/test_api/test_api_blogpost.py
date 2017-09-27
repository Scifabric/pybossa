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
from nose.tools import assert_equal
from test_api import TestAPI

from factories import UserFactory, BlogpostFactory, ProjectFactory

from pybossa.repositories import BlogRepository
from mock import patch
blog_repo = BlogRepository(db)

class TestBlogpostAPI(TestAPI):

    @with_context
    def test_blogpost_query_list_project_ids(self):
        """Get a list of blogposts using a list of project_ids."""
        projects = ProjectFactory.create_batch(3)
        blogposts = []
        for project in projects:
            tmp = BlogpostFactory.create_batch(2, project=project)
            for t in tmp:
                blogposts.append(t)

        project_ids = [project.id for project in projects]
        url = '/api/blogpost?project_id=%s&limit=100' % project_ids
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 3 * 2, len(data)
        for blog in data:
            assert blog['project_id'] in project_ids
        blogpost_project_ids = list(set([blog['project_id'] for blog in data]))
        assert sorted(project_ids) == sorted(blogpost_project_ids)

        # more filters
        res = self.app.get(url + '&orderby=created&desc=true')
        data = json.loads(res.data)
        assert data[0]['id'] == blogposts[-1].id


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
        assert data[0]['media_url'] == blogpost.media_url, data

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
        admin, owner, user = UserFactory.create_batch(3)
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

        # As admin
        url = '/api/blogpost?api_key=%s' % admin.api_key
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
        assert 'Reserved keys in payload' in data['exception_msg'], data

    @with_context
    def test_update_blogpost(self):
        """Test API Blogpost update post (PUT)."""
        admin, owner, user = UserFactory.create_batch(3)
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
        data = blogpost.dictize()
        del data['id']
        del data['created']
        del data['updated']
        del data['user_id']
        res = self.app.put(url, data=json.dumps(data))
        data = json.loads(res.data)
        assert res.status_code == 403, (res.status_code, res.data)

        # As owner
        blogpost.title = 'new'
        blogpost.body = 'new body'
        url = '/api/blogpost/%s?api_key=%s' % (blogpost.id, owner.api_key)
        payload = blogpost.dictize()
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

        # As admin
        blogpost.title = 'new'
        blogpost.body = 'new body'
        url = '/api/blogpost/%s?api_key=%s' % (blogpost.id, admin.api_key)
        payload = blogpost.dictize()
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
        assert 'Reserved keys in payload' in data['exception_msg'] ,  data


        # as owner with wrong key
        blogpost.title = 'new'
        blogpost.body = 'new body'
        url = '/api/blogpost/%s?api_key=%s' % (blogpost.id, owner.api_key)
        payload = blogpost.dictize()
        del payload['user_id']
        del payload['created']
        del payload['updated']
        del payload['id']
        payload['foo'] = 'bar'
        res = self.app.put(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 415, data
        assert 'foo' in data['exception_msg'], data

    @with_context
    @patch('pybossa.api.api_base.uploader.delete_file')
    def test_delete_blogpost(self, mock_delete):
        """Test API Blogpost delete post (DEL)."""
        mock_delete.return_value = True
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
        assert mock_delete.called_with(blogpost.info['file_name'],
                                       blogpost.info['container'])

        # As admin
        url = '/api/blogpost/%s?api_key=%s' % (blogpost2.id, admin.api_key)
        res = self.app.delete(url)
        assert res.status_code == 204, res.status_code

    @with_context
    def test_blogpost_post_file(self):
        """Test API Blogpost file upload creation."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        project2 = ProjectFactory.create(owner=user)

        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        # As anon
        url = '/api/blogpost'
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 401, data
        assert data['status_code'] == 401, data

        # As a user
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/blogpost?api_key=%s' % user.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data
        assert data['status_code'] == 403, data

        # As owner
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img,
                       title='title',
                       body='body')

        url = '/api/blogpost?api_key=%s' % project.owner.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 200, data
        container = "user_%s" % owner.id
        assert data['info']['container'] == container, data
        assert data['info']['file_name'] == 'test_file.jpg', data
        assert 'test_file.jpg' in data['media_url'], data

        # As admin
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img,
                       title='title',
                       body='body')

        url = '/api/blogpost?api_key=%s' % admin.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 200, data
        container = "user_%s" % owner.id
        assert data['info']['container'] == container, data
        assert data['info']['file_name'] == 'test_file.jpg', data
        assert 'test_file.jpg' in data['media_url'], data

        # As owner wrong 404 project_id
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/blogpost?api_key=%s' % owner.api_key
        payload['project_id'] = -1
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # As owner using wrong project_id
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/blogpost?api_key=%s' % owner.api_key
        payload['project_id'] = project2.id
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data

        # As owner using wrong attribute
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       wrong=img)

        url = '/api/blogpost?api_key=%s' % owner.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # As owner using reserved key 
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/blogpost?api_key=%s' % owner.api_key
        payload['project_id'] = project.id
        payload['id'] = 3
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 400, data
        assert 'Reserved keys in payload' in data['exception_msg'], data

    @with_context
    def test_blogpost_put_file(self):
        """Test API Blogpost file upload update."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        project2 = ProjectFactory.create(owner=user)
        blogpost = BlogpostFactory.create(project=project)

        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        # As anon
        url = '/api/blogpost/%s' % blogpost.id
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 401, data
        assert data['status_code'] == 401, data

        # As a user
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/blogpost/%s?api_key=%s' % (blogpost.id, user.api_key)
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data
        assert data['status_code'] == 403, data

        # As owner
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/blogpost/%s?api_key=%s' % (blogpost.id,
                                               project.owner.api_key)
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 200, data
        container = "user_%s" % owner.id
        assert data['info']['container'] == container, data
        assert data['info']['file_name'] == 'test_file.jpg', data
        assert 'test_file.jpg' in data['media_url'], data

        # As admin
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/blogpost/%s?api_key=%s' % (blogpost.id,
                                               admin.api_key)
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 200, data
        container = "user_%s" % owner.id
        assert data['info']['container'] == container, data
        assert data['info']['file_name'] == 'test_file.jpg', data
        assert 'test_file.jpg' in data['media_url'], data


        # As owner wrong 404 project_id
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/blogpost?api_key=%s' % owner.api_key
        payload['project_id'] = -1
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # As owner using wrong project_id
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/blogpost?api_key=%s' % owner.api_key
        payload['project_id'] = project2.id
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data

        # As owner using wrong attribute
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       wrong=img)

        url = '/api/blogpost?api_key=%s' % owner.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # As owner using reserved key
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/blogpost?api_key=%s' % owner.api_key
        payload['project_id'] = project.id
        payload['id'] = 3
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 400, data
        assert 'Reserved keys in payload' in data['exception_msg'] , data
