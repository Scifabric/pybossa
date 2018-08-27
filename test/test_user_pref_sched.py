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
from pybossa.jobs import send_email_notifications
from factories import TaskFactory, ProjectFactory, UserFactory, TaskRunFactory
from pybossa.sched import get_user_pref_task, Schedulers
from pybossa.cache.helpers import n_available_tasks_for_user
import datetime


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

    @with_context
    def test_get_unique_user_pref(self):
        """
        Test get_unique_user_preferences returns unique user preferences
        upon flattening input user preferences
        """

        from pybossa.util import get_unique_user_preferences

        user_prefs = [{'languages': ['en'], 'locations': ['us']}, {'languages': ['en', 'ru']}]
        duser_prefs = get_unique_user_preferences(user_prefs)
        err_msg = 'There should be 3 unique user_prefs after dropping 1 duplicate user_pref'
        assert len(duser_prefs) == 3, err_msg

        err_msg = 'user_pref mismatch; duplicate user_pref languages as en should be dropped'
        expected_user_pref = set(['\'{"languages": ["en"]}\'', '\'{"languages": ["ru"]}\'', '\'{"locations": ["us"]}\''])
        assert duser_prefs == expected_user_pref, err_msg

    @with_context
    def test_recent_contributors_list_as_per_user_pref(self):
        """
        Notify users about new tasks imported based on user preference and those who were not notified previously
        """
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['en']}         # owner is english user
        user_repo.save(owner)
        ch_user = UserFactory.create(id=501)
        ch_user.user_pref = {'languages': ['ch']}       # chinese language user
        user_repo.save(ch_user)
        ru_user = UserFactory.create(id=502)
        ru_user.user_pref = {'languages': ['ru']}       # russian language user
        user_repo.save(ru_user)

        # Stage 1 :
        # Create 4 tasks - 3 english, 1 chinese.
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.user_pref
        tasks = TaskFactory.create_batch(4, project=project, n_answers=1)
        tasks[0].user_pref = {'languages': ['en']}
        task_repo.save(tasks[0])
        tasks[1].user_pref = {'languages': ['en']}
        task_repo.save(tasks[1])
        tasks[2].user_pref = {'languages': ['ru']}
        task_repo.save(tasks[2])
        tasks[3].user_pref = {'languages': ['ch']}
        task_repo.save(tasks[3])

        # Complete 2 english and 1 russian tasks
        # completing 1 russian task will mark all russian tasks completed
        # and such users to be notified about new task imported
        taskrun1 = TaskRunFactory.create(task=tasks[0], user=owner)
        taskrun2 = TaskRunFactory.create(task=tasks[1], user=owner)
        taskrun3 = TaskRunFactory.create(task=tasks[2], user=ru_user)

        # Stage 2 :
        # create 3 more tasks; 2 russian and 1 chinese

        # at this stage, record current time.
        # chinese user has existing ongoing task, hence won't be notified
        # russian user has all tasks completed, hence will be notified
        now = datetime.datetime.utcnow().isoformat()

        tasks = TaskFactory.create_batch(3, project=project, n_answers=1)
        tasks[0].user_pref = {'languages': ['ru']}
        task_repo.save(tasks[0])
        tasks[1].user_pref = {'languages': ['ru']}
        task_repo.save(tasks[1])
        tasks[2].user_pref = {'languages': ['ch']}
        task_repo.save(tasks[2])

        recent_contributors = user_repo.get_user_pref_recent_contributor_emails(project.id, now)
        # with russian task completed, russian user will be notified about new task imported
        err_msg = 'There should be 1 contributors'
        assert len(recent_contributors) == 1, err_msg

        err_msg = 'only user3 that has language preference russian should be notified'
        assert recent_contributors[0] == 'user3@test.com', err_msg

    @with_context
    def test_recent_contributors_list_with_multiple_user_pref(self):
        """
        User with multiple user pref to be excluded from notifying when there are
        existing ongoing tasks matching any one of same user pref
        """
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['en']}                 # owner is english user
        user_repo.save(owner)
        sp_fr_user = UserFactory.create(id=501)
        sp_fr_user.user_pref = {'languages': ['sp', 'fr']}      # spanish french language user
        user_repo.save(sp_fr_user)
        ch_user = UserFactory.create(id=502)
        ch_user.user_pref = {'languages': ['ch']}               # russian language user
        user_repo.save(ch_user)

        # Stage 1 :
        # Create 4 tasks - 3 english, 1 chinese.
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.user_pref
        tasks = TaskFactory.create_batch(6, project=project, n_answers=1)
        tasks[0].user_pref = {'languages': ['en']}
        task_repo.save(tasks[0])
        tasks[1].user_pref = {'languages': ['sp']}
        task_repo.save(tasks[1])
        tasks[2].user_pref = {'languages': ['sp']}
        task_repo.save(tasks[2])
        tasks[3].user_pref = {'languages': ['fr']}
        task_repo.save(tasks[3])
        tasks[4].user_pref = {'languages': ['fr']}
        task_repo.save(tasks[4])
        tasks[5].user_pref = {'languages': ['ch']}
        task_repo.save(tasks[5])

        # Submit 1 english and chinese task runs. this will complete
        # such tasks and assoicated users to be notified about new task imported
        taskrun1 = TaskRunFactory.create(task=tasks[0], user=owner)
        taskrun2 = TaskRunFactory.create(task=tasks[5], user=ch_user)
        # Submit 1 spanish and 1 french task runs. since there are 1 each onging
        # tasks, assoicated users wont be notified about new task imported
        taskrun1 = TaskRunFactory.create(task=tasks[1], user=sp_fr_user)
        taskrun2 = TaskRunFactory.create(task=tasks[3], user=sp_fr_user)

        # Stage 2 :
        # create 3 more tasks; 1 spanish, 1 french and 1 chinese

        # at this stage, record current time.
        # spanish and french user has existing ongoing task, hence won't be notified
        # chinese and english user has all tasks completed, hence will be notified
        now = datetime.datetime.utcnow().isoformat()

        tasks = TaskFactory.create_batch(4, project=project, n_answers=1)
        tasks[0].user_pref = {'languages': ['en']}
        task_repo.save(tasks[0])
        tasks[1].user_pref = {'languages': ['sp']}
        task_repo.save(tasks[1])
        tasks[2].user_pref = {'languages': ['fr']}
        task_repo.save(tasks[2])
        tasks[3].user_pref = {'languages': ['ch']}
        task_repo.save(tasks[3])

        recent_contributors = user_repo.get_user_pref_recent_contributor_emails(project.id, now)
        # with english and chinese task completed, two such user will be notified about new task imported
        err_msg = 'There should be 2 contributors'
        assert len(recent_contributors) == 2, err_msg
        err_msg = 'user1 and user3 with english and chinese language preference should be notified'
        assert ('user1@test.com' in recent_contributors and
                'user3@test.com' in recent_contributors and
                'user2@test.com' not in recent_contributors), err_msg

    @with_context
    def test_recent_contributor_with_multiple_user_pref_notified(self):
        """
        User with multiple user pref to be notified when one of his/her
        user pref matches any new task user pref
        """
        owner = UserFactory.create(id=500)
        owner.user_pref = {'languages': ['en']}                 # owner is english user
        user_repo.save(owner)
        sp_fr_user = UserFactory.create(id=501)
        sp_fr_user.user_pref = {'languages': ['sp', 'fr']}      # spanish french language user
        user_repo.save(sp_fr_user)

        # Stage 1 :
        # Create 3 tasks - 1 english, 1 spanish, 1 french.
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.user_pref
        tasks = TaskFactory.create_batch(6, project=project, n_answers=1)
        tasks[0].user_pref = {'languages': ['en']}
        task_repo.save(tasks[0])
        tasks[1].user_pref = {'languages': ['sp']}
        task_repo.save(tasks[1])
        tasks[2].user_pref = {'languages': ['fr']}
        task_repo.save(tasks[2])

        # Submit 1 english and spanish tasks. this will complete
        # such tasks and assoicated users to be notified about new task imported
        taskrun1 = TaskRunFactory.create(task=tasks[0], user=owner)
        taskrun2 = TaskRunFactory.create(task=tasks[1], user=sp_fr_user)

        # Stage 2 :
        # create 1 spanish task
        # at this stage, record current time.
        # there is french ongoing task, but since spanish task is complete
        # sp_fr_user will be notified
        now = datetime.datetime.utcnow().isoformat()

        tasks = TaskFactory.create_batch(1, project=project, n_answers=1)
        tasks[0].user_pref = {'languages': ['sp']}
        task_repo.save(tasks[0])
        recent_contributors = user_repo.get_user_pref_recent_contributor_emails(project.id, now)
        # with one spanish task completed, user2 will be notified about new spanish task imported
        err_msg = 'There should be 1 contributors'
        assert len(recent_contributors) == 1, err_msg
        err_msg = 'user1 and user3 with english and chinese language preference should be notified'
        assert 'user2@test.com' in recent_contributors, err_msg

    @with_context
    @patch('pybossa.jobs.user_repo.get_user_pref_recent_contributor_emails')
    def test_no_email_notif(self, get_contrib_emails):
        """
        if the project is not configured, email notifications won't be sent
        """
        owner = UserFactory.create(id=500, user_pref={'languages': ['en']})

        project = ProjectFactory.create(owner=owner, email_notif=False)
        project.info['sched'] = Schedulers.user_pref
        project_repo.save(project)
        tasks = TaskFactory.create_batch(1, project=project, n_answers=1,
                                         user_pref={'languages': ['en']})

        TaskRunFactory.create(task=tasks[0], user=owner)

        TaskFactory.create_batch(1, project=project, n_answers=1,
                                 user_pref={'languages': ['en']})
        send_email_notifications()
        get_contrib_emails.assert_not_called()

    @with_context
    @patch('pybossa.jobs.user_repo.get_user_pref_recent_contributor_emails')
    def test_email_notif(self, get_contrib_emails):
        """
        if the project is configured, email notifications will be sent
        """
        owner = UserFactory.create(id=500, user_pref={'languages': ['en']})

        project = ProjectFactory.create(owner=owner, email_notif=True)
        project.info['sched'] = Schedulers.user_pref
        project_repo.save(project)
        tasks = TaskFactory.create_batch(1, project=project, n_answers=1,
                                         user_pref={'languages': ['en']})

        TaskRunFactory.create(task=tasks[0], user=owner)

        TaskFactory.create_batch(1, project=project, n_answers=1,
                                 user_pref={'languages': ['en']})
        send_email_notifications()
        get_contrib_emails.assert_called()


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


    @with_context
    def test_task_5(self):

        from pybossa import data_access

        owner = UserFactory.create(id=500)
        user = UserFactory.create(id=501, info=dict(data_access=["L1"]))
        patch_data_access_levels = dict(
            valid_access_levels=[("L1", "L1"), ("L2", "L2")],
            valid_user_levels_for_project_task_level=dict(L1=[], L2=["L1"]),
            valid_task_levels_for_user_level=dict(L1=["L2", "L3", "L4"], L2=["L3", "L4"]),
            valid_project_levels_for_task_level=dict(L1=["L1"], L2=["L1", "L2"]),
            valid_task_levels_for_project_level=dict(L1=["L1", "L2", "L3", "L4"], L2=["L2", "L3", "L4"])
        )

        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner, info=dict(project_users=[owner.id]))
        project.info['sched'] = Schedulers.user_pref
        tasks = TaskFactory.create_batch(3, project=project, n_answers=2, info=dict(data_access=["L1"]))
        tasks[0].info['data_access'] = ["L1"]
        task_repo.save(tasks[0])
        tasks[1].info['data_access'] = ["L1"]
        task_repo.save(tasks[1])
        tasks[2].info['data_access'] = ["L2"]
        task_repo.save(tasks[2])

        with patch.object(data_access, 'data_access_levels', patch_data_access_levels):
            assert n_available_tasks_for_user(project, 501) == 3
