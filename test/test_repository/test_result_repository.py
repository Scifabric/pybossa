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
from factories import TaskFactory, TaskRunFactory, ProjectFactory
from pybossa.repositories import ResultRepository
from pybossa.core import task_repo, result_repo
from nose.tools import assert_raises
from pybossa.exc import WrongObjectError, DBIntegrityError


class TestResultRepository(Test):

    def setUp(self):
        super(TestResultRepository, self).setUp()
        self.result_repo = ResultRepository(db)

    @with_context
    def create_result(self, n_answers=1, filter_by=False):
        task = TaskFactory.create(n_answers=n_answers)
        TaskRunFactory.create(task=task)
        if filter_by:
            return self.result_repo.filter_by(project_id=1)
        else:
            return self.result_repo.get_by(project_id=1)


    @with_context
    def test_get_return_none_if_no_result(self):
        """Test get method returns None if there is no result with the
        specified id"""

        result = self.result_repo.get(2)

        assert result is None, result


    @with_context
    def test_get_returns_result(self):
        """Test get method returns a result if exists"""

        n_answers = 1

        task = TaskFactory.create(n_answers=n_answers)
        task_run = TaskRunFactory.create(task=task)

        result = self.result_repo.filter_by(project_id=1)


        err_msg = "There should be a result"
        assert len(result) == 1, err_msg
        result = result[0]
        assert result.project_id == 1, err_msg
        assert result.task_id == task.id, err_msg
        assert len(result.task_run_ids) == n_answers, err_msg
        err_msg = "The task_run id is missing in the results array"
        for tr_id in result.task_run_ids:
            assert tr_id == task_run.id, err_msg

    @with_context
    def test_get_by_returns_result(self):
        """Test get_by method returns a result if exists"""

        n_answers = 1

        task = TaskFactory.create(n_answers=n_answers)
        task_run = TaskRunFactory.create(task=task)

        result = self.result_repo.get_by(project_id=1)


        err_msg = "There should be a result"
        assert result.project_id == 1, err_msg
        assert result.task_id == task.id, err_msg
        assert len(result.task_run_ids) == n_answers, err_msg
        err_msg = "The task_run id is missing in the results array"
        for tr_id in result.task_run_ids:
            assert tr_id == task_run.id, err_msg


    @with_context
    def test_get_returns_result_after_increasig_redundancy(self):
        """Test get method returns a result if after increasing redundancy"""

        n_answers = 1

        task = TaskFactory.create(n_answers=n_answers)
        task_run = TaskRunFactory.create(task=task)

        result = self.result_repo.filter_by(project_id=1)

        err_msg = "There should be a result"
        assert len(result) == 1, err_msg
        result = result[0]
        assert result.project_id == 1, err_msg
        assert result.task_id == task.id, err_msg
        assert len(result.task_run_ids) == n_answers, err_msg
        err_msg = "The task_run id is missing in the results array"
        for tr_id in result.task_run_ids:
            assert tr_id == task_run.id, err_msg

        # Increase redundancy
        tmp = task_repo.get_task(task.id)
        tmp.n_answers = 2
        task_repo.update(task)

        err_msg = "There should be only one result"
        results = result_repo.filter_by(project_id=1)
        assert len(results) == 1, err_msg
        task_run_2 = TaskRunFactory.create(task=task)

        err_msg = "There should be 1 results"
        results = result_repo.filter_by(project_id=1)
        assert len(results) == 1, err_msg

        err_msg = "There should be 2 results"
        results = result_repo.filter_by(project_id=1, last_version=False)
        assert len(results) == 2, err_msg

        assert results[1].project_id == 1, err_msg
        assert results[1].task_id == task.id, err_msg
        err_msg = "First result should have only one task run ID"
        assert len(results[0].task_run_ids) == 1, err_msg
        err_msg = "Second result should have only two task run IDs"
        assert len(results[1].task_run_ids) == 2, err_msg
        err_msg = "The task_run id is missing in the results array"
        for tr_id in results[1].task_run_ids:
            assert tr_id in [task_run.id, task_run_2.id], err_msg


    @with_context
    def test_get_returns_no_result(self):
        """Test get method does not return a result if task not completed"""

        n_answers = 3

        task = TaskFactory.create(n_answers=n_answers)
        TaskRunFactory.create(task=task)

        result = self.result_repo.filter_by(project_id=1)

        err_msg = "There should not be a result"
        assert len(result) == 0, err_msg

    @with_context
    def test_fulltext_search_result(self):
        """Test fulltext search in JSON info works."""
        result = self.create_result()
        text = 'something word you me bar'
        data = {'foo': text}
        result.info = data
        self.result_repo.update(result)

        info = 'foo::word'
        res = self.result_repo.filter_by(info=info, fulltextsearch='1')
        assert len(res) == 1, len(res)
        assert res[0][0].info['foo'] == text, res[0]

        res = self.result_repo.filter_by(info=info)
        assert len(res) == 0, len(res)

    @with_context
    def test_fulltext_search_result_01(self):
        """Test fulltext search in JSON info works."""
        result = self.create_result()
        text = 'something word you me bar'
        data = {'foo': text, 'bar': 'foo'}
        result.info = data
        self.result_repo.update(result)

        info = 'foo::word&bar|bar::foo'
        res = self.result_repo.filter_by(info=info, fulltextsearch='1')
        assert len(res) == 1, len(res)
        assert res[0][0].info['foo'] == text, res[0]


    @with_context
    def test_info_json_search_result(self):
        """Test search in JSON info works."""
        result = self.create_result()
        text = 'bar'
        data = {'foo': text}
        result.info = data
        self.result_repo.update(result)

        info = 'foo::bar'
        res = self.result_repo.filter_by(info=info)
        assert len(res) == 1, len(res)
        assert res[0].info['foo'] == text, res[0]


    @with_context
    def test_update(self):
        """Test update persists the changes made to the result"""

        result = self.create_result()
        result.info = dict(new='value')

        self.result_repo.update(result)
        updated_result = self.result_repo.get(result.id)

        assert updated_result.info['new'] == 'value', updated_result


    @with_context
    def test_update_fails_if_integrity_error(self):
        """Test update raises a DBIntegrityError if the instance to be updated
        lacks a required value"""

        result = self.create_result()
        result.project_id = None

        assert_raises(DBIntegrityError, self.result_repo.update, result)


    @with_context
    def test_update_only_updates_results(self):
        """Test update raises a WrongObjectError when an object which is not
        a Result instance is updated"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.result_repo.update, bad_object)

    @with_context
    def test_delete_results_from_project(self):
        """Test delte_results_from_project works."""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project,n_answers=1)
        taskrun = TaskRunFactory.create(task=task, project=project)
        result = result_repo.get_by(project_id=task.project.id)
        assert result
        result_repo.delete_results_from_project(project)
        result = result_repo.get_by(project_id=task.project.id)
        assert result is None
