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

#from base import web, model, Fixtures, db, redis_flushall
from default import Test, db, with_context
from pybossa.model import rebuild_db
from mock import patch, Mock


#def teardown_package(cls):
#    rebuild_db()
#    #redis_flushall()


class HelperAPI(Test):

    endpoints = ['app', 'task', 'taskrun', 'user']

    @with_context
    def setUp(self):
        super(HelperAPI, self).setUp()
        rebuild_db()
        self.create()

    @with_context
    def tearDown(self):
        db.session.remove()
        #redis_flushall()

    # Helper functions
    @with_context
    def register(self, method="POST", fullname="John Doe", username="johndoe",
                 password="p4ssw0rd", password2=None, email=None):
        """Helper function to register and sign in a user"""
        if password2 is None:
            password2 = password
        if email is None:
            email = username + '@example.com'
        if method == "POST":
            return self.app.post('/account/register',
                                 data={'fullname': fullname,
                                       'username': username,
                                       'email_addr': email,
                                       'password': password,
                                       'confirm': password2,
                                       },
                                 follow_redirects=True)
        else:
            return self.app.get('/account/register', follow_redirects=True)

    @with_context
    def signin(self, method="POST", email="johndoe@example.com", password="p4ssw0rd",
               next=None):
        """Helper function to sign in current user"""
        url = '/account/signin'
        if next is not None:
            url = url + '?next=' + next
        if method == "POST":
            return self.app.post(url,
                                 data={'email': email,
                                       'password': password},
                                 follow_redirects=True)
        else:
            return self.app.get(url, follow_redirects=True)

    @with_context
    def signout(self):
        """Helper function to sign out current user"""
        return self.app.get('/account/signout', follow_redirects=True)

