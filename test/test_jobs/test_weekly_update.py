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

from default import Test, with_context, flask_app
from pybossa.jobs import get_weekly_stats_update_projects
from pybossa.jobs import send_weekly_stats_project
from factories import TaskRunFactory, UserFactory, ProjectFactory, TaskFactory
from mock import patch, MagicMock
from nose.tools import assert_raises


class TestWeeklyStats(Test):


    @with_context
    @patch('pybossa.jobs.datetime')
    def test_get_jobs_only_on_sunday(self, mock_datetime):
        """Test JOB get jobs for weekly stats works only on Sunday."""
        user = UserFactory.create(pro=True)
        pr = ProjectFactory(owner=user)
        task = TaskFactory.create(project=pr)
        TaskRunFactory.create(project=pr, task=task)
        mock_date = MagicMock()
        mock_date.strftime.return_value = 'Monday'
        mock_datetime.today.return_value = mock_date

        jobs = get_weekly_stats_update_projects()
        assert_raises(StopIteration, jobs.__next__)

    @with_context
    @patch('pybossa.jobs.datetime')
    def test_get_jobs_only_on_sunday_variant(self, mock_datetime):
        """Test JOB get jobs for weekly stats works only on Sunday variant."""
        user = UserFactory.create(pro=True)
        pr = ProjectFactory(owner=user)
        task = TaskFactory.create(project=pr)
        TaskRunFactory.create(project=pr, task=task)
        mock_date = MagicMock()
        mock_date.strftime.return_value = 'Sunday'
        mock_datetime.today.return_value = mock_date

        jobs = get_weekly_stats_update_projects()
        for job in jobs:
            assert type(job) == dict, type(job)
            assert job['name'] == send_weekly_stats_project
            assert job['args'] == [pr.id]
            assert job['kwargs'] == {}
            assert job['timeout'] == self.flask_app.config.get('TIMEOUT')
            assert job['queue'] == 'low'

    @with_context
    @patch('pybossa.jobs.datetime')
    def test_get_jobs_no_pro_feature_only_for_pros(self, mock_datetime):
        """Test JOB get jobs for weekly stats works only for pros if feature is
        only for pros."""
        user = UserFactory.create(pro=False)
        pr = ProjectFactory(owner=user)
        task = TaskFactory.create(project=pr)
        TaskRunFactory.create(project=pr, task=task)
        mock_date = MagicMock()
        mock_date.strftime.return_value = 'Sunday'
        mock_datetime.today.return_value = mock_date

        jobs = get_weekly_stats_update_projects()
        assert_raises(StopIteration, jobs.__next__)

    @with_context
    @patch('pybossa.jobs.datetime')
    @patch.dict(flask_app.config, {'PRO_FEATURES': {'project_weekly_report': False}})
    def test_get_jobs_no_pro_feature_for_everyone(self, mock_datetime):
        """Test JOB get jobs for weekly stats works for non pros if feature is
        only for everyone."""
        user = UserFactory.create(pro=False)
        pr = ProjectFactory(owner=user)
        task = TaskFactory.create(project=pr)
        TaskRunFactory.create(project=pr, task=task)
        mock_date = MagicMock()
        mock_date.strftime.return_value = 'Sunday'
        mock_datetime.today.return_value = mock_date

        jobs = [job for job in get_weekly_stats_update_projects()]

        assert len(jobs) == 1
        for job in jobs:
            assert type(job) == dict, type(job)
            assert job['name'] == send_weekly_stats_project
            assert job['args'] == [pr.id]
            assert job['kwargs'] == {}
            assert job['timeout'] == self.flask_app.config.get('TIMEOUT')
            assert job['queue'] == 'low'

    @with_context
    @patch('pybossa.jobs.datetime')
    def test_get_jobs_no_featured(self, mock_datetime):
        """Test JOB get jobs for weekly stats works only for featured."""
        user = UserFactory.create(pro=False)
        pr = ProjectFactory(owner=user, featured=False)
        task = TaskFactory.create(project=pr)
        TaskRunFactory.create(project=pr, task=task)
        mock_date = MagicMock()
        mock_date.strftime.return_value = 'Sunday'
        mock_datetime.today.return_value = mock_date

        jobs = get_weekly_stats_update_projects()
        assert_raises(StopIteration, jobs.__next__)

    @with_context
    @patch('pybossa.jobs.datetime')
    def test_get_jobs_only_on_featured_variant(self, mock_datetime):
        """Test JOB get jobs for weekly stats works for featured."""
        user = UserFactory.create(pro=False)
        pr = ProjectFactory(owner=user, featured=True)
        task = TaskFactory.create(project=pr)
        TaskRunFactory.create(project=pr, task=task)
        mock_date = MagicMock()
        mock_date.strftime.return_value = 'Sunday'
        mock_datetime.today.return_value = mock_date

        jobs = get_weekly_stats_update_projects()
        for job in jobs:
            assert type(job) == dict, type(job)
            assert job['name'] == send_weekly_stats_project
            assert job['args'] == [pr.id]
            assert job['kwargs'] == {}
            assert job['timeout'] == self.flask_app.config.get('TIMEOUT')
            assert job['queue'] == 'low'

    @with_context
    @patch('pybossa.jobs.enqueue_job')
    def test_send_email(self, mock):
        """Test JOB send email works."""
        user = UserFactory.create(pro=False)
        pr = ProjectFactory(owner=user, featured=True)
        task = TaskFactory.create(project=pr)
        TaskRunFactory.create(project=pr, task=task)
        send_weekly_stats_project(pr.id)
        assert mock.called

    @with_context
    @patch('pybossa.jobs.enqueue_job')
    def test_send_email_not_subscribed(self, mock):
        """Test JOB send email not subscribed works."""
        user = UserFactory.create(pro=False, subscribed=False)
        pr = ProjectFactory(owner=user, featured=True)
        task = TaskFactory.create(project=pr)
        TaskRunFactory.create(project=pr, task=task)
        res = send_weekly_stats_project(pr.id)
        assert res == "Owner does not want updates by email", res
