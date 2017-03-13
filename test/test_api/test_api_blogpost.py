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
