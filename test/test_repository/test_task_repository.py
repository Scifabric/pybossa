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
# Cache global variables for timeouts

from default import Test, db, with_context
from nose.tools import assert_raises
from factories import TaskFactory, TaskRunFactory, ProjectFactory
from pybossa.repositories import TaskRepository, ProjectRepository
from pybossa.exc import WrongObjectError, DBIntegrityError
from pybossa.model.task import Task

project_repo = ProjectRepository(db)


class TestTaskRepositoryForTaskQueries(Test):

    def setUp(self):
        super(TestTaskRepositoryForTaskQueries, self).setUp()
        self.task_repo = TaskRepository(db)


    @with_context
    def test_orderby(self):
        """Test orderby."""
        project = ProjectFactory.create()
        task1 = TaskFactory.create(fav_user_ids=[1], project=project)
        task2 = TaskFactory.create(fav_user_ids=None, project=project)
        task3 = TaskFactory.create(fav_user_ids=[1, 2, 3], project=project)

        task = self.task_repo.filter_tasks_by(orderby='id', desc=True,
                                              project_id=project.id, limit=1)[0]
        assert task == task3, (task, task3)

        task = self.task_repo.filter_tasks_by(orderby='id', desc=False,
                                              project_id=project.id, limit=1)[0]
        assert task == task1, (task, task1)


        task = self.task_repo.filter_tasks_by(orderby='created', desc=True,
                                              project_id=project.id)[0]
        assert task == task3, (task.id, task3.id)

        task = self.task_repo.filter_tasks_by(orderby='created', desc=False,
                                              project_id=project.id)[0]
        assert task == task1, (task.created, task1.created)

        task = self.task_repo.filter_tasks_by(orderby='fav_user_ids', desc=True,
                                              project_id=project.id)[0][0]
        assert task == task3, (task.id, task3.id)

        task = self.task_repo.filter_tasks_by(orderby='fav_user_ids', desc=False,
                                              project_id=project.id)[0][0]
        assert task == task2, (task.fav_user_ids, task2.fav_user_ids)

    @with_context
    def test_handle_info_json_plain_text(self):
        """Test handle info in JSON as plain text works."""
        TaskFactory.create(info='answer')
        res = self.task_repo.filter_tasks_by(info='answer')
        assert len(res) == 1
        assert res[0].info == 'answer', res[0]

    @with_context
    def test_handle_info_json_integer(self):
        """Test handle info in JSON as integer text works."""
        TaskFactory.create(info=95)
        res = self.task_repo.filter_tasks_by(info='"95"')
        assert len(res) == 1
        assert res[0].info == 95, res[0]

    @with_context
    def test_handle_info_json_float(self):
        """Test handle info in JSON as floattext works."""
        TaskFactory.create(info='9.5')
        res = self.task_repo.filter_tasks_by(info='9.5')
        assert len(res) == 1
        assert res[0].info == '9.5', res[0]

    @with_context
    def test_handle_info_json(self):
        """Test handle info in JSON works."""
        TaskFactory.create(info={'foo': 'bar'})
        info = 'foo::bar'
        res = self.task_repo.filter_tasks_by(info=info)
        assert len(res) == 1
        assert res[0].info['foo'] == 'bar', res[0]

    @with_context
    def test_handle_info_json_fulltextsearch(self):
        """Test handle info fulltextsearch in JSON works."""
        text = 'bar word agent something'
        TaskFactory.create(info={'foo': text})
        info = 'foo::agent'
        res = self.task_repo.filter_tasks_by(info=info, fulltextsearch='1')
        assert len(res) == 1
        assert res[0][0].info['foo'] == text, res[0]

        res = self.task_repo.filter_tasks_by(info=info)
        assert len(res) == 0, len(res)


    @with_context
    def test_handle_info_json_multiple_keys(self):
        """Test handle info in JSON with multiple keys works."""
        TaskFactory.create(info={'foo': 'bar', 'bar': 'foo'})
        info = 'foo::bar|bar::foo'
        res = self.task_repo.filter_tasks_by(info=info)
        assert len(res) == 1
        assert res[0].info['foo'] == 'bar', res[0]
        assert res[0].info['bar'] == 'foo', res[0]

    @with_context
    def test_handle_info_json_multiple_keys_fulltextsearch(self):
        """Test handle info in JSON with multiple keys works."""
        text = "two three four five"
        TaskFactory.create(info={'foo': 'bar', 'extra': text})
        info = 'foo::bar|extra::four'
        res = self.task_repo.filter_tasks_by(info=info, fulltextsearch='1')
        assert len(res) == 1, len(res)
        assert res[0][0].info['foo'] == 'bar', res[0]
        assert res[0][0].info['extra'] == text, res[0]

        res = self.task_repo.filter_tasks_by(info=info)
        assert len(res) == 0, len(res)

    @with_context
    def test_handle_info_json_multiple_keys_and_fulltextsearch(self):
        """Test handle info in JSON with multiple keys and AND operator works."""
        text = "agent myself you bar"
        TaskFactory.create(info={'foo': 'bar', 'bar': text})

        info = 'foo::bar|bar::you&agent'
        res = self.task_repo.filter_tasks_by(info=info, fulltextsearch='1')
        assert len(res) == 1, len(res)
        assert res[0][0].info['foo'] == 'bar', res[0]
        assert res[0][0].info['bar'] == text, res[0]


    @with_context
    def test_handle_info_json_multiple_keys_404(self):
        """Test handle info in JSON with multiple keys not found works."""
        TaskFactory.create(info={'foo': 'bar', 'daniel': 'foo'})
        info = 'foo::bar|bar::foo'
        res = self.task_repo.filter_tasks_by(info=info)
        assert len(res) == 0

    @with_context
    def test_handle_info_json_multiple_keys_404_with_one_pipe(self):
        """Test handle info in JSON with multiple keys not found works."""
        TaskFactory.create(info={'foo': 'bar', 'bar': 'foo'})
        info = 'foo::bar|'
        res = self.task_repo.filter_tasks_by(info=info)
        assert len(res) == 1
        assert res[0].info['foo'] == 'bar', res[0]
        assert res[0].info['bar'] == 'foo', res[0]

    @with_context
    def test_handle_info_json_multiple_keys_404_fulltextsearch(self):
        """Test handle info in JSON with full text
        search with multiple keys not found works."""
        TaskFactory.create(info={'foo': 'bar', 'bar': 'foo'})
        info = 'foo::bar|'
        res = self.task_repo.filter_tasks_by(info=info, fulltextsearch='1')
        assert len(res) == 1
        assert res[0][0].info['foo'] == 'bar', res[0]
        assert res[0][0].info['bar'] == 'foo', res[0]


    @with_context
    def test_handle_info_json_wrong_data(self):
        """Test handle info in JSON with wrong data works."""
        TaskFactory.create(info={'foo': 'bar', 'bar': 'foo'})

        infos = ['|', '||', '|::', ':|', '::|', '|:', 'foo|', 'foo|']
        for info in infos:
            res = self.task_repo.filter_tasks_by(info=info)
            assert len(res) == 0

        for info in infos:
            res = self.task_repo.filter_tasks_by(info=info, fulltextsearch='1')
            assert len(res) == 0

    @with_context
    def test_get_task_return_none_if_no_task(self):
        """Test get_task method returns None if there is no task with the
        specified id"""

        task = self.task_repo.get_task(200)

        assert task is None, task


    @with_context
    def test_get_task_returns_task(self):
        """Test get_task method returns a task if exists"""

        task = TaskFactory.create()

        retrieved_task = self.task_repo.get_task(task.id)

        assert task == retrieved_task, retrieved_task


    @with_context
    def test_get_task_by(self):
        """Test get_task_by returns a task with the specified attribute"""

        task = TaskFactory.create(state='done')

        retrieved_task = self.task_repo.get_task_by(state=task.state)

        assert task == retrieved_task, retrieved_task


    @with_context
    def test_get_task_by_returns_none_if_no_task(self):
        """Test get_task_by returns None if no task matches the query"""

        TaskFactory.create(state='done')

        task = self.task_repo.get_task_by(state='ongoing')

        assert task is None, task


    @with_context
    def test_filter_tasks_by_no_matches(self):
        """Test filter_tasks_by returns an empty list if no tasks match the query"""

        TaskFactory.create(state='done', n_answers=17)

        retrieved_tasks = self.task_repo.filter_tasks_by(state='ongoing')

        assert isinstance(retrieved_tasks, list)
        assert len(retrieved_tasks) == 0, retrieved_tasks


    @with_context
    def test_filter_tasks_by_one_condition(self):
        """Test filter_tasks_by returns a list of tasks that meet the filtering
        condition"""

        TaskFactory.create_batch(3, state='done')
        should_be_missing = TaskFactory.create(state='ongoing')

        retrieved_tasks = self.task_repo.filter_tasks_by(state='done')

        assert len(retrieved_tasks) == 3, retrieved_tasks
        assert should_be_missing not in retrieved_tasks, retrieved_tasks


    @with_context
    def test_filter_tasks_by_multiple_conditions(self):
        """Test filter_tasks_by supports multiple-condition queries"""

        TaskFactory.create(state='done', n_answers=17)
        task = TaskFactory.create(state='done', n_answers=99)

        retrieved_tasks = self.task_repo.filter_tasks_by(state='done',
                                                         n_answers=99)

        assert len(retrieved_tasks) == 1, retrieved_tasks
        assert task in retrieved_tasks, retrieved_tasks


    @with_context
    def test_filter_tasks_support_yield_option(self):
        """Test that filter_tasks_by with the yielded=True option returns the
        results as a generator"""

        tasks = TaskFactory.create_batch(2, state='done')

        yielded_tasks = self.task_repo.filter_tasks_by(state='done', yielded=True)

        import types
        assert isinstance(yielded_tasks.__iter__(), types.GeneratorType)
        for task in yielded_tasks:
            assert task in tasks


    @with_context
    def test_filter_tasks_limit_offset(self):
        """Test that filter_tasks_by supports limit and offset options"""

        TaskFactory.create_batch(4)
        all_tasks = self.task_repo.filter_tasks_by()

        first_two = self.task_repo.filter_tasks_by(limit=2)
        last_two = self.task_repo.filter_tasks_by(limit=2, offset=2)

        assert len(first_two) == 2, first_two
        assert len(last_two) == 2, last_two
        assert first_two == all_tasks[:2]
        assert last_two == all_tasks[2:]


    @with_context
    def test_count_tasks_with_no_matches(self):
        """Test count_tasks_with returns 0 if no tasks match the query"""

        TaskFactory.create(state='done', n_answers=17)

        count = self.task_repo.count_tasks_with(state='ongoing')

        assert count == 0, count


    @with_context
    def test_count_tasks_with_one_condition(self):
        """Test count_tasks_with returns the number of tasks that meet the
        filtering condition"""

        TaskFactory.create_batch(3, state='done')
        should_be_missing = TaskFactory.create(state='ongoing')

        count = self.task_repo.count_tasks_with(state='done')

        assert count == 3, count


    @with_context
    def test_count_tasks_with_multiple_conditions(self):
        """Test count_tasks_with supports multiple-condition queries"""

        TaskFactory.create(state='done', n_answers=17)
        task = TaskFactory.create(state='done', n_answers=99)

        count = self.task_repo.count_tasks_with(state='done', n_answers=99)

        assert count == 1, count



class TestTaskRepositoryForTaskrunQueries(Test):

    def setUp(self):
        super(TestTaskRepositoryForTaskrunQueries, self).setUp()
        self.task_repo = TaskRepository(db)


    @with_context
    def test_get_task_run_return_none_if_no_task_run(self):
        """Test get_task_run method returns None if there is no taskrun with the
        specified id"""

        taskrun = self.task_repo.get_task_run(200)

        assert taskrun is None, taskrun


    @with_context
    def test_get_task_run_returns_task_run(self):
        """Test get_task_run method returns a taskrun if exists"""

        taskrun = TaskRunFactory.create()

        retrieved_taskrun = self.task_repo.get_task_run(taskrun.id)

        assert taskrun == retrieved_taskrun, retrieved_taskrun


    @with_context
    def test_get_task_run_by(self):
        """Test get_task_run_by returns a taskrun with the specified attribute"""

        taskrun = TaskRunFactory.create(info='info')

        retrieved_taskrun = self.task_repo.get_task_run_by(info=taskrun.info)

        assert taskrun == retrieved_taskrun, retrieved_taskrun

    @with_context
    def test_get_task_run_by_info_json(self):
        """Test get_task_run_by with JSON returns a
        taskrun with the specified attribute"""

        data = {'foo': 'bar'}
        taskrun = TaskRunFactory.create(info=data)

        info = 'foo::bar'
        retrieved_taskrun = self.task_repo.get_task_run_by(info=info)

        assert taskrun == retrieved_taskrun, retrieved_taskrun

    @with_context
    def test_get_task_run_by_info_json_fulltext(self):
        """Test get_task_run_by with JSON and fulltext returns a
        taskrun with the specified attribute"""

        data = {'foo': 'bar'}
        taskrun = TaskRunFactory.create(info=data)

        info = 'foo::bar'
        retrieved_taskrun = self.task_repo.get_task_run_by(info=info,
                                                           fulltextsearch='1')

        assert taskrun == retrieved_taskrun, retrieved_taskrun



    @with_context
    def test_get_task_run_by_returns_none_if_no_task_run(self):
        """Test get_task_run_by returns None if no taskrun matches the query"""

        TaskRunFactory.create(info='info')

        taskrun = self.task_repo.get_task_run_by(info='other info')

        assert taskrun is None, taskrun


    @with_context
    def test_filter_task_runs_by_no_matches(self):
        """Test filter_task_runs_by returns an empty list if no taskruns match
        the query"""

        TaskRunFactory.create(info='info')

        retrieved_taskruns = self.task_repo.filter_task_runs_by(info='other')

        assert isinstance(retrieved_taskruns, list)
        assert len(retrieved_taskruns) == 0, retrieved_taskruns


    @with_context
    def test_filter_task_runs_by_one_condition(self):
        """Test filter_task_runs_by returns a list of taskruns that meet the
        filtering condition"""

        TaskRunFactory.create_batch(3, info='info')
        should_be_missing = TaskFactory.create(info='other info')

        retrieved_taskruns = self.task_repo.filter_task_runs_by(info='info')

        assert len(retrieved_taskruns) == 3, retrieved_taskruns
        assert should_be_missing not in retrieved_taskruns, retrieved_taskruns


    @with_context
    def test_filter_task_runs_by_multiple_conditions(self):
        """Test filter_task_runs_by supports multiple-condition queries"""

        TaskRunFactory.create(info='info', user_ip='8.8.8.8')
        taskrun = TaskRunFactory.create(info='info', user_ip='1.1.1.1')

        retrieved_taskruns = self.task_repo.filter_task_runs_by(info='info',
                                                                user_ip='1.1.1.1')

        assert len(retrieved_taskruns) == 1, retrieved_taskruns
        assert taskrun in retrieved_taskruns, retrieved_taskruns


    @with_context
    def test_filter_task_runs_by_multiple_conditions_fulltext(self):
        """Test filter_task_runs_by supports multiple-condition
        fulltext queries"""

        text = 'you agent something word'
        data = {'foo': 'bar', 'bar': text}
        TaskRunFactory.create(info=data, user_ip='8.8.8.8')
        taskrun = TaskRunFactory.create(info=data, user_ip='1.1.1.1')

        info = 'foo::bar|bar::agent'
        retrieved_taskruns = self.task_repo.filter_task_runs_by(info=info,
                                                                user_ip='1.1.1.1',
                                                                fulltextsearch='1')

        assert len(retrieved_taskruns) == 1, retrieved_taskruns
        assert taskrun in retrieved_taskruns[0], retrieved_taskruns

        retrieved_taskruns = self.task_repo.filter_task_runs_by(info=info,
                                                                user_ip='1.1.1.1')
        assert len(retrieved_taskruns) == 0, retrieved_taskruns

    @with_context
    def test_filter_task_runs_support_yield_option(self):
        """Test that filter_task_runs_by with the yielded=True option returns
        the results as a generator"""

        task_runs = TaskRunFactory.create_batch(2, info='info')

        yielded_task_runs = self.task_repo.filter_task_runs_by(info='info',
                                                               yielded=True)

        import types
        assert isinstance(yielded_task_runs.__iter__(), types.GeneratorType)
        for taskrun in yielded_task_runs:
            assert taskrun in task_runs


    @with_context
    def test_filter_tasks_runs_limit_offset(self):
        """Test that filter_tasks_by supports limit and offset options"""

        TaskRunFactory.create_batch(4)
        all_task_runs = self.task_repo.filter_task_runs_by()

        first_two = self.task_repo.filter_task_runs_by(limit=2)
        last_two = self.task_repo.filter_task_runs_by(limit=2, offset=2)

        assert len(first_two) == 2, first_two
        assert len(last_two) == 2, last_two
        assert first_two == all_task_runs[:2]
        assert last_two == all_task_runs[2:]


    @with_context
    def test_count_task_runs_with_no_matches(self):
        """Test count_task_runs_with returns 0 if no taskruns match the query"""

        TaskRunFactory.create(info='info')

        count = self.task_repo.count_task_runs_with(info='other info')

        assert count == 0, count


    @with_context
    def test_count_task_runs_with_one_condition(self):
        """Test count_task_runs_with returns the number of taskruns that meet the
        filtering condition"""

        TaskRunFactory.create_batch(3, info='info')
        should_be_missing = TaskRunFactory.create(info='other info')

        count = self.task_repo.count_task_runs_with(info='info')

        assert count == 3, count


    @with_context
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


    @with_context
    def test_save_saves_tasks(self):
        """Test save persists Task instances"""

        task = TaskFactory.build()
        assert self.task_repo.get_task(task.id) is None

        self.task_repo.save(task)

        assert self.task_repo.get_task(task.id) == task, "Task not saved"


    @with_context
    def test_save_saves_taskruns(self):
        """Test save persists TaskRun instances"""

        taskrun = TaskRunFactory.build()
        assert self.task_repo.get_task_run(taskrun.id) is None

        self.task_repo.save(taskrun)

        assert self.task_repo.get_task_run(taskrun.id) == taskrun, "TaskRun not saved"


    @with_context
    def test_save_fails_if_integrity_error(self):
        """Test save raises a DBIntegrityError if the instance to be saved lacks
        a required value"""

        task = TaskFactory.build(project_id=None, project=None)

        assert_raises(DBIntegrityError, self.task_repo.save, task)


    @with_context
    def test_save_only_saves_tasks_and_taskruns(self):
        """Test save raises a WrongObjectError when an object which is neither
        a Task nor a Taskrun instance is saved"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.task_repo.save, bad_object)


    @with_context
    def test_update_task(self):
        """Test update persists the changes made to Task instances"""

        task = TaskFactory.create(state='ongoing')
        task.state = 'done'

        self.task_repo.update(task)
        updated_task = self.task_repo.get_task(task.id)

        assert updated_task.state == 'done', updated_task


    @with_context
    def test_update_taskrun(self):
        """Test update persists the changes made to TaskRun instances"""

        taskrun = TaskRunFactory.create(info='info')
        taskrun.info = 'updated info!'

        self.task_repo.update(taskrun)
        updated_taskrun = self.task_repo.get_task_run(taskrun.id)

        assert updated_taskrun.info == 'updated info!', updated_taskrun


    @with_context
    def test_update_fails_if_integrity_error(self):
        """Test update raises a DBIntegrityError if the instance to be updated
        lacks a required value"""

        task = TaskFactory.create()
        task.project_id = None

        assert_raises(DBIntegrityError, self.task_repo.update, task)


    @with_context
    def test_update_only_updates_tasks_and_taskruns(self):
        """Test update raises a WrongObjectError when an object which is neither
        a Task nor a TaskRun instance is updated"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.task_repo.update, bad_object)


    @with_context
    def test_delete_task(self):
        """Test delete removes the Task instance"""

        task = TaskFactory.create()

        self.task_repo.delete(task)
        deleted = self.task_repo.get_task(task.id)

        assert deleted is None, deleted


    @with_context
    def test_delete_task_deletes_dependent_taskruns(self):
        """Test delete removes the dependent TaskRun instances"""

        task = TaskFactory.create()
        taskrun = TaskRunFactory.create(task=task)

        self.task_repo.delete(task)
        deleted = self.task_repo.get_task_run(taskrun.id)

        assert deleted is None, deleted


    @with_context
    def test_delete_taskrun(self):
        """Test delete removes the TaskRun instance"""

        taskrun = TaskRunFactory.create()

        self.task_repo.delete(taskrun)
        deleted = self.task_repo.get_task_run(taskrun.id)

        assert deleted is None, deleted


    @with_context
    def test_delete_only_deletes_tasks(self):
        """Test delete raises a WrongObjectError if is requested to delete other
        than a task"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.task_repo.delete, bad_object)


    @with_context
    def test_delete_valid_from_project_deletes_many_tasks(self):
        """Test delete_valid_from_project deletes many tasks at once"""

        tasks = TaskFactory.create_batch(2)

        project = project_repo.get(tasks[0].project_id)

        self.task_repo.delete_valid_from_project(project)

        tasks = self.task_repo.filter_tasks_by(project_id=project.id)

        assert len(tasks) == 0, len(tasks)


    @with_context
    def test_delete_valid_from_project_deletes_dependent(self):
        """Test delete_valid_from_project deletes dependent taskruns too"""

        task = TaskFactory.create()
        taskrun = TaskRunFactory.create(task=task)
        task_run_id = taskrun.id
        project = project_repo.get(task.project_id)

        self.task_repo.delete_valid_from_project(project)
        deleted = self.task_repo.get_task_run(id=task_run_id)

        assert deleted is None, deleted


    @with_context
    def test_delete_valid_from_project_deletes_dependent_without_result(self):
        """Test delete_valid_from_project deletes dependent taskruns without result"""

        task = TaskFactory.create(n_answers=1)
        project = project_repo.get(task.project_id)
        taskrun = TaskRunFactory.create(task=task)
        task2 = TaskFactory.create(project=project)
        TaskRunFactory.create(task=task2)

        self.task_repo.delete_valid_from_project(project)
        non_deleted = self.task_repo.filter_tasks_by(project_id=project.id)

        err_msg = "There should be one task, as it belongs to a result"
        assert len(non_deleted) == 1, err_msg
        assert non_deleted[0].id == task.id, err_msg

        non_deleted = self.task_repo.filter_task_runs_by(project_id=project.id)

        err_msg = "There should be one task_run, as it belongs to a result"
        assert len(non_deleted) == 1, err_msg
        assert non_deleted[0].id == taskrun.id, err_msg


    @with_context
    def test_delete_taskruns_from_project_deletes_taskruns(self):
        task = TaskFactory.create()
        project = project_repo.get(task.project_id)
        taskrun = TaskRunFactory.create(task=task)

        self.task_repo.delete_taskruns_from_project(project)
        taskruns = self.task_repo.filter_task_runs_by(project_id=project.id)

        assert taskruns == [], taskruns


    @with_context
    def test_update_tasks_redundancy_changes_all_project_tasks_redundancy(self):
        """Test update_tasks_redundancy updates the n_answers value for every
        task in the project"""

        project = ProjectFactory.create()
        TaskFactory.create_batch(2, project=project, n_answers=1)

        self.task_repo.update_tasks_redundancy(project, 2)
        tasks = self.task_repo.filter_tasks_by(project_id=project.id)

        for task in tasks:
            assert task.n_answers == 2, task.n_answers


    @with_context
    def test_update_tasks_redundancy_updates_state_when_incrementing(self):
        """Test update_tasks_redundancy changes 'completed' tasks to 'ongoing'
        if n_answers is incremented enough"""

        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(2, project=project, n_answers=2)
        TaskRunFactory.create_batch(2, task=tasks[0])
        tasks[0].state = 'completed'
        self.task_repo.update(tasks[0])

        assert tasks[0].state == 'completed', tasks[0].state
        assert tasks[1].state == 'ongoing', tasks[1].state

        self.task_repo.update_tasks_redundancy(project, 3)
        tasks = self.task_repo.filter_tasks_by(project_id=project.id)

        for task in tasks:
            assert task.state == 'ongoing', task.state


    @with_context
    def test_update_tasks_redundancy_updates_state_when_decrementing(self):
        """Test update_tasks_redundancy changes 'ongoing' tasks to 'completed'
        if n_answers is decremented enough"""

        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(2, project=project, n_answers=2)
        TaskRunFactory.create_batch(2, task=tasks[0])
        TaskRunFactory.create(task=tasks[1])
        tasks[0].state = 'completed'
        self.task_repo.update(tasks[0])

        assert tasks[0].state == 'completed', tasks[0].state
        assert tasks[1].state == 'ongoing', tasks[1].state

        self.task_repo.update_tasks_redundancy(project, 1)
        tasks = self.task_repo.filter_tasks_by(project_id=project.id)

        for task in tasks:
            assert task.state == 'completed', task.state
