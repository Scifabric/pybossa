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

import json
import StringIO

from helper import web
from pybossa.model.blogpost import Blogpost
from pybossa.model.user import User
from base import redis_flushall, model, Fixtures
from mock import patch, Mock
from flask import Response
from collections import namedtuple
from pybossa.core import db, signer
from pybossa.util import unicode_csv_reader
from pybossa.util import get_user_signup_method
from pybossa.ckan import Ckan
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError
from werkzeug.exceptions import NotFound



class TestBlogpostView(web.Helper):

    def test_blogposts_get_all(self):
        """Test blogposts are shown"""
        user = Fixtures.create_users()[1]
        app = Fixtures.create_app(info=None)
        app.owner = user
        blogpost = Blogpost(owner=user, app=app, title='thisisatitle', body='body')
        db.session.add_all([user, app, blogpost])
        db.session.commit()
        url = "/app/%s/blog" % app.short_name

        # As anonymous
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'thisisatitle' in res.data

        # As authenticated
        self.register()
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'thisisatitle' in res.data


    def test_blogposts_get_all_app_hidden(self):
        """Test blogposts for hidden apps are not shown"""
        self.register()
        admin = db.session.query(User).get(1)
        self.signout()
        self.register(username='user', email='user@user.com')
        user = db.session.query(User).get(2)
        app = Fixtures.create_app(info=None)
        app.owner = user
        app.hidden = 1
        blogpost = Blogpost(owner=user, app=app, title='thisisatitle', body='body')
        db.session.add_all([app, blogpost])
        db.session.commit()
        url = "/app/%s/blog" % app.short_name

        # As app owner
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'thisisatitle' in res.data

        # As authenticated
        self.signout()
        self.register(username='notowner', email='user2@user.com')
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 403, res.status_code

        # As anonymous
        self.signout()
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 401, res.status_code

        # As admin
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'thisisatitle' in res.data


    def test_blogpost_get_all_errors(self):
        """Test blogpost get all raises error if the app does not exist"""
        url = "/app/non-existing-app/blog"

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code


    def test_blogpost_get_one(self):
        """Test blogpost get with id shows one blogpost"""
        user = Fixtures.create_users()[1]
        app = Fixtures.create_app(info=None)
        app.owner = user
        blogpost = Blogpost(owner=user, app=app, title='thisisatitle', body='body')
        db.session.add_all([user, app, blogpost])
        db.session.commit()
        url = "/app/%s/blog/%s" % (app.short_name, blogpost.id)

        # As anonymous
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'thisisatitle' in res.data

        # As authenticated
        self.register()
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'thisisatitle' in res.data


    def test_blogpost_get_one_app_hidden(self):
        """Test blogpost get with id with hidden app does not show the post"""


    def test_blogpost_get_one_errors(self):
        """Test blogposts get non existing posts raises errors"""
        'cuando el post no existe, la app no existe, o la app y el blog no se corresponden'



    def test_blogpost_create(self):
        """Test creation of blogposts for app owners"""
        user = Fixtures.create_users()[1]
        app = Fixtures.create_app(info=None)
        app.owner = user
        db.session.add_all([user, app])
        db.session.commit()
        blogpost = Blogpost(owner=user, app=app)
        url = "/app/%s/blog/new" % app.short_name

        # As anonymous



