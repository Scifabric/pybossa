# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
from factories import ProjectFactory, TaskFactory, TaskRunFactory
from factories import UserFactory
from pybossa.repositories import ResultRepository
from pybossa.exc import WrongObjectError, DBIntegrityError


class TestResultRepository(Test):

    def setUp(self):
        super(TestResultRepository, self).setUp()
        self.result_repo = ResultRepository(db)


    def test_get_return_none_if_no_result(self):
        """Test get method returns None if there is no result with the
        specified id"""

        result = self.result_repo.get(2)

        assert result is None, result


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

    def test_get_returns_no_result(self):
        """Test get method does not return a result if task not completed"""

        n_answers = 3

        task = TaskFactory.create(n_answers=n_answers)
        TaskRunFactory.create(task=task)

        result = self.result_repo.filter_by(project_id=1)

        err_msg = "There should not be a result"
        assert len(result) == 0, err_msg


    # def test_get_by(self):
    #     """Test get_by returns a log with the specified attribute"""

    #     project = ProjectFactory.create()
    #     log = AuditlogFactory.create(project_id=project.id,
    #                                  project_short_name=project.short_name,
    #                                  user_id=project.owner.id,
    #                                  user_name=project.owner.name)


    #     retrieved_log = self.result_repo.get_by(user_id=project.owner.id)

    #     assert log == retrieved_log, retrieved_log


    # def test_get_by_returns_none_if_no_log(self):
    #     """Test get_by returns None if no log matches the query"""

    #     project = ProjectFactory.create()
    #     AuditlogFactory.create(project_id=project.id,
    #                            project_short_name=project.short_name,
    #                            user_id=project.owner.id,
    #                            user_name=project.owner.name)

    #     retrieved_log = self.result_repo.get_by(user_id=5555)

    #     assert retrieved_log is None, retrieved_log


    # def test_filter_by_no_matches(self):
    #     """Test filter_by returns an empty list if no log matches the query"""

    #     project = ProjectFactory.create()
    #     AuditlogFactory.create(project_id=project.id,
    #                            project_short_name=project.short_name,
    #                            user_id=project.owner.id,
    #                            user_name=project.owner.name)

    #     retrieved_logs = self.result_repo.filter_by(user_name='no_name')

    #     assert isinstance(retrieved_logs, list)
    #     assert len(retrieved_logs) == 0, retrieved_logs


    # def test_filter_by_one_condition(self):
    #     """Test filter_by returns a list of logs that meet the filtering
    #     condition"""

    #     project = ProjectFactory.create()
    #     AuditlogFactory.create_batch(size=3, project_id=project.id,
    #                            project_short_name=project.short_name,
    #                            user_id=project.owner.id,
    #                            user_name=project.owner.name)

    #     project2 = ProjectFactory.create()
    #     should_be_missing = AuditlogFactory.create_batch(size=3, project_id=project2.id,
    #                                                project_short_name=project2.short_name,
    #                                                user_id=project2.owner.id,
    #                                                user_name=project2.owner.name)


    #     retrieved_logs = self.result_repo.filter_by(user_id=project.owner.id)

    #     assert len(retrieved_logs) == 3, retrieved_logs
    #     assert should_be_missing not in retrieved_logs, retrieved_logs


    # def test_filter_by_multiple_conditions(self):
    #     """Test filter_by supports multiple-condition queries"""

    #     project = ProjectFactory.create()
    #     user = UserFactory.create()
    #     AuditlogFactory.create_batch(size=3, project_id=project.id,
    #                            project_short_name=project.short_name,
    #                            user_id=project.owner.id,
    #                            user_name=project.owner.name)

    #     log = AuditlogFactory.create(project_id=project.id,
    #                                  project_short_name=project.short_name,
    #                                  user_id=user.id,
    #                                  user_name=user.name)

    #     retrieved_logs = self.result_repo.filter_by(project_id=project.id,
    #                                                   user_id=user.id)

    #     assert len(retrieved_logs) == 1, retrieved_logs
    #     assert log in retrieved_logs, retrieved_logs


    # def test_save(self):
    #     """Test save persist the log"""

    #     project = ProjectFactory.create()
    #     log = AuditlogFactory.build(project_id=project.id,
    #                                 project_short_name=project.short_name,
    #                                 user_id=project.owner.id,
    #                                 user_name=project.owner.name)

    #     assert self.result_repo.get(log.id) is None

    #     self.result_repo.save(log)

    #     assert self.result_repo.get(log.id) == log, "Log not saved"


    # def test_save_fails_if_integrity_error(self):
    #     """Test save raises a DBIntegrityError if the instance to be saved lacks
    #     a required value"""

    #     log = AuditlogFactory.build(project_id=None)

    #     assert_raises(DBIntegrityError, self.result_repo.save, log)


    # def test_save_only_saves_projects(self):
    #     """Test save raises a WrongObjectError when an object which is not
    #     a Log instance is saved"""

    #     bad_object = dict()

    #     assert_raises(WrongObjectError, self.result_repo.save, bad_object)
