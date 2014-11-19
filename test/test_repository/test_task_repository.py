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
# Cache global variables for timeouts

from default import Test, db
from nose.tools import assert_raises
from factories import TaskFactory, TaskRunFactory, AppFactory
from pybossa.repositories import TaskRepository
from pybossa.exc import WrongObjectError, DBIntegrityError


class TestTaskRepositoryForTaskQueries(Test):

    def setUp(self):
        super(TestTaskRepositoryForTaskQueries, self).setUp()
        self.task_repo = TaskRepository(db)


    def test_get_task_return_none_if_no_task(self):
        """Test get_task method returns None if there is no task with the
        specified id"""

        task = self.task_repo.get_task(200)

        assert task is None, task


    def test_get_task_returns_task(self):
        """Test get_task method returns a task if exists"""

        task = TaskFactory.create()

        retrieved_task = self.task_repo.get_task(task.id)

        assert task == retrieved_task, retrieved_task


    def test_get_task_by(self):
        """Test get_task_by returns a task with the specified attribute"""

        task = TaskFactory.create(state='done')

        retrieved_task = self.task_repo.get_task_by(state=task.state)

        assert task == retrieved_task, retrieved_task


    def test_get_task_by_returns_none_if_no_task(self):
        """Test get_task_by returns None if no task matches the query"""

        TaskFactory.create(state='done')

        task = self.task_repo.get_task_by(state='ongoing')

        assert task is None, task


    def test_filter_tasks_by_no_matches(self):
        """Test filter_tasks_by returns an empty list if no tasks match the query"""

        TaskFactory.create(state='done', n_answers=17)

        retrieved_tasks = self.task_repo.filter_tasks_by(state='ongoing')

        assert isinstance(retrieved_tasks, list)
        assert len(retrieved_tasks) == 0, retrieved_tasks


    def test_filter_tasks_by_one_condition(self):
        """Test filter_tasks_by returns a list of tasks that meet the filtering
        condition"""

        TaskFactory.create_batch(3, state='done')
        should_be_missing = TaskFactory.create(state='ongoing')

        retrieved_tasks = self.task_repo.filter_tasks_by(state='done')

        assert len(retrieved_tasks) == 3, retrieved_tasks
        assert should_be_missing not in retrieved_tasks, retrieved_tasks


    def test_filter_tasks_by_multiple_conditions(self):
        """Test filter_tasks_by supports multiple-condition queries"""

        TaskFactory.create(state='done', n_answers=17)
        task = TaskFactory.create(state='done', n_answers=99)

        retrieved_tasks = self.task_repo.filter_tasks_by(state='done',
                                                         n_answers=99)

        assert len(retrieved_tasks) == 1, retrieved_tasks
        assert task in retrieved_tasks, retrieved_tasks


    def test_filter_tasks_support_yield_option(self):
        """Test that filter_tasks_by with the yielded=True option returns the
        results in a generator fashion"""

        tasks = TaskFactory.create_batch(2, state='done')

        yielded_tasks = self.task_repo.filter_tasks_by(state='done', yielded=True)

        import types
        assert isinstance(yielded_tasks.__iter__(), types.GeneratorType)
        for task in yielded_tasks:
            assert task in tasks


    def test_count_tasks_with_no_matches(self):
        """Test count_tasks_with returns 0 if no tasks match the query"""

        TaskFactory.create(state='done', n_answers=17)

        count = self.task_repo.count_tasks_with(state='ongoing')

        assert count == 0, count


    def test_count_tasks_with_one_condition(self):
        """Test count_tasks_with returns the number of tasks that meet the
        filtering condition"""

        TaskFactory.create_batch(3, state='done')
        should_be_missing = TaskFactory.create(state='ongoing')

        count = self.task_repo.count_tasks_with(state='done')

        assert count == 3, count


    def test_count_tasks_with_multiple_conditions(self):
        """Test count_tasks_with supports multiple-condition queries"""

        TaskFactory.create(state='done', n_answers=17)
        task = TaskFactory.create(state='done', n_answers=99)

        count = self.task_repo.count_tasks_with(state='done',
                                                         n_answers=99)

        assert count == 1, count



class TestTaskRepositoryForTaskrunQueries(Test):

    def setUp(self):
        super(TestTaskRepositoryForTaskrunQueries, self).setUp()
        self.task_repo = TaskRepository(db)


    def test_get_task_run_return_none_if_no_task_run(self):
        """Test get_task_run method returns None if there is no taskrun with the
        specified id"""

        taskrun = self.task_repo.get_task_run(200)

        assert taskrun is None, taskrun


    def test_get_task_run_returns_task_run(self):
        """Test get_task_run method returns a taskrun if exists"""

        taskrun = TaskRunFactory.create()

        retrieved_taskrun = self.task_repo.get_task_run(taskrun.id)

        assert taskrun == retrieved_taskrun, retrieved_taskrun


    def test_get_task_run_by(self):
        """Test get_task_run_by returns a taskrun with the specified attribute"""

        taskrun = TaskRunFactory.create(info='info')

        retrieved_taskrun = self.task_repo.get_task_run_by(info=taskrun.info)

        assert taskrun == retrieved_taskrun, retrieved_taskrun


    def test_get_task_run_by_returns_none_if_no_task_run(self):
        """Test get_task_run_by returns None if no taskrun matches the query"""

        TaskRunFactory.create(info='info')

        taskrun = self.task_repo.get_task_run_by(info='other info')

        assert taskrun is None, taskrun


    def test_filter_task_runs_by_no_matches(self):
        """Test filter_task_runs_by returns an empty list if no taskruns match
        the query"""

        TaskRunFactory.create(info='info')

        retrieved_taskruns = self.task_repo.filter_task_runs_by(info='other')

        assert isinstance(retrieved_taskruns, list)
        assert len(retrieved_taskruns) == 0, retrieved_taskruns


    def test_filter_task_runs_by_one_condition(self):
        """Test filter_task_runs_by returns a list of taskruns that meet the
        filtering condition"""

        TaskRunFactory.create_batch(3, info='info')
        should_be_missing = TaskFactory.create(info='other info')

        retrieved_taskruns = self.task_repo.filter_task_runs_by(info='info')

        assert len(retrieved_taskruns) == 3, retrieved_taskruns
        assert should_be_missing not in retrieved_taskruns, retrieved_taskruns


    def test_filter_task_runs_by_multiple_conditions(self):
        """Test filter_task_runs_by supports multiple-condition queries"""

        TaskRunFactory.create(info='info', user_ip='8.8.8.8')
        taskrun = TaskRunFactory.create(info='info', user_ip='1.1.1.1')

        retrieved_taskruns = self.task_repo.filter_task_runs_by(info='info',
                                                                user_ip='1.1.1.1')

        assert len(retrieved_taskruns) == 1, retrieved_taskruns
        assert taskrun in retrieved_taskruns, retrieved_taskruns


    def test_filter_task_runs_support_yield_option(self):
        """Test that filter_task_runs_by with the yielded=True option returns
        the results in a generator fashion"""

        task_runs = TaskRunFactory.create_batch(2, info='info')

        yielded_task_runs = self.task_repo.filter_task_runs_by(info='info',
                                                               yielded=True)

        import types
        assert isinstance(yielded_task_runs.__iter__(), types.GeneratorType)
        for taskrun in yielded_task_runs:
            assert taskrun in task_runs


    def test_count_task_runs_with_no_matches(self):
        """Test count_task_runs_with returns 0 if no taskruns match the query"""

        TaskRunFactory.create(info='info')

        count = self.task_repo.count_task_runs_with(info='other info')

        assert count == 0, count


    def test_count_task_runs_with_one_condition(self):
        """Test count_task_runs_with returns the number of taskruns that meet the
        filtering condition"""

        TaskRunFactory.create_batch(3, info='info')
        should_be_missing = TaskRunFactory.create(info='other info')

        count = self.task_repo.count_task_runs_with(info='info')

        assert count == 3, count


    def test_count_task_runs_with_multiple_conditions(self):
        """Test count_task_runs_with supports multiple-condition queries"""

        TaskRunFactory.create(info='info', user_ip='8.8.8.8')
        taskrun = TaskRunFactory.create(info='info', user_ip='1.1.1.1')

        count = self.task_repo.count_task_runs_with(info='info',
                                                    user_ip='1.1.1.1')

        assert count == 1, count



class TestTaskRepositorySaveDeleteUpdate(Test):

    def setUp(self):
        super(TestTaskRepositorySaveDeleteUpdate, self).setUp()
        self.task_repo = TaskRepository(db)


    def test_save_saves_tasks(self):
        """Test save persists Task instances"""

        task = TaskFactory.build()
        assert self.task_repo.get_task(task.id) is None

        self.task_repo.save(task)

        assert self.task_repo.get_task(task.id) == task, "Task not saved"


    def test_save_saves_taskruns(self):
        """Test save persists TaskRun instances"""

        taskrun = TaskRunFactory.build()
        assert self.task_repo.get_task_run(taskrun.id) is None

        self.task_repo.save(taskrun)

        assert self.task_repo.get_task_run(taskrun.id) == taskrun, "TaskRun not saved"


    def test_save_fails_if_integrity_error(self):
        """Test save raises a DBIntegrityError if the instance to be saved lacks
        a required value"""

        task = TaskFactory.build(app_id=None, app=None)

        assert_raises(DBIntegrityError, self.task_repo.save, task)


    def test_save_only_saves_tasks_and_taskruns(self):
        """Test save raises a WrongObjectError when an object which is neither
        a Task nor a Taskrun instance is saved"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.task_repo.save, bad_object)


    def test_update_task(self):
        """Test update persists the changes made to Task instances"""

        task = TaskFactory.create(state='ongoing')
        task.state = 'done'

        self.task_repo.update(task)
        updated_task = self.task_repo.get_task(task.id)

        assert updated_task.state == 'done', updated_task


    def test_update_taskrun(self):
        """Test update persists the changes made to TaskRun instances"""

        taskrun = TaskRunFactory.create(info='info')
        taskrun.info = 'updated info!'

        self.task_repo.update(taskrun)
        updated_taskrun = self.task_repo.get_task_run(taskrun.id)

        assert updated_taskrun.info == 'updated info!', updated_taskrun


    def test_update_fails_if_integrity_error(self):
        """Test update raises a DBIntegrityError if the instance to be updated
        lacks a required value"""

        task = TaskFactory.create()
        task.app_id = None

        assert_raises(DBIntegrityError, self.task_repo.update, task)


    def test_update_only_updates_tasks_and_taskruns(self):
        """Test update raises a WrongObjectError when an object which is neither
        a Task nor a TaskRun instance is updated"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.task_repo.update, bad_object)


    def test_delete_task(self):
        """Test delete removes the Task instance"""

        task = TaskFactory.create()

        self.task_repo.delete(task)
        deleted = self.task_repo.get_task(task.id)

        assert deleted is None, deleted


    def test_delete_taskrun(self):
        """Test delete removes the TaskRun instance"""

        taskrun = TaskRunFactory.create()

        self.task_repo.delete(taskrun)
        deleted = self.task_repo.get_task_run(taskrun.id)

        assert deleted is None, deleted


    def test_delete_only_deletes_tasks(self):
        """Test delete raises a WrongObjectError if is requested to delete other
        than a task"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.task_repo.delete, bad_object)


    def test_delete_all_deletes_many_tasks(self):
        """Test delete_all deletes many tasks at once"""

        tasks = TaskFactory.create_batch(2)

        self.task_repo.delete_all(tasks)

        for task in tasks:
            assert self.task_repo.get_task(task.id) is None, task


    def test_delete_all_deletes_many_taskruns(self):
        """Test delete_all deletes many taskruns at once"""

        taskruns = TaskRunFactory.create_batch(2)

        self.task_repo.delete_all(taskruns)

        for taskrun in taskruns:
            assert self.task_repo.get_task_run(taskrun.id) is None, taskrun


    def test_delete_all_raises_error_if_no_task(self):
        """Test delete_all raises a WrongObjectError if is requested to delete
        any other object than a task"""

        bad_objects = [dict(), 'string']

        assert_raises(WrongObjectError, self.task_repo.delete_all, bad_objects)


    def test_update_tasks_redundancy_changes_all_project_tasks_redundancy(self):
        """Test update_tasks_redundancy updates the n_answers value for every
        task in the project"""

        project = AppFactory.create()
        TaskFactory.create_batch(2, app=project, n_answers=1)

        self.task_repo.update_tasks_redundancy(project, 2)
        tasks = self.task_repo.filter_tasks_by(app_id=project.id)

        for task in tasks:
            assert task.n_answers == 2, task.n_answers


    def test_update_tasks_redundancy_updates_state_when_incrementing(self):
        """Test update_tasks_redundancy changes 'completed' tasks to 'ongoing'
        if n_answers is incremented enough"""

        project = AppFactory.create()
        tasks = TaskFactory.create_batch(2, app=project, n_answers=2)
        TaskRunFactory.create_batch(2, task=tasks[0])
        tasks[0].state = 'completed'
        self.task_repo.update(tasks[0])

        assert tasks[0].state == 'completed', tasks[0].state
        assert tasks[1].state == 'ongoing', tasks[1].state

        self.task_repo.update_tasks_redundancy(project, 3)
        tasks = self.task_repo.filter_tasks_by(app_id=project.id)

        for task in tasks:
            assert task.state == 'ongoing', task.state


    def test_update_tasks_redundancy_updates_state_when_decrementing(self):
        """Test update_tasks_redundancy changes 'ongoing' tasks to 'completed'
        if n_answers is decremented enough"""

        project = AppFactory.create()
        tasks = TaskFactory.create_batch(2, app=project, n_answers=2)
        TaskRunFactory.create_batch(2, task=tasks[0])
        TaskRunFactory.create(task=tasks[1])
        tasks[0].state = 'completed'
        self.task_repo.update(tasks[0])

        assert tasks[0].state == 'completed', tasks[0].state
        assert tasks[1].state == 'ongoing', tasks[1].state

        self.task_repo.update_tasks_redundancy(project, 1)
        tasks = self.task_repo.filter_tasks_by(app_id=project.id)

        for task in tasks:
            assert task.state == 'completed', task.state
