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
from factories import TaskFactory, CategoryFactory
from pybossa.repositories import TaskRepository
from pybossa.exc import WrongObjectError, DBIntegrityError


class TestTaskRepositoryForTasks(Test):

    def setUp(self):
        super(TestTaskRepositoryForTasks, self).setUp()
        self.task_repo = TaskRepository(db)


    def test_get_return_none_if_no_task(self):
        """Test get_task method returns None if there is no task with the
        specified id"""

        task = self.task_repo.get_task(200)

        assert task is None, task


    def test_get_returns_task(self):
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

        tasks = TaskFactory.create_batch(3, state='done')

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


    def test_save(self):
        """Test save persist the task"""

        task = TaskFactory.build()
        assert self.task_repo.get_task(task.id) is None

        self.task_repo.save(task)

        assert self.task_repo.get_task(task.id) == task, "Task not saved"


    def test_save_fails_if_integrity_error(self):
        """Test save raises a DBIntegrityError if the instance to be saved lacks
        a required value"""

        task = TaskFactory.build(app_id=None, app=None)

        assert_raises(DBIntegrityError, self.task_repo.save, task)


    def test_save_only_saves_tasks(self):
        """Test save raises a WrongObjectError when an object which is not
        a Task instance is saved"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.task_repo.save, bad_object)


    def test_update(self):
        """Test update persists the changes made to the task"""

        task = TaskFactory.create(state='ongoing')
        task.state = 'done'

        self.task_repo.update(task)
        updated_task = self.task_repo.get_task(task.id)

        assert updated_task.state == 'done', updated_task


    def test_update_fails_if_integrity_error(self):
        """Test update raises a DBIntegrityError if the instance to be updated
        lacks a required value"""

        task = TaskFactory.create()
        task.app_id = None

        assert_raises(DBIntegrityError, self.task_repo.update, task)


    def test_update_only_updates_tasks(self):
        """Test update raises a WrongObjectError when an object which is not
        a Task instance is updated"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.task_repo.update, bad_object)


    def test_delete(self):
        """Test delete removes the task instance"""

        task = TaskFactory.create()

        self.task_repo.delete(task)
        deleted = self.task_repo.get_task(task.id)

        assert deleted is None, deleted


    def test_delete_only_deletes_tasks(self):
        """Test delete raises a WrongObjectError if is requested to delete other
        than a task"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.task_repo.delete, bad_object)


    def test_delete_all(self):
        """Test delete_all deletes many tasks at once"""

        tasks = TaskFactory.create_batch(2)

        self.task_repo.delete_all(tasks)

        for task in tasks:
            assert self.task_repo.get_task(task.id) is None, task


    def test_delete_all_raises_error_if_no_task(self):
        """Test delete_all raises a WrongObjectError if is requested to delete
        any other object than a task"""

        bad_objects = [dict(), 'string']

        assert_raises(WrongObjectError, self.task_repo.delete_all, bad_objects)

