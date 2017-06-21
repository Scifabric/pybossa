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
from default import Test, with_context
from pybossa.view.account import get_update_feed

from factories import ProjectFactory, TaskFactory, TaskRunFactory, UserFactory, BlogpostFactory

class TestActivityFeed(Test):

    def setUp(self):
        super(TestActivityFeed, self).setUp()


    @with_context
    def test_user_creation(self):
        """Test ACTIVITY FEED works for User creation."""
        user = UserFactory.create()
        update_feed = get_update_feed()
        err_msg = "It should be the same user"
        assert update_feed[0]['fullname'] == user.fullname, err_msg
        assert update_feed[0]['name'] == user.name, err_msg
        # assert update_feed[0].get('info') is not None, err_msg
        err_msg = "The update action should be User"
        assert update_feed[0]['action_updated'] == 'User', err_msg

    @with_context
    def test_project_creation(self):
        """Test ACTIVITY FEED works for project creation."""
        project = ProjectFactory.create()
        update_feed = get_update_feed()
        err_msg = "It should be the same project"
        assert update_feed[0]['id'] == project.id, err_msg
        assert update_feed[0]['name'] == project.name, err_msg
        assert update_feed[0]['short_name'] == project.short_name, err_msg
        # assert update_feed[0].get('info') is None, err_msg
        err_msg = "The update action should be Project"
        assert update_feed[0]['action_updated'] == 'Project', err_msg

    @with_context
    def test_blogpost_creation(self):
        """Test ACTIVITY FEED works for blog post creation."""
        blogpost = BlogpostFactory.create()
        update_feed = get_update_feed()
        err_msg = "It should be the blog post"
        assert update_feed[0]['id'] == blogpost.project_id, err_msg
        assert update_feed[0]['name'] == blogpost.project.name, err_msg
        assert update_feed[0]['short_name'] == blogpost.project.short_name, err_msg
        # assert update_feed[0].get('info') is not None, err_msg
        err_msg = "The update action should be Project"
        assert update_feed[0]['action_updated'] == 'Blog', err_msg

    @with_context
    def test_task_creation(self):
        """Test ACTIVITY FEED works for task creation."""
        task = TaskFactory.create()
        update_feed = get_update_feed()
        err_msg = "It should be the task"
        assert update_feed[0]['id'] == task.project_id, err_msg
        assert update_feed[0]['name'] == task.project.name, err_msg
        assert update_feed[0]['short_name'] == task.project.short_name, err_msg
        # assert update_feed[0].get('info') is not None, err_msg
        err_msg = "The update action should be Project"
        assert update_feed[0]['action_updated'] == 'Task', err_msg

    @with_context
    def test_taskrun_creation(self):
        """Test ACTIVITY FEED works for task_run creation."""
        task_run = TaskRunFactory.create()
        update_feed = get_update_feed()
        err_msg = "It should be the same task_run"
        assert update_feed[0]['name'] == task_run.user.name, err_msg
        assert update_feed[0]['fullname'] == task_run.user.fullname, err_msg
        assert update_feed[0]['project_name'] == task_run.project.name, err_msg
        assert update_feed[0]['project_short_name'] == task_run.project.short_name, err_msg
        # assert update_feed[0].get('info') is not None, err_msg
        err_msg = "The update action should be Project"
        assert update_feed[0]['action_updated'] == 'UserContribution', err_msg

    @with_context
    def test_taskrun_creation_state_completed(self):
        """Test ACTIVITY FEED works for task_run creation state completed."""
        task = TaskFactory.create(n_answers=1)
        task_run = TaskRunFactory.create(task=task)
        update_feed = get_update_feed()
        err_msg = "It should be the same task_run"
        assert update_feed[0]['id'] == task_run.project.id, err_msg
        assert update_feed[0]['name'] == task_run.project.name, err_msg
        assert update_feed[0]['short_name'] == task_run.project.short_name, err_msg
        # assert update_feed[0].get('info') is not None, err_msg
        err_msg = "The update action should be Project"
        assert update_feed[0]['action_updated'] == 'TaskCompleted', err_msg

    @with_context
    def test_max_limit(self):
        """Test ACTIVITY FEED limit works."""
        ProjectFactory.create_batch(101)

        update_feed = get_update_feed()
        err_msg = "There should be at max 100 updates."
        assert len(update_feed) == 100, err_msg
