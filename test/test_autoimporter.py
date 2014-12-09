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
from mock import patch, MagicMock
from redis import StrictRedis
from rq_scheduler import Scheduler
from default import db
from helper import web
from pybossa.model.app import App
from pybossa.model.user import User
from pybossa.jobs import import_tasks
from factories import AppFactory
from pybossa.view.applications import (_setup_autoimport_job, HOUR,
    _get_scheduled_autoimport_job)

class TestAutoimporterAccessAndResponses(web.Helper):

    def test_autoimporter_get_redirects_to_login_if_anonymous(self):
        """Test task autoimporter endpoint requires login"""
        app = AppFactory.create()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.get(url)
        redirect_url = 'http://localhost/account/signin?next='
        assert res.status_code == 302, res.status_code
        assert redirect_url in res.location, res.location


    def test_autoimporter_get_forbidden_non_owner(self):
        """Test task autoimporter returns Forbidden if non owner accesses"""
        self.register()
        self.new_application()
        app = db.session.query(App).first()
        self.signout()
        self.register(name='non-owner')
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.get(url)

        assert res.status_code == 403, res.status_code


    def test_autoimporter_get_forbidden_owner_no_pro(self):
        """Test task autoimporter returns Forbidden if no pro accesses"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.get(url, follow_redirects=True)
        assert  res.status_code == 403, res.status_code


    def test_autoimporter_get_owner_pro(self):
        """Test task autoimporter works for pro user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        owner = db.session.query(User).filter_by(name="owner").first()
        owner.pro = True
        db.session.commit()

        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.get(url, follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    def test_autoimporter_get_admin(self):
        """Test task autoimporter works for admin user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_application()
        self.signout()
        self.signin()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.get(url, follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    def test_autoimporter_get_nonexisting_project(self):
        """Test task autoimporter to a non existing project returns 404"""
        self.register()
        res = self.app.get("/app/noExists/tasks/autoimporter")

        assert res.status_code == 404, res.status_code


    def test_autoimporter_post_redirects_to_login_if_anonymous(self):
        """Test task autoimporter endpoint post requires login"""
        app = AppFactory.create()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.post(url, data={})
        redirect_url = 'http://localhost/account/signin?next='
        assert res.status_code == 302, res.status_code
        assert redirect_url in res.location, res.location


    def test_autoimporter_post_forbidden_non_owner(self):
        """Test task autoimporter post returns Forbidden if non owner accesses"""
        self.register()
        self.new_application()
        app = db.session.query(App).first()
        self.signout()
        self.register(name='non-owner')
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.post(url, data={})

        assert res.status_code == 403, res.status_code


    def test_autoimporter_post_forbidden_owner_no_pro(self):
        """Test task autoimporter post returns Forbidden if no pro accesses"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.post(url, data={}, follow_redirects=True)
        assert  res.status_code == 403, res.status_code


    def test_autoimporter_post_owner_pro(self):
        """Test task autoimporter post works for pro user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        owner = db.session.query(User).filter_by(name="owner").first()
        owner.pro = True
        db.session.commit()

        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.post(url, data={'csv_url': 'http://as.com',
                                       'formtype': 'json', 'form_name': 'csv'},
                                       follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    def test_autoimporter_post_admin(self):
        """Test task autoimporter post works for admin user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_application()
        self.signout()
        self.signin()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.post(url, data={'csv_url': 'http://as.com',
                                       'formtype': 'json', 'form_name': 'csv'},
                                       follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    def test_autoimporter_post_nonexisting_project(self):
        """Test task autoimporter post to a non existing project returns 404"""
        self.register()
        res = self.app.post("/app/noExists/tasks/autoimporter", data={})

        assert res.status_code == 404, res.status_code


    def test_delete_autoimporter_post_redirects_to_login_if_anonymous(self):
        """Test delete task autoimporter endpoint requires login"""
        app = AppFactory.create()
        url = "/app/%s/tasks/autoimporter/delete" % app.short_name

        res = self.app.post(url, data={})
        redirect_url = 'http://localhost/account/signin?next='
        assert res.status_code == 302, res.status_code
        assert redirect_url in res.location, res.location


    def test_delete_autoimporter_post_forbidden_non_owner(self):
        """Test delete task autoimporter returns Forbidden if non owner accesses"""
        self.register()
        self.new_application()
        app = db.session.query(App).first()
        self.signout()
        self.register(name='non-owner')
        url = "/app/%s/tasks/autoimporter/delete" % app.short_name

        res = self.app.post(url, data={})

        assert res.status_code == 403, res.status_code


    def test_delete_autoimporter_post_forbidden_owner_no_pro(self):
        """Test delete task autoimporter returns Forbidden if no pro accesses"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter/delete" % app.short_name

        res = self.app.post(url, data={}, follow_redirects=True)
        assert  res.status_code == 403, res.status_code


    def test_delete_autoimporter_post_owner_pro(self):
        """Test delete task autoimporter works for pro user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        owner = db.session.query(User).filter_by(name="owner").first()
        owner.pro = True
        db.session.commit()

        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter/delete" % app.short_name

        res = self.app.post(url, data={}, follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    def test_delete_autoimporter_post_admin(self):
        """Test delete task autoimporter works for admin user"""
        self.register()
        self.signout()
        # User
        self.register(name="owner")
        self.new_application()
        self.signout()
        self.signin()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter/delete" % app.short_name

        res = self.app.post(url, data={}, follow_redirects=True)
        assert  res.status_code == 200, res.status_code


    def test_delete_autoimporter_get_nonexisting_project(self):
        """Test task delete autoimporter to a non existing project returns 404"""
        self.register()
        res = self.app.post("/app/noExists/tasks/autoimporter/delete")

        assert res.status_code == 404, res.status_code



class TestAutoimporterBehaviour(web.Helper):

    def test_autoimporter_shows_template_to_create_new_if_no_autoimporter(self):
        """Test task autoimporter get renders the template for creating new
        autoimporter if none exists"""
        self.register()
        owner = db.session.query(User).first()
        app = AppFactory.create(owner=owner)
        url = "/app/%s/tasks/autoimporter" % app.short_name
        expected_text = "Setup task autoimporter"

        res = self.app.get(url, follow_redirects=True)

        assert expected_text in res.data
        assert 'CSV' in res.data
        assert 'Google Drive Spreadsheet' in res.data
        assert 'EpiCollect Plus Project' in res.data


    def test_autoimporter_with_specific_variant_argument(self):
        """Test task autoimporter with specific autoimporter variant argument
        shows the form for it, for each of the variants"""
        self.register()
        owner = db.session.query(User).first()
        app = AppFactory.create(owner=owner)

        # CSV
        url = "/app/%s/tasks/autoimporter?template=csv" % app.short_name
        res = self.app.get(url, follow_redirects=True)

        assert "From a CSV file" in res.data
        assert 'action="/app/%s/tasks/autoimporter"' % app.short_name in res.data

        # Google Docs
        url = "/app/%s/tasks/autoimporter?template=gdocs" % app.short_name
        res = self.app.get(url, follow_redirects=True)

        assert "From a Google Docs Spreadsheet" in res.data
        assert 'action="/app/%s/tasks/autoimporter"' % app.short_name in res.data

        # Epicollect Plus
        url = "/app/%s/tasks/autoimporter?template=epicollect" % app.short_name
        res = self.app.get(url, follow_redirects=True)

        assert "From an EpiCollect Plus project" in res.data
        assert 'action="/app/%s/tasks/autoimporter"' % app.short_name in res.data


    @patch('pybossa.view.applications._get_scheduled_autoimport_job')
    def test_autoimporter_shows_current_autoimporter_if_exists(self, scheduled):
        """Test task autoimporter shows the current autoimporter if exists"""
        self.register()
        owner = db.session.query(User).first()
        app = AppFactory.create(owner=owner)
        mock_autoimporter_job = MagicMock()
        mock_autoimporter_job.args = [app.id, 'csv']
        mock_autoimporter_job.kwargs = {'csv_url': 'http://fakeurl.com'}
        scheduled.return_value = mock_autoimporter_job
        url = "/app/%s/tasks/autoimporter" % app.short_name

        res = self.app.get(url, follow_redirects=True)

        assert "You currently have the following autoimporter" in res.data


    @patch('pybossa.view.applications._setup_autoimport_job')
    def test_autoimporter_post_calls_setup_autoimport_job(self, schedule):
        """Test a valid post to autoimporter endpoint calls the function that
        handles creation of the autoimport scheduled job"""
        self.register()
        owner = db.session.query(User).first()
        app = AppFactory.create(owner=owner)
        url = "/app/%s/tasks/autoimporter" % app.short_name
        data = {'form_name': 'csv', 'csv_url': 'http://fakeurl.com'}

        self.app.post(url, data=data, follow_redirects=True)

        schedule.assert_called_with(app, 'csv', csv_url=data['csv_url'])


    @patch('pybossa.view.applications._get_scheduled_autoimport_job')
    @patch('pybossa.view.applications._setup_autoimport_job')
    def test_autoimporter_prevents_from_duplicated(self, scheduler, scheduled):
        """Test a valid post to autoimporter endpoint will not create another
        autoimporter if one exists for that app"""
        self.register()
        owner = db.session.query(User).first()
        app = AppFactory.create(owner=owner)
        mock_autoimporter_job = MagicMock()
        mock_autoimporter_job._args = [app.id, 'csv']
        mock_autoimporter_job._kwargs = {'csv_url': 'http://fakeurl.com'}
        scheduled.return_value = mock_autoimporter_job
        url = "/app/%s/tasks/autoimporter" % app.short_name
        data = {'form_name': 'gdocs', 'googledocs_url': 'http://another.com'}

        res = self.app.post(url, data=data, follow_redirects=True)

        assert scheduler.called is False, "Another autoimporter was created"


    def test_setup_autoimport_job_creates_and_schedules_job(self):
        """Test _setup_autoimport_job function works as expected"""
        app = AppFactory.create()
        scheduler = Scheduler(queue_name='test', connection=StrictRedis())

        _setup_autoimport_job(app, 'csv', csv_url='http://fakeurl.com')

        job = scheduler.get_jobs()[0]
        assert job.func == import_tasks, job.func
        assert job.args == [app.id, 'csv'], job.args
        assert job.kwargs == {'csv_url': 'http://fakeurl.com'}, job.kwargs
        assert job.timeout == 500, job.timeout
        assert job.meta['interval'] == 24 * HOUR, job.meta


    def test_delete_autoimporter_deletes_current_autoimporter_job(self):
        from datetime import datetime
        self.register()
        self.new_application()
        app = db.session.query(App).first()
        url = "/app/%s/tasks/autoimporter/delete" % app.short_name
        scheduler = Scheduler(queue_name='test', connection=StrictRedis())
        job = scheduler.schedule(datetime.utcnow(), import_tasks,
                                 args=[app.id, 'csv'],
                                 kwargs={'csv_url': 'http://fake.com'})
        assert len(scheduler.get_jobs()) == 1

        res = self.app.post(url, data={}, follow_redirects=True)

        assert scheduler.get_jobs() == [], scheduler.get_jobs()


    def test_get_scheduled_autoimport_job_returns_None_if_no_autoimporter(self):
        app = AppFactory.create()
        job = _get_scheduled_autoimport_job(app.id)

        assert job is None, job


    def test_get_scheduled_autoimport_job_returns_job_autoimporter(self):
        from datetime import datetime
        scheduler = Scheduler(queue_name='test', connection=StrictRedis())
        app = AppFactory.create()
        scheduler.schedule(datetime.utcnow(), abs, args=[-1])
        job = scheduler.schedule(datetime.utcnow(), import_tasks,
                           args=[app.id, 'csv'],
                           kwargs={'csv_url': 'http://fake.com'})
        result = _get_scheduled_autoimport_job(app.id)

        assert result == job
