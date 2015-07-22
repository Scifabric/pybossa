# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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

from pybossa.jobs import notify_blog_users
from default import Test, with_context
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
    def test_notify_blog_users(self, mock):
        """Test Notify Blog users works."""
        user = UserFactory.create(subscribed=False)
        project = ProjectFactory.create()
        TaskRunFactory.create(project=project)
        TaskRunFactory.create(project=project, user=user)
        blog = BlogpostFactory.create(project=project)
        res = notify_blog_users(blog.id, blog.project.id)
        msg = "1 users notified by email"
        assert res == msg, res
