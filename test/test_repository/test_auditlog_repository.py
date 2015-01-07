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
from factories import AppFactory
from factories import AuditlogFactory, UserFactory
from pybossa.repositories import AuditlogRepository
from pybossa.exc import WrongObjectError, DBIntegrityError


class TestAuditlogRepositoryForProjects(Test):

    def setUp(self):
        super(TestAuditlogRepositoryForProjects, self).setUp()
        self.auditlog_repo = AuditlogRepository(db)


    def test_get_return_none_if_no_log(self):
        """Test get method returns None if there is no log with the
        specified id"""

        log = self.auditlog_repo.get(2)

        assert log is None, log


    def test_get_returns_log(self):
        """Test get method returns a log if exists"""

        app = AppFactory.create()
        log = AuditlogFactory.create(app_id=app.id,
                                     app_short_name=app.short_name,
                                     user_id=app.owner.id,
                                     user_name=app.owner.name)

        retrieved_log = self.auditlog_repo.get(log.id)

        assert log == retrieved_log, retrieved_log


    def test_get_by(self):
        """Test get_by returns a log with the specified attribute"""

        app = AppFactory.create()
        log = AuditlogFactory.create(app_id=app.id,
                                     app_short_name=app.short_name,
                                     user_id=app.owner.id,
                                     user_name=app.owner.name)


        retrieved_log = self.auditlog_repo.get_by(user_id=app.owner.id)

        assert log == retrieved_log, retrieved_log


    def test_get_by_returns_none_if_no_log(self):
        """Test get_by returns None if no log matches the query"""

        app = AppFactory.create()
        AuditlogFactory.create(app_id=app.id,
                               app_short_name=app.short_name,
                               user_id=app.owner.id,
                               user_name=app.owner.name)

        retrieved_log = self.auditlog_repo.get_by(user_id=5555)

        assert retrieved_log is None, retrieved_log


    def test_filter_by_no_matches(self):
        """Test filter_by returns an empty list if no log matches the query"""

        app = AppFactory.create()
        AuditlogFactory.create(app_id=app.id,
                               app_short_name=app.short_name,
                               user_id=app.owner.id,
                               user_name=app.owner.name)

        retrieved_logs = self.auditlog_repo.filter_by(user_name='no_name')

        assert isinstance(retrieved_logs, list)
        assert len(retrieved_logs) == 0, retrieved_logs


    def test_filter_by_one_condition(self):
        """Test filter_by returns a list of logs that meet the filtering
        condition"""

        app = AppFactory.create()
        AuditlogFactory.create_batch(size=3, app_id=app.id,
                               app_short_name=app.short_name,
                               user_id=app.owner.id,
                               user_name=app.owner.name)

        app2 = AppFactory.create()
        should_be_missing = AuditlogFactory.create_batch(size=3, app_id=app2.id,
                                                   app_short_name=app2.short_name,
                                                   user_id=app2.owner.id,
                                                   user_name=app2.owner.name)


        retrieved_logs = self.auditlog_repo.filter_by(user_id=app.owner.id)

        assert len(retrieved_logs) == 3, retrieved_logs
        assert should_be_missing not in retrieved_logs, retrieved_logs


    def test_filter_by_multiple_conditions(self):
        """Test filter_by supports multiple-condition queries"""

        app = AppFactory.create()
        user = UserFactory.create()
        AuditlogFactory.create_batch(size=3, app_id=app.id,
                               app_short_name=app.short_name,
                               user_id=app.owner.id,
                               user_name=app.owner.name)

        log = AuditlogFactory.create(app_id=app.id,
                                     app_short_name=app.short_name,
                                     user_id=user.id,
                                     user_name=user.name)

        retrieved_logs = self.auditlog_repo.filter_by(app_id=app.id,
                                                      user_id=user.id)

        assert len(retrieved_logs) == 1, retrieved_logs
        assert log in retrieved_logs, retrieved_logs


    def test_save(self):
        """Test save persist the log"""

        app = AppFactory.create()
        log = AuditlogFactory.build(app_id=app.id,
                                    app_short_name=app.short_name,
                                    user_id=app.owner.id,
                                    user_name=app.owner.name)

        assert self.auditlog_repo.get(log.id) is None

        self.auditlog_repo.save(log)

        assert self.auditlog_repo.get(log.id) == log, "Log not saved"


    def test_save_fails_if_integrity_error(self):
        """Test save raises a DBIntegrityError if the instance to be saved lacks
        a required value"""

        log = AuditlogFactory.build(app_id=None)

        assert_raises(DBIntegrityError, self.auditlog_repo.save, log)


    def test_save_only_saves_projects(self):
        """Test save raises a WrongObjectError when an object which is not
        a Log instance is saved"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.auditlog_repo.save, bad_object)
