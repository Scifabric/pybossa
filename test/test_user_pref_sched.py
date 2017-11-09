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

from mock import patch
from helper import sched
from default import with_context
from pybossa.core import project_repo, task_repo, user_repo
from factories import TaskFactory, ProjectFactory, UserFactory
from pybossa.sched import get_user_pref_task, Schedulers
from pybossa.cache.helpers import n_available_tasks_for_user


class TestSched(sched.Helper):

    @with_context
    def test_no_pref(self):
        """
        User and task don't have preferences
        """
        owner = UserFactory.create(id=500)
        project = ProjectFactory.create(owner=owner)
        TaskFactory.create_batch(1, project=project, n_answers=10)
        tasks = get_user_pref_task(1, 500)
        assert tasks

    @with_context
    def test_task_no_pref(self):
        """
        User has preferences set, task doesn't
        """
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['en']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        TaskFactory.create_batch(1, project=project, n_answers=10)
        tasks = get_user_pref_task(1, 500)
        assert not tasks

    @with_context
    def test_no_user_pref(self):
        """
        Task has preferences set, user doesn't
        """
        owner = UserFactory.create(id=500)
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create_batch(1, project=project, n_answers=10)[0]
        task.user_pref = {'languages': ['en', 'de']}
        task_repo.save(task)
        tasks = get_user_pref_task(1, 500)
        assert not tasks

    @with_context
    def test_task_0(self):
        """
        Task has multiple preferences, user has single preference; match
        """
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['en']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create_batch(1, project=project, n_answers=10)[0]
        task.user_pref = {'languages': ['en', 'de']}
        task_repo.save(task)
        tasks = get_user_pref_task(1, 500)
        assert tasks

    @with_context
    def test_task_1(self):
        """
        Task has single preference, user has multiple preferences; match
        """
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['en', 'de']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create_batch(1, project=project, n_answers=10)[0]
        task.user_pref = {'languages': ['en']}
        task_repo.save(task)
        tasks = get_user_pref_task(1, 500)
        assert tasks

    @with_context
    def test_task_2(self):
        """
        Task has multiple preferences, user has multiple preferences; match
        """
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['en', 'de']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create_batch(1, project=project, n_answers=10)[0]
        task.user_pref = {'languages': ['en', 'es']}
        task_repo.save(task)
        tasks = get_user_pref_task(1, 500)
        assert tasks

    @with_context
    def test_task_3(self):
        """
        User has single preference, task has single preference, no match
        """
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['de']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create_batch(1, project=project, n_answers=10)[0]
        task.user_pref = {'languages': ['en']}
        task_repo.save(task)
        tasks = get_user_pref_task(1, 500)
        assert not tasks

    @with_context
    def test_task_4(self):
        """
        User has multiple preferences of different kinds,
        task has single preference, match
        """
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['de'], 'locations': ['us']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create_batch(1, project=project, n_answers=10)[0]
        task.user_pref = {'languages': ['de']}
        task_repo.save(task)
        tasks = get_user_pref_task(1, 500)
        assert tasks

    @with_context
    def test_task_5(self):
        """
        User has multiple preferences of different kinds,
        task has single preference, match
        """
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['de'], 'locations': ['us']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create_batch(1, project=project, n_answers=10)[0]
        task.user_pref = {'locations': ['us']}
        task_repo.save(task)
        tasks = get_user_pref_task(1, 500)
        assert tasks

    @with_context
    def test_task_6(self):
        """
        User has multiple preferences of different kinds,
        task has multiple preferences of different kinds, no match
        """
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['de'], 'locations': ['us']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create_batch(1, project=project, n_answers=10)[0]
        task.user_pref = {'languages': ['en', 'zh'], 'locations': ['es']}
        task_repo.save(task)
        tasks = get_user_pref_task(1, 500)
        assert not tasks

    @with_context
    def test_task_7(self):
        """
        Invalid user preference
        """
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': 'invalid_user_pref'}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create_batch(1, project=project, n_answers=10)[0]
        task.user_pref = {'languages': ['en', 'zh']}
        task_repo.save(task)
        tasks = get_user_pref_task(1, 500)
        assert not tasks


class TestNTaskAvailable(sched.Helper):

    @with_context
    def test_task_0(self):
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['de']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.user_pref
        task = TaskFactory.create_batch(1, project=project, n_answers=10)[0]
        task.user_pref = {'languages': ['en', 'zh']}
        task_repo.save(task)
        assert n_available_tasks_for_user(project, 500) == 0

    @with_context
    def test_task_1(self):
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['de']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.locked
        task = TaskFactory.create_batch(1, project=project, n_answers=10)[0]
        task.user_pref = {'languages': ['en', 'zh']}
        task_repo.save(task)
        assert n_available_tasks_for_user(project, 500) == 1

    @with_context
    def test_task_2(self):
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['de', 'en']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.user_pref
        task = TaskFactory.create_batch(1, project=project, n_answers=10)[0]
        task.user_pref = {'languages': ['en', 'zh']}
        task_repo.save(task)
        assert n_available_tasks_for_user(project, 500) == 1

    @with_context
    def test_task_3(self):
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['de', 'en']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.user_pref
        tasks = TaskFactory.create_batch(2, project=project, n_answers=10)
        tasks[0].user_pref = {'languages': ['en', 'zh']}
        task_repo.save(tasks[0])
        tasks[1].user_pref = {'languages': ['zh']}
        task_repo.save(tasks[0])
        assert n_available_tasks_for_user(project, 500) == 1

    @with_context
    def test_task_4(self):
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['de', 'en']}
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.user_pref
        tasks = TaskFactory.create_batch(2, project=project, n_answers=10)
        tasks[0].user_pref = {'languages': ['en', 'zh']}
        task_repo.save(tasks[0])
        tasks[1].user_pref = {'languages': ['de']}
        task_repo.save(tasks[0])
        assert n_available_tasks_for_user(project, 500) == 2

