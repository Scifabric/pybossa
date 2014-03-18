# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.

import json

from base import Fixtures
from helper import web as web_helper
from pybossa.hateoas import Hateoas


class TestHateoas(web_helper.Helper):
    url = "/app/%s/tasks/export" % Fixtures.app_short_name

    hateoas = Hateoas()

    def setUp(self):
        super(TestHateoas, self).setUp()
        Fixtures.create()

    # Tests

    def test_00_link_object(self):
        """Test HATEOAS object link is created"""
        # For app
        res = self.app.get("/api/app/1", follow_redirects=True)
        output = json.loads(res.data)
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg

        err_msg = "There should be a Links list with the category URI"
        assert output['links'] is not None, err_msg
        assert len(output['links']) == 1, err_msg
        app_link = self.hateoas.link(rel='category', title='category',
                                     href='http://localhost/api/category/1')
        assert app_link == output['links'][0], err_msg

        app_link = self.hateoas.link(rel='self', title='app',
                                     href='http://localhost/api/app/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert app_link == output['link'], err_msg

        # For task
        res = self.app.get("/api/task/1", follow_redirects=True)
        output = json.loads(res.data)
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        task_link = self.hateoas.link(rel='self', title='task',
                                      href='http://localhost/api/task/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert task_link == output['link'], err_msg
        err_msg = "There should be one parent link: app"
        assert output.get('links') is not None, err_msg
        assert len(output.get('links')) == 1, err_msg
        err_msg = "The parent link is wrong"
        app_link = self.hateoas.link(rel='parent', title='app',
                                     href='http://localhost/api/app/1')
        assert output.get('links')[0] == app_link, err_msg

        # For taskrun
        res = self.app.get("/api/taskrun/1", follow_redirects=True)
        output = json.loads(res.data)
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        task_link = self.hateoas.link(rel='self', title='taskrun',
                                      href='http://localhost/api/taskrun/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert task_link == output['link'], err_msg
        err_msg = "There should be two parent links: app and task"
        assert output.get('links') is not None, err_msg
        assert len(output.get('links')) == 2, err_msg
        err_msg = "The parent app link is wrong"
        app_link = self.hateoas.link(rel='parent', title='app',
                                     href='http://localhost/api/app/1')
        assert output.get('links')[0] == app_link, err_msg

        err_msg = "The parent task link is wrong"
        app_link = self.hateoas.link(rel='parent', title='task',
                                     href='http://localhost/api/task/1')
        assert output.get('links')[1] == app_link, err_msg

        # For category
        res = self.app.get("/api/category/1", follow_redirects=True)
        output = json.loads(res.data)
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        category_link = self.hateoas.link(rel='self', title='category',
                                          href='http://localhost/api/category/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert category_link == output['link'], err_msg
        err_msg = "There should be no other links"
        assert output.get('links') is None, err_msg
        err_msg = "The object links should are wrong"

        # For user
        # Pending define what user fields will be visible through the API
        # Issue #626. For now let's suppose link and links are not visible
        # res = self.app.get("/api/user/1?api_key=" + Fixtures.root_api_key, follow_redirects=True)
        # output = json.loads(res.data)
        # err_msg = "There should be a Link with the object URI"
        # assert output['link'] is not None, err_msg
        # user_link = self.hateoas.link(rel='self', title='user',
        #                               href='http://localhost/api/user/1')
        # err_msg = "The object link ir wrong: %s" % output['link']
        # assert user_link == output['link'], err_msg
        # # when the links specification of a user will be set, modify the following
        # err_msg = "The list of links should be empty for now"
        # assert output.get('links') == None, err_msg


    def test_01_link_object(self):
        """Test HATEOAS object link is created"""
        # For app
        res = self.app.get("/api/app", follow_redirects=True)
        output = json.loads(res.data)[0]
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        app_link = self.hateoas.link(rel='self', title='app',
                                     href='http://localhost/api/app/1')

        err_msg = "The object link is wrong: %s" % output['link']
        assert app_link == output['link'], err_msg

        err_msg = "There should be a Links list with the category URI"
        assert output['links'] is not None, err_msg
        assert len(output['links']) == 1, err_msg
        app_link = self.hateoas.link(rel='category', title='category',
                                     href='http://localhost/api/category/1')
        assert app_link == output['links'][0], err_msg

        # For task
        res = self.app.get("/api/task", follow_redirects=True)
        output = json.loads(res.data)[0]
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        task_link = self.hateoas.link(rel='self', title='task',
                                      href='http://localhost/api/task/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert task_link == output['link'], err_msg
        err_msg = "There should be one parent link: app"
        assert output.get('links') is not None, err_msg
        assert len(output.get('links')) == 1, err_msg
        err_msg = "The parent link is wrong"
        app_link = self.hateoas.link(rel='parent', title='app',
                                     href='http://localhost/api/app/1')
        assert output.get('links')[0] == app_link, err_msg

        # For taskrun
        res = self.app.get("/api/taskrun", follow_redirects=True)
        output = json.loads(res.data)[0]
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        task_link = self.hateoas.link(rel='self', title='taskrun',
                                      href='http://localhost/api/taskrun/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert task_link == output['link'], err_msg
        err_msg = "There should be two parent links: app and task"
        assert output.get('links') is not None, err_msg
        assert len(output.get('links')) == 2, err_msg
        err_msg = "The parent app link is wrong"
        app_link = self.hateoas.link(rel='parent', title='app',
                                     href='http://localhost/api/app/1')
        assert output.get('links')[0] == app_link, err_msg

        err_msg = "The parent task link is wrong"
        app_link = self.hateoas.link(rel='parent', title='task',
                                     href='http://localhost/api/task/1')
        assert output.get('links')[1] == app_link, err_msg

        # For category
        res = self.app.get("/api/category", follow_redirects=True)
        output = json.loads(res.data)[0]
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        category_link = self.hateoas.link(rel='self', title='category',
                                      href='http://localhost/api/category/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert category_link == output['link'], err_msg
        err_msg = "There should be no other links"
        assert output.get('links') is None, err_msg
        err_msg = "The object links should are wrong"

        # For user
        # Pending define what user fields will be visible through the API
        # Issue #626. For now let's suppose link and links are not visible
        # res = self.app.get("/api/user?api_key=" + Fixtures.root_api_key, follow_redirects=True)
        # output = json.loads(res.data)[0]
        # err_msg = "There should be a Link with the object URI"
        # assert output['link'] is not None, err_msg
        # user_link = self.hateoas.link(rel='self', title='user',
        #                               href='http://localhost/api/user/1')
        # err_msg = "The object link ir wrong: %s" % output['link']
        # assert user_link == output['link'], err_msg
        # # when the links specification of a user will be set, modify the following
        # err_msg = "The list of links should be empty for now"
        # assert output.get('links') == None, err_msg
