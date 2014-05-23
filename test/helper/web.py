# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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

from default import Test, db, Fixtures, with_context
from helper.user import User
from pybossa.model.app import App
from pybossa.model.category import Category
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun


class Helper(Test):
    """Class to help testing the web interface"""

    user = User()

    def html_title(self, title=None):
        """Helper function to create an HTML title"""
        if title is None:
            return "<title>PyBossa</title>"
        else:
            return "<title>PyBossa &middot; %s</title>" % title

    def register(self, method="POST", fullname="John Doe", name="johndoe",
                 password="p4ssw0rd", password2=None, email=None):
        """Helper function to register and sign in a user"""
        if password2 is None:
            password2 = password
        if email is None:
            email = name + '@example.com'
        if method == "POST":
            return self.app.post('/account/register',
                                 data={
                                     'fullname': fullname,
                                     'name': name,
                                     'email_addr': email,
                                     'password': password,
                                     'confirm': password2},
                                 follow_redirects=True)
        else:
            return self.app.get('/account/register', follow_redirects=True)

    def signin(self, method="POST", email="johndoe@example.com", password="p4ssw0rd",
               next=None):
        """Helper function to sign in current user"""
        url = '/account/signin'
        if next is not None:
            url = url + '?next=' + next
        if method == "POST":
            return self.app.post(url, data={'email': email,
                                            'password': password},
                                 follow_redirects=True)
        else:
            return self.app.get(url, follow_redirects=True)

    def profile(self, name="johndoe"):
        """Helper function to check profile of signed in user"""
        url = "/account/%s" % name
        return self.app.get(url, follow_redirects=True)

    def update_profile(self, method="POST", id=1, fullname="John Doe",
                       name="johndoe", locale="es",
                       email_addr="johndoe@example.com",
                       new_name=None,
                       btn='Profile'):
        """Helper function to update the profile of users"""
        url = "/account/%s/update" % name
        if new_name:
            name = new_name
        if (method == "POST"):
            return self.app.post(url,
                                 data={'id': id,
                                       'fullname': fullname,
                                       'name': name,
                                       'locale': locale,
                                       'email_addr': email_addr,
                                       'btn': btn},
                                 follow_redirects=True)
        else:
            return self.app.get(url,
                                follow_redirects=True)

    def signout(self):
        """Helper function to sign out current user"""
        return self.app.get('/account/signout', follow_redirects=True)

    def create_categories(self):
        with self.flask_app.app_context():
            categories = db.session.query(Category).all()
            if len(categories) == 0:
                print "Categories 0"
                print "Creating default ones"
                self._create_categories()


    def new_application(self, method="POST", name="Sample App",
                        short_name="sampleapp", description="Description",
                        long_description=u'Long Description\n================'):
        """Helper function to create an application"""
        if method == "POST":
            self.create_categories()
            return self.app.post("/app/new", data={
                'name': name,
                'short_name': short_name,
                'description': description,
                'long_description': long_description,
            }, follow_redirects=True)
        else:
            return self.app.get("/app/new", follow_redirects=True)

    def new_task(self, appid):
        """Helper function to create tasks for an app"""
        tasks = []
        for i in range(0, 10):
            tasks.append(Task(app_id=appid, state='0', info={}))
        db.session.add_all(tasks)
        db.session.commit()

    def delete_task_runs(self, app_id=1):
        """Deletes all TaskRuns for a given app_id"""
        db.session.query(TaskRun).filter_by(app_id=1).delete()
        db.session.commit()

    def task_settings_scheduler(self, method="POST", short_name='sampleapp',
                                sched="default"):
        """Helper function to modify task scheduler"""
        url = "/app/%s/tasks/scheduler" % short_name
        if method == "POST":
            return self.app.post(url, data={
                'sched': sched,
            }, follow_redirects=True)
        else:
            return self.app.get(url, follow_redirects=True)

    def task_settings_redundancy(self, method="POST", short_name='sampleapp',
                                 n_answers=30):
        """Helper function to modify task redundancy"""
        url = "/app/%s/tasks/redundancy" % short_name
        if method == "POST":
            return self.app.post(url, data={
                'n_answers': n_answers,
            }, follow_redirects=True)
        else:
            return self.app.get(url, follow_redirects=True)

    def task_settings_priority(self, method="POST", short_name='sampleapp',
                                 task_ids="1", priority_0=0.0):
        """Helper function to modify task redundancy"""
        url = "/app/%s/tasks/priority" % short_name
        if method == "POST":
            return self.app.post(url, data={
                'task_ids': task_ids,
                'priority_0': priority_0
            }, follow_redirects=True)
        else:
            return self.app.get(url, follow_redirects=True)

    def delete_application(self, method="POST", short_name="sampleapp"):
        """Helper function to delete an application"""
        if method == "POST":
            return self.app.post("/app/%s/delete" % short_name,
                                 follow_redirects=True)
        else:
            return self.app.get("/app/%s/delete" % short_name,
                                follow_redirects=True)

    def update_application(self, method="POST", short_name="sampleapp", id=1,
                           new_name="Sample App", new_short_name="sampleapp",
                           new_description="Description",
                           new_allow_anonymous_contributors="False",
                           new_category_id="2",
                           new_long_description="Long desc",
                           new_sched="random",
                           new_hidden=False):
        """Helper function to update an application"""
        if method == "POST":
            if new_hidden:
                return self.app.post("/app/%s/update" % short_name,
                                     data={
                                         'id': id,
                                         'name': new_name,
                                         'short_name': new_short_name,
                                         'description': new_description,
                                         'allow_anonymous_contributors': new_allow_anonymous_contributors,
                                         'category_id': new_category_id,
                                         'long_description': new_long_description,
                                         'sched': new_sched,
                                         'hidden': new_hidden,
                                         'btn': 'Save'},
                                     follow_redirects=True)
            else:
                return self.app.post("/app/%s/update" % short_name,
                                     data={'id': id, 'name': new_name,
                                           'short_name': new_short_name,
                                           'allow_anonymous_contributors': new_allow_anonymous_contributors,
                                           'category_id': new_category_id,
                                           'long_description': new_long_description,
                                           'sched': new_sched,
                                           'description': new_description,
                                           'btn': 'Save'
                                           },
                                     follow_redirects=True)
        else:
            return self.app.get("/app/%s/update" % short_name,
                                follow_redirects=True)
