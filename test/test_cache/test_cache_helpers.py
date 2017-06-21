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

from default import Test, db, with_context
from factories import (ProjectFactory, TaskFactory, TaskRunFactory,
                      AnonymousTaskRunFactory, UserFactory)
from pybossa.cache import helpers
from pybossa.cache.project_stats import update_stats


class TestHelpersCache(Test):

    @with_context
    def test_n_available_tasks_no_tasks_authenticated_user(self):
        """Test n_available_tasks returns 0 for authenticated user if the project
        has no tasks"""
        project = ProjectFactory.create()

        n_available_tasks = helpers.n_available_tasks(project.id, user_id=1)

        assert n_available_tasks == 0, n_available_tasks


    @with_context
    def test_n_available_tasks_no_tasks_anonymous_user(self):
        """Test n_available_tasks returns 0 for anonymous user if the project
        has no tasks"""
        project = ProjectFactory.create()

        n_available_tasks = helpers.n_available_tasks(project.id, user_ip='127.0.0.1')

        assert n_available_tasks == 0, n_available_tasks

    @with_context
    def test_n_available_tasks_no_taskruns_authenticated_user(self):
        """Test n_available_tasks returns 1 for authenticated user
        if there are no taskruns"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)

        n_available_tasks = helpers.n_available_tasks(project.id, user_id=1)

        assert n_available_tasks == 1, n_available_tasks

    @with_context
    def test_n_available_tasks_no_taskruns_anonymous_user(self):
        """Test n_available_tasks returns 1 for anonymous user
        if there are no taskruns"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)

        n_available_tasks = helpers.n_available_tasks(project.id, user_ip='127.0.0.1')

        assert n_available_tasks == 1, n_available_tasks

    @with_context
    def test_n_available_tasks_all_tasks_completed_authenticated_user(self):
        """Test n_available_tasks returns 0 for authenticated user if all the
        tasks are completed"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, state='completed')

        n_available_tasks = helpers.n_available_tasks(project.id, user_id=1)

        assert n_available_tasks == 0, n_available_tasks

    @with_context
    def test_n_available_tasks_all_tasks_completed_anonymous_user(self):
        """Test n_available_tasks returns 0 for anonymous user if all the
        tasks are completed"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, state='completed')

        n_available_tasks = helpers.n_available_tasks(project.id, user_ip='127.0.0.1')

        assert n_available_tasks == 0, n_available_tasks

    @with_context
    def test_n_available_tasks_all_tasks_answered_by_authenticated_user(self):
        """Test n_available_tasks returns 0 for authenticated user if he has
        submitted taskruns for all the tasks"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, n_answers=2)
        user = UserFactory.create()
        taskrun = TaskRunFactory.create(task=task, user=user)

        n_available_tasks = helpers.n_available_tasks(project.id, user_id=user.id)

        assert task.state != 'completed', task.state
        assert n_available_tasks == 0, n_available_tasks

    @with_context
    def test_n_available_tasks_all_tasks_answered_by_anonymous_user(self):
        """Test n_available_tasks returns 0 for anonymous user if he has
        submitted taskruns for all the tasks"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, n_answers=2)
        taskrun = AnonymousTaskRunFactory.create(task=task)

        n_available_tasks = helpers.n_available_tasks(project.id, user_ip=taskrun.user_ip)

        assert task.state != 'completed', task.state
        assert n_available_tasks == 0, n_available_tasks

    @with_context
    def test_n_available_tasks_some_tasks_answered_by_authenticated_user(self):
        """Test n_available_tasks returns 1 for authenticated user if he has
        submitted taskruns for one of the tasks but there is still another task"""
        project = ProjectFactory.create()
        answered_task = TaskFactory.create(project=project)
        available_task = TaskFactory.create(project=project)
        user = UserFactory.create()
        taskrun = TaskRunFactory.create(task=answered_task, user=user)

        n_available_tasks = helpers.n_available_tasks(project.id, user_id=user.id)
        assert n_available_tasks == 1, n_available_tasks

    @with_context
    def test_n_available_tasks_some_tasks_answered_by_anonymous_user(self):
        """Test n_available_tasks returns 1 for anonymous user if he has
        submitted taskruns for one of the tasks but there is still another task"""
        project = ProjectFactory.create()
        answered_task = TaskFactory.create(project=project)
        available_task = TaskFactory.create(project=project)
        taskrun = AnonymousTaskRunFactory.create(task=answered_task)

        n_available_tasks = helpers.n_available_tasks(project.id, user_ip=taskrun.user_ip)

        assert n_available_tasks == 1, n_available_tasks

    @with_context
    def test_n_available_tasks_some_task_answered_by_another_user(self):
        """Test n_available_tasks returns 1 for a user if another
        user has submitted taskruns for the task but he hasn't"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        user = UserFactory.create()
        taskrun = TaskRunFactory.create(task=task)

        n_available_tasks = helpers.n_available_tasks(project.id, user_id=user.id)
        assert n_available_tasks == 1, n_available_tasks

    @with_context
    def test_check_contributing_state_completed(self):
        """Test check_contributing_state returns 'completed' for a project with all
        tasks completed and user that has contributed to it"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, n_answers=1)
        user = UserFactory.create()
        TaskRunFactory.create_batch(1, task=task, user=user)

        update_stats(project.id)
        contributing_state = helpers.check_contributing_state(project=project,
                                                              user_id=user.id)

        assert task.state == 'completed', task.state
        assert contributing_state == 'completed', contributing_state

    @with_context
    def test_check_contributing_state_completed_user_not_contributed(self):
        """Test check_contributing_state returns 'completed' for a project with all
        tasks completed even if the user has not contributed to it"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, n_answers=2)
        TaskRunFactory.create_batch(2, task=task)
        user = UserFactory.create()
        update_stats(project.id)
        contributing_state = helpers.check_contributing_state(project=project,
                                                              user_id=user.id)

        assert task.state == 'completed', task.state
        assert contributing_state == 'completed', contributing_state

    @with_context
    def test_check_contributing_state_ongoing_tasks_not_contributed(self):
        """Test check_contributing_state returns 'can_contribute' for a project
        with ongoing tasks a user has not contributed to"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        user = UserFactory.create()

        contributing_state = helpers.check_contributing_state(project=project,
                                                              user_id=user.id)

        assert contributing_state == 'can_contribute', contributing_state

    @with_context
    def test_check_contributing_state_ongoing_tasks_contributed(self):
        """Test check_contributing_state returns 'cannot_contribute' for a project
        with ongoing tasks to which the user has already contributed"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, n_answers=3)
        user = UserFactory.create()
        TaskRunFactory.create(task=task, user=user)
        contributing_state = helpers.check_contributing_state(project=project,
                                                              user_id=user.id)

        assert contributing_state == 'cannot_contribute', contributing_state

    @with_context
    def test_check_contributing_state_draft(self):
        """Test check_contributing_state returns 'draft' for a project that has
        ongoing tasks but has no presenter"""
        project = ProjectFactory.create(published=False, info={})
        task = TaskFactory.create(project=project)
        user = UserFactory.create()

        contributing_state = helpers.check_contributing_state(project=project,
                                                              user_id=user.id)

        assert 'task_presenter' not in project.info
        assert contributing_state == 'draft', contributing_state

    @with_context
    def test_check_contributing_state_draft_presenter(self):
        """Test check_contributing_state returns 'draft' for a project that has
        no tasks but has a presenter"""
        project = ProjectFactory.create(published=False)
        user = UserFactory.create()

        contributing_state = helpers.check_contributing_state(project=project,
                                                              user_id=user.id)

        assert 'task_presenter' in project.info
        assert contributing_state == 'draft', contributing_state

    @with_context
    def test_check_contributing_state_publish(self):
        """Test check_contributing_state returns 'publish' for a project that is
        not published but is ready to be validated for publication (i.e. has both
        tasks and a task presenter"""
        project = ProjectFactory.create(published=False)
        task = TaskFactory.create(project=project)
        user = UserFactory.create()

        contributing_state = helpers.check_contributing_state(project=project,
                                                              user_id=user.id)

        assert contributing_state == 'publish', contributing_state
