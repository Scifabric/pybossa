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


from helper import web
from pybossa.model.blogpost import Blogpost
from pybossa.model.user import User
from base import redis_flushall, model, Fixtures
from mock import patch, Mock
from flask import Response, url_for
from pybossa.core import db
from werkzeug.exceptions import NotFound



class TestBlogpostView(web.Helper):

    def test_blogposts_get_all(self):
        """Test blogpost GET all blogposts"""
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


    def test_blogposts_get_all_with_hidden_app(self):
        """Test blogpost GET does not show hidden apps"""
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
        """Test blogpost GET all raises error if the app does not exist"""
        url = "/app/non-existing-app/blog"

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code


    def test_blogpost_get_one(self):
        """Test blogpost GET with id shows one blogpost"""
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


    def test_blogpost_get_one_with_hidden_app(self):
        """Test blogpost GET a given post id with hidden app does not show the post"""
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
        url = "/app/%s/blog/%s" % (app.short_name, blogpost.id)

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

    def test_blogpost_get_one_errors(self):
        """Test blogposts GET non existing posts raises errors"""
        self.register()
        user = db.session.query(User).get(1)
        app1 = model.app.App(name='app1',
                short_name='app1',
                description=u'description')
        app2 = Fixtures.create_app(info=None)
        app1.owner = user
        app2.owner = user
        blogpost = Blogpost(owner=user, app=app1, title='thisisatitle', body='body')
        db.session.add_all([app1, app2, blogpost])
        db.session.commit()

        # To a non-existing app
        url = "/app/non-existing-app/blog/%s" % blogpost.id
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        # To a non-existing post
        url = "/app/%s/blog/999999" % app1.short_name
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        # To an existing post but with an app in the URL it does not belong to
        url = "/app/%s/blog/%s" % (app2.short_name, blogpost.id)
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code


    from pybossa.view.applications import redirect

    @patch('pybossa.view.applications.redirect', wraps=redirect)
    def test_blogpost_create_by_owner(self, mock_redirect):
        """Test blogposts, app owners can create"""
        self.register()
        user = db.session.query(User).get(1)
        app = Fixtures.create_app(info=None)
        app.owner = user
        db.session.add(app)
        db.session.commit()
        url = "/app/%s/blog/new" % app.short_name

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code

        res = self.app.post(url,
                            data={'title':'blogpost title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 200, res.status_code
        mock_redirect.assert_called_with('/app/%s/blog' % app.short_name)

        blogpost = db.session.query(Blogpost).first()
        assert blogpost.title == 'blogpost title', blogpost.title
        assert blogpost.app_id == app.id, blogpost.app.id
        assert blogpost.user_id == user.id, blogpost.user_id


    def test_blogpost_create_by_anonymous(self):
        """Test blogpost create, anonymous users are redirected to signin"""
        user = Fixtures.create_users()[1]
        app = Fixtures.create_app(info=None)
        app.owner = user
        db.session.add_all([user, app])
        db.session.commit()
        url = "/app/%s/blog/new" % app.short_name

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert "Please sign in to access this page" in res.data, res

        res = self.app.post(url,
                            data={'title':'blogpost title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert "Please sign in to access this page" in res.data

        blogpost = db.session.query(Blogpost).first()
        assert blogpost == None, blogpost


    def test_blogpost_create_by_non_owner(self):
        """Test blogpost create by non owner of the app is forbidden"""
        user = Fixtures.create_users()[1]
        app = Fixtures.create_app(info=None)
        app.owner = user
        db.session.add_all([user, app])
        db.session.commit()
        url = "/app/%s/blog/new" % app.short_name
        self.register()

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 403, res.status_code

        res = self.app.post(url,
                            data={'title':'blogpost title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 403, res.status_code


    def test_blogpost_create_errors(self):
        """Test blogposts create for non existing apps raises errors"""
        self.register()
        url = "/app/non-existing-app/blog/new"

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        res = self.app.post(url, data={'title':'blogpost title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 404, res.status_code


    @patch('pybossa.view.applications.redirect', wraps=redirect)
    def test_blogpost_update_by_owner(self, mock_redirect):
        """Test blogposts, app owners can update"""
        self.register()
        user = db.session.query(User).get(1)
        app = Fixtures.create_app(info=None)
        app.owner = user
        blogpost = Blogpost(owner=user, app=app, title='thisisatitle', body='body')
        db.session.add_all([app, blogpost])
        db.session.commit()
        url = "/app/%s/blog/%s/update" % (app.short_name, blogpost.id)

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code

        res = self.app.post(url,
                            data={'id': blogpost.id,
                                  'title':'blogpost title',
                                  'body':'new body'},
                            follow_redirects=True)
        assert res.status_code == 200, res.status_code
        mock_redirect.assert_called_with('/app/%s/blog' % app.short_name)

        blogpost = db.session.query(Blogpost).first()
        print blogpost
        assert blogpost.title == 'blogpost title', blogpost.title
        assert blogpost.body == 'new body', blogpost.body



    def test_blogpost_update_by_anonymous(self):
        """Test blogpost update, anonymous users are redirected to signin"""
        user = Fixtures.create_users()[1]
        app = Fixtures.create_app(info=None)
        app.owner = user
        blogpost = Blogpost(owner=user, app=app, title='thisisatitle', body='body')
        db.session.add_all([user, app, blogpost])
        db.session.commit()
        url = "/app/%s/blog/%s/update" % (app.short_name, blogpost.id)

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert "Please sign in to access this page" in res.data, res.data

        res = self.app.post(url,
                            data={'id':blogpost.id,
                                  'title':'new title',
                                  'body':'new body'},
                            follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert "Please sign in to access this page" in res.data

        blogpost = db.session.query(Blogpost).first()
        assert blogpost.title == 'thisisatitle', blogpost.title


    def test_blogpost_update_by_non_owner(self):
        """Test blogpost update by non owner of the app is forbidden"""
        user = Fixtures.create_users()[1]
        app = Fixtures.create_app(info=None)
        app.owner = user
        blogpost = Blogpost(owner=user, app=app, title='thisisatitle', body='body')
        db.session.add_all([user, app, blogpost])
        db.session.commit()
        url = "/app/%s/blog/%s/update" % (app.short_name, blogpost.id)
        self.register()

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 403, res.status_code

        res = self.app.post(url,
                            data={'title':'new title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 403, res.status_code

        blogpost = db.session.query(Blogpost).first()
        assert blogpost.title == 'thisisatitle', blogpost.title


    def test_blogpost_update_errors(self):
        """Test blogposts update for non existing apps raises errors"""
        self.register()
        user = db.session.query(User).get(1)
        app1 = model.app.App(name='app1',
                short_name='app1',
                description=u'description')
        app2 = Fixtures.create_app(info=None)
        app1.owner = user
        app2.owner = user
        blogpost = Blogpost(owner=user, app=app1, title='thisisatitle', body='body')
        db.session.add_all([app1, app2, blogpost])
        db.session.commit()

        # To a non-existing app
        url = "/app/non-existing-app/blog/%s/update" % blogpost.id
        res = self.app.post(url, data={'title':'new title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 404, res.status_code

        # To a non-existing post
        url = "/app/%s/blog/999999/update" % app1.short_name
        res = self.app.post(url, data={'title':'new title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 404, res.status_code

        # To an existing post but with an app in the URL it does not belong to
        url = "/app/%s/blog/%s/update" % (app2.short_name, blogpost.id)
        res = self.app.post(url, data={'title':'new title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 404, res.status_code






