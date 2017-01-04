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

from pybossa.jobs import notify_blog_users
from default import Test, with_context, flask_app
from factories import BlogpostFactory
from factories import TaskRunFactory
from factories import ProjectFactory
from factories import UserFactory
from mock import patch, MagicMock

queue = MagicMock()
queue.enqueue.return_value = True


class TestNotifyBlogUsers(Test):


    @with_context
    @patch('pybossa.jobs.requests')
    def test_notify_blog_users_featured_project(self, mock):
        """Test Notify Blog users with featured project works."""
        user = UserFactory.create(subscribed=False)
        project = ProjectFactory.create(featured=True)
        TaskRunFactory.create(project=project)
        TaskRunFactory.create(project=project, user=user)
        blog = BlogpostFactory.create(project=project)
        res = notify_blog_users(blog.id, blog.project.id)
        msg = "1 users notified by email"
        assert res == msg, res

    @with_context
    @patch('pybossa.jobs.requests')
    @patch.dict(flask_app.config, {'PRO_FEATURES': {'notify_blog_updates': True}})
    def test_notify_blog_users_pro_owner_feature_only_for_pros(self, mock):
        """Test Notify Blog users with pro owner project works."""
        owner = UserFactory.create(pro=True)
        user = UserFactory.create(subscribed=False)
        project = ProjectFactory.create(owner=owner)
        TaskRunFactory.create(project=project)
        TaskRunFactory.create(project=project, user=user)
        blog = BlogpostFactory.create(project=project)
        res = notify_blog_users(blog.id, blog.project.id)
        msg = "1 users notified by email"
        assert res == msg, res

    @with_context
    @patch('pybossa.jobs.requests')
    @patch.dict(flask_app.config, {'PRO_FEATURES': {'notify_blog_updates': False}})
    def test_notify_blog_users_pro_owner_feature_for_everyone(self, mock):
        """Test Notify Blog users with pro owner project works for normal owners
        too if feature is for everyone"""
        owner = UserFactory.create(pro=False)
        user = UserFactory.create(subscribed=False)
        project = ProjectFactory.create(owner=owner)
        TaskRunFactory.create(project=project)
        TaskRunFactory.create(project=project, user=user)
        blog = BlogpostFactory.create(project=project)
        res = notify_blog_users(blog.id, blog.project.id)
        msg = "1 users notified by email"
        assert res == msg, res

    @with_context
    @patch('pybossa.jobs.requests')
    def test_notify_blog_users(self, mock):
        """Test Notify Blog users without pro or featured works."""
        owner = UserFactory.create(pro=False)
        user = UserFactory.create(subscribed=False)
        project = ProjectFactory.create(owner=owner, featured=False)
        TaskRunFactory.create(project=project)
        TaskRunFactory.create(project=project, user=user)
        blog = BlogpostFactory.create(project=project)
        res = notify_blog_users(blog.id, blog.project.id)
        msg = "0 users notified by email"
        assert res == msg, res
