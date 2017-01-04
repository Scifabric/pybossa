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
from pybossa.jobs import import_tasks, task_repo, get_autoimport_jobs
from pybossa.model.task import Task
from pybossa.importers import ImportReport
from factories import ProjectFactory, TaskFactory, UserFactory
from mock import patch

class TestImportTasksJob(Test):

    @with_context
    @patch('pybossa.jobs.importer.create_tasks')
    def test_it_creates_the_new_tasks(self, create):
        project = ProjectFactory.create()
        form_data = {'type': 'csv', 'csv_url': 'http://google.es'}

        import_tasks(project.id, **form_data)

        create.assert_called_once_with(task_repo, project.id, **form_data)

    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('pybossa.jobs.importer.create_tasks')
    def test_sends_email_to_user_with_result_on_success(self, create, send_mail):
        create.return_value = ImportReport(message='1 new task was imported successfully', metadata=None, total=1)
        project = ProjectFactory.create()
        form_data = {'type': 'csv', 'csv_url': 'http://google.es'}
        subject = 'Tasks Import to your project %s' % project.name
        body = 'Hello,\n\n1 new task was imported successfully to your project %s!\n\nAll the best,\nThe PYBOSSA team.' % project.name
        email_data = dict(recipients=[project.owner.email_addr],
                          subject=subject, body=body)

        import_tasks(project.id, **form_data)

        send_mail.assert_called_once_with(email_data)

    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('pybossa.jobs.importer.create_tasks')
    def test_it_adds_import_metadata_to_autoimporter_if_is_autoimport_job(self, create, send_mail):
        create.return_value = ImportReport(message='1 new task was imported successfully', metadata="meta", total=1)
        form_data = {'type': 'csv', 'csv_url': 'http://google.es'}
        project = ProjectFactory.create(info=dict(autoimporter=form_data))
        subject = 'Tasks Import to your project %s' % project.name
        body = 'Hello,\n\n1 new task was imported successfully to your project %s!\n\nAll the best,\nThe PYBOSSA team.' % project.name
        email_data = dict(recipients=[project.owner.email_addr],
                          subject=subject, body=body)

        import_tasks(project.id, from_auto=True, **form_data)
        autoimporter = project.get_autoimporter()

        assert autoimporter.get('last_import_meta') == 'meta', autoimporter

    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('pybossa.jobs.importer.create_tasks')
    def test_it_does_not_add_import_metadata_to_autoimporter_if_is_import_job(self, create, send_mail):
        create.return_value = ImportReport(message='1 new task was imported successfully', metadata="meta", total=1)
        form_data = {'type': 'csv', 'csv_url': 'http://google.es'}
        project = ProjectFactory.create(info=dict(autoimporter=form_data))
        subject = 'Tasks Import to your project %s' % project.name
        body = 'Hello,\n\n1 new task was imported successfully to your project %s!\n\nAll the best,\nThe PYBOSSA team.' % project.name
        email_data = dict(recipients=[project.owner.email_addr],
                          subject=subject, body=body)

        import_tasks(project.id, from_auto=False, **form_data)
        autoimporter = project.get_autoimporter()

        assert autoimporter.get('last_import_meta') == None, autoimporter


class TestAutoimportJobs(Test):
    @with_context
    def test_autoimport_jobs_no_autoimporter(self):
        """Test JOB autoimport does not return projects without autoimporter."""
        user = UserFactory.create(pro=True)
        ProjectFactory.create(owner=user)
        jobs_generator = get_autoimport_jobs()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be 0 jobs."
        assert len(jobs) == 0, msg

    @with_context
    def test_autoimport_jobs_with_autoimporter(self):
        """Test JOB autoimport jobs returns projects with autoimporter."""
        user = UserFactory.create(pro=True)
        project = ProjectFactory.create(owner=user,info=dict(autoimporter='foobar'))
        jobs_generator = get_autoimport_jobs()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be 1 job."
        assert len(jobs) == 1, msg
        job = jobs[0]
        msg = "It sould be the same project."
        assert job['args'][0] == project.id, msg
        msg = "It sould be created as an auto import job."
        assert job['args'][1] == True, msg
        msg = "There sould be the kwargs."
        assert job['kwargs'] == 'foobar', msg

    @with_context
    @patch.dict(flask_app.config, {'PRO_FEATURES': {'autoimporter': True}})
    def test_autoimport_jobs_without_pro_when_only_pro(self):
        """Test JOB autoimport jobs does not return normal user owned projects
        if autoimporter is only enabled for pros."""
        ProjectFactory.create(info=dict(autoimporter='foobar'))
        jobs_generator = get_autoimport_jobs()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be 0 jobs."
        assert len(jobs) == 0, msg

    @with_context
    @patch.dict(flask_app.config, {'PRO_FEATURES': {'autoimporter': False}})
    def test_autoimport_jobs_without_pro_when_for_everyone(self):
        """Test JOB autoimport jobs returns normal user owned projects
        if autoimporter is enabled for everyone."""
        project = ProjectFactory.create(info=dict(autoimporter='foobar'))
        jobs_generator = get_autoimport_jobs()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be 1 job."
        assert len(jobs) == 1, msg
        job = jobs[0]
        msg = "It sould be the same project."
        assert job['args'][0] == project.id, msg
        msg = "It sould be created as an auto import job."
        assert job['args'][1] == True, msg
        msg = "There sould be the kwargs."
        assert job['kwargs'] == 'foobar', msg
