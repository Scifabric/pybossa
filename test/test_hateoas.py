# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
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
from pybossa.hateoas import Hateoas
from factories import ProjectFactory, TaskRunFactory, TaskFactory


class TestHateoas(Test):

    hateoas = Hateoas()

    @with_context
    def setUp(self):
        super(TestHateoas, self).setUp()
        project = ProjectFactory.create(published=True, id=1)
        task = TaskFactory.create(id=1, project=project)
        TaskRunFactory.create(project=project, task=task)

    # Tests
    @with_context
    def test_00_link_object(self):
        """Test HATEOAS object link is created"""
        # For project
        res = self.app.get("/api/project/1", follow_redirects=True)
        output = json.loads(res.data)
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg

        err_msg = "There should be a Links list with the category URI"
        assert output['links'] is not None, err_msg
        assert len(output['links']) == 1, err_msg
        project_link = self.hateoas.link(rel='category', title='category',
                                     href='https://localhost/api/category/1')
        assert project_link == output['links'][0], err_msg

        project_link = self.hateoas.link(rel='self', title='project',
                                     href='https://localhost/api/project/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert project_link == output['link'], err_msg

        # For task
        res = self.app.get("/api/task/1", follow_redirects=True)
        output = json.loads(res.data)
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        task_link = self.hateoas.link(rel='self', title='task',
                                      href='https://localhost/api/task/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert task_link == output['link'], err_msg
        err_msg = "There should be one parent link: project"
        assert output.get('links') is not None, err_msg
        assert len(output.get('links')) == 1, err_msg
        err_msg = "The parent link is wrong"
        project_link = self.hateoas.link(rel='parent', title='project',
                                     href='https://localhost/api/project/1')
        assert output.get('links')[0] == project_link, err_msg

        # For taskrun
        res = self.app.get("/api/taskrun/1", follow_redirects=True)
        output = json.loads(res.data)
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        task_link = self.hateoas.link(rel='self', title='taskrun',
                                      href='https://localhost/api/taskrun/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert task_link == output['link'], err_msg
        err_msg = "There should be two parent links: project and task"
        assert output.get('links') is not None, err_msg
        assert len(output.get('links')) == 2, err_msg
        err_msg = "The parent project link is wrong"
        project_link = self.hateoas.link(rel='parent', title='project',
                                     href='https://localhost/api/project/1')
        assert output.get('links')[0] == project_link, err_msg

        err_msg = "The parent task link is wrong"
        project_link = self.hateoas.link(rel='parent', title='task',
                                     href='https://localhost/api/task/1')
        assert output.get('links')[1] == project_link, err_msg
        res = self.app.post("/api/taskrun")

        # For category
        res = self.app.get("/api/category/1", follow_redirects=True)
        output = json.loads(res.data)
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        category_link = self.hateoas.link(rel='self', title='category',
                                          href='https://localhost/api/category/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert category_link == output['link'], err_msg
        err_msg = "There should be no other links"
        assert output.get('links') is None, err_msg
        err_msg = "The object links should are wrong"

        # For user
        # Pending define what user fields will be visible through the API
        # Issue #626. For now let's suppose link and links are not visible
        # res = self.app.get("/api/user/1?api_key=" + self.root_api_key, follow_redirects=True)
        # output = json.loads(res.data)
        # err_msg = "There should be a Link with the object URI"
        # assert output['link'] is not None, err_msg
        # user_link = self.hateoas.link(rel='self', title='user',
        #                               href='https://localhost/api/user/1')
        # err_msg = "The object link ir wrong: %s" % output['link']
        # assert user_link == output['link'], err_msg
        # # when the links specification of a user will be set, modify the following
        # err_msg = "The list of links should be empty for now"
        # assert output.get('links') == None, err_msg


    @with_context
    def test_01_link_object(self):
        """Test HATEOAS object link is created"""
        # For project
        res = self.app.get("/api/project", follow_redirects=True)
        output = json.loads(res.data)[0]
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        project_link = self.hateoas.link(rel='self', title='project',
                                     href='https://localhost/api/project/1')

        err_msg = "The object link is wrong: %s" % output['link']
        assert project_link == output['link'], err_msg

        err_msg = "There should be a Links list with the category URI"
        assert output['links'] is not None, err_msg
        assert len(output['links']) == 1, err_msg
        project_link = self.hateoas.link(rel='category', title='category',
                                     href='https://localhost/api/category/1')
        assert project_link == output['links'][0], err_msg

        # For task
        res = self.app.get("/api/task", follow_redirects=True)
        output = json.loads(res.data)[0]
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        task_link = self.hateoas.link(rel='self', title='task',
                                      href='https://localhost/api/task/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert task_link == output['link'], err_msg
        err_msg = "There should be one parent link: project"
        assert output.get('links') is not None, err_msg
        assert len(output.get('links')) == 1, err_msg
        err_msg = "The parent link is wrong"
        project_link = self.hateoas.link(rel='parent', title='project',
                                     href='https://localhost/api/project/1')
        assert output.get('links')[0] == project_link, project_link

        # For taskrun
        res = self.app.get("/api/taskrun", follow_redirects=True)
        output = json.loads(res.data)[0]
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        task_link = self.hateoas.link(rel='self', title='taskrun',
                                      href='https://localhost/api/taskrun/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert task_link == output['link'], err_msg
        err_msg = "There should be two parent links: project and task"
        assert output.get('links') is not None, err_msg
        assert len(output.get('links')) == 2, err_msg
        err_msg = "The parent project link is wrong"
        project_link = self.hateoas.link(rel='parent', title='project',
                                     href='https://localhost/api/project/1')
        assert output.get('links')[0] == project_link, err_msg

        err_msg = "The parent task link is wrong"
        project_link = self.hateoas.link(rel='parent', title='task',
                                     href='https://localhost/api/task/1')
        assert output.get('links')[1] == project_link, err_msg

        # Check that hateoas removes all link and links from item
        without_links = self.hateoas.remove_links(output)
        err_msg = "There should not be any link or links keys"
        assert without_links.get('link') is None, err_msg
        assert without_links.get('links') is None, err_msg

        # For category
        res = self.app.get("/api/category", follow_redirects=True)
        output = json.loads(res.data)[0]
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        category_link = self.hateoas.link(rel='self', title='category',
                                      href='https://localhost/api/category/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert category_link == output['link'], err_msg
        err_msg = "There should be no other links"
        assert output.get('links') is None, err_msg
        err_msg = "The object links should are wrong"

        # For user
        # Pending define what user fields will be visible through the API
        # Issue #626. For now let's suppose link and links are not visible
        # res = self.app.get("/api/user?api_key=" + self.root_api_key, follow_redirects=True)
        # output = json.loads(res.data)[0]
        # err_msg = "There should be a Link with the object URI"
        # assert output['link'] is not None, err_msg
        # user_link = self.hateoas.link(rel='self', title='user',
        #                               href='https://localhost/api/user/1')
        # err_msg = "The object link ir wrong: %s" % output['link']
        # assert user_link == output['link'], err_msg
        # # when the links specification of a user will be set, modify the following
        # err_msg = "The list of links should be empty for now"
        # assert output.get('links') == None, err_msg
