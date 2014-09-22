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
from default import db, with_context, Test
from factories import AppFactory, BlogpostFactory
from mock import patch

from pybossa.repositories import BlogRepository
from pybossa.repositories import UserRepository
blog_repo = BlogRepository(db)
user_repo = UserRepository(db)




class TestBlogpostView(web.Helper):

    def test_blogposts_get_all(self):
        """Test blogpost GET all blogposts"""
        user = self.create_users()[1]
        app = AppFactory.create(owner=user)
        blogpost_1 = BlogpostFactory.create(owner=user, app=app, title='titleone')
        blogpost_2 = BlogpostFactory.create(owner=user, app=app, title='titletwo')
        url = "/app/%s/blog" % app.short_name

        # As anonymous
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'titleone' in res.data
        assert 'titletwo' in res.data

        # As authenticated
        self.register()
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'titleone' in res.data
        assert 'titletwo' in res.data


    def test_blogposts_get_all_with_hidden_app(self):
        """Test blogpost GET does not show hidden projects"""
        self.register()
        admin = user_repo.get(1)
        self.signout()
        self.register(name='user', email='user@user.com')
        user = user_repo.get(2)
        app = AppFactory.create(owner=user, hidden=1)
        blogpost = BlogpostFactory.create(app=app, title='title', body='body')
        url = "/app/%s/blog" % app.short_name

        # As app owner
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'title' in res.data

        # As authenticated
        self.signout()
        self.register(name='notowner', email='user2@user.com')
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
        assert 'title' in res.data


    def test_blogpost_get_all_errors(self):
        """Test blogpost GET all raises error if the project does not exist"""
        url = "/app/non-existing-app/blog"

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code


    def test_blogpost_get_one(self):
        """Test blogpost GET with id shows one blogpost"""
        user = self.create_users()[1]
        app = AppFactory.create(owner=user)
        blogpost = BlogpostFactory.create(app=app, title='title', body='body')
        url = "/app/%s/%s" % (app.short_name, blogpost.id)

        # As anonymous
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'title' in res.data

        # As authenticated
        self.register()
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'title' in res.data


    def test_blogpost_get_one_with_hidden_app(self):
        """Test blogpost GET a given post id with hidden project does not show the post"""
        self.register()
        admin = user_repo.get(1)
        self.signout()
        self.register(name='user', email='user@user.com')
        user = user_repo.get(2)
        app = AppFactory.create(owner=user, hidden=1)
        blogpost = BlogpostFactory.create(app=app, title='title', body='body')
        url = "/app/%s/%s" % (app.short_name, blogpost.id)

        # As app owner
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'title' in res.data

        # As authenticated
        self.signout()
        self.register(name='notowner', email='user2@user.com')
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
        assert 'title' in res.data


    def test_blogpost_get_one_errors(self):
        """Test blogposts GET non existing posts raises errors"""
        self.register()
        user = user_repo.get(1)
        app1, app2 = AppFactory.create_batch(2, owner=user)
        blogpost = BlogpostFactory.create(app=app1, title='title', body='body')

        # To a non-existing app
        url = "/app/non-existing-app/%s" % blogpost.id
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        # To a non-existing post
        url = "/app/%s/999999" % app1.short_name
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        # To an existing post but with a project in the URL it does not belong to
        url = "/app/%s/%s" % (app2.short_name, blogpost.id)
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code


    from pybossa.view.applications import redirect

    @patch('pybossa.view.applications.redirect', wraps=redirect)
    def test_blogpost_create_by_owner(self, mock_redirect):
        """Test blogposts, project owners can create"""
        self.register()
        user = user_repo.get(1)
        app = AppFactory.create(owner=user)
        url = "/app/%s/new-blogpost" % app.short_name

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code

        res = self.app.post(url,
                            data={'title':'blogpost title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 200, res.status_code
        mock_redirect.assert_called_with('/app/%s/blog' % app.short_name)

        blogpost = blog_repo.get_by(title='blogpost title')
        assert blogpost.title == 'blogpost title', blogpost.title
        assert blogpost.app_id == app.id, blogpost.app.id
        assert blogpost.user_id == user.id, blogpost.user_id


    def test_blogpost_create_by_anonymous(self):
        """Test blogpost create, anonymous users are redirected to signin"""
        app = AppFactory.create()
        url = "/app/%s/new-blogpost" % app.short_name

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert "Please sign in to access this page" in res.data, res

        res = self.app.post(url,
                            data={'title':'blogpost title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert "Please sign in to access this page" in res.data

        blogpost = blog_repo.get_by(title='blogpost title')
        assert blogpost == None, blogpost


    def test_blogpost_create_by_non_owner(self):
        """Test blogpost create by non owner of the project is forbidden"""

        self.register()
        user = user_repo.get(1)
        app = AppFactory.create(owner=user)
        url = "/app/%s/new-blogpost" % app.short_name
        self.signout()
        self.register(name='notowner', email='user2@user.com')

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 403, res.status_code

        res = self.app.post(url,
                            data={'title':'blogpost title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 403, res.status_code


    def test_blogpost_create_errors(self):
        """Test blogposts create for non existing projects raises errors"""
        self.register()
        url = "/app/non-existing-app/new-blogpost"

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        res = self.app.post(url, data={'title':'blogpost title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 404, res.status_code


    @patch('pybossa.view.applications.redirect', wraps=redirect)
    def test_blogpost_update_by_owner(self, mock_redirect):
        """Test blogposts, project owners can update"""
        self.register()
        user = user_repo.get(1)
        app = AppFactory.create(owner=user)
        blogpost = BlogpostFactory.create(app=app, title='title', body='body')
        url = "/app/%s/%s/update" % (app.short_name, blogpost.id)

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code

        res = self.app.post(url,
                            data={'id': blogpost.id,
                                  'title':'blogpost title',
                                  'body':'new body'},
                            follow_redirects=True)
        assert res.status_code == 200, res.status_code
        mock_redirect.assert_called_with('/app/%s/blog' % app.short_name)

        blogpost = blog_repo.get_by(title='blogpost title')
        assert blogpost.title == 'blogpost title', blogpost.title
        assert blogpost.body == 'new body', blogpost.body



    def test_blogpost_update_by_anonymous(self):
        """Test blogpost update, anonymous users are redirected to signin"""
        app = AppFactory.create()
        blogpost = BlogpostFactory.create(app=app, title='title', body='body')
        url = "/app/%s/%s/update" % (app.short_name, blogpost.id)

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

        blogpost = blog_repo.get_by()
        assert blogpost.title == 'title', blogpost.title


    @with_context
    def test_blogpost_update_by_non_owner(self):
        """Test blogpost update by non owner of the project is forbidden"""
        self.register()
        user = user_repo.get(1)
        app = AppFactory.create(owner=user)
        blogpost = BlogpostFactory.create(app=app, title='title', body='body')
        url = "/app/%s/new-blogpost" % app.short_name
        self.signout()
        self.register(name='notowner', email='user2@user.com')
        url = "/app/%s/%s/update" % (app.short_name, blogpost.id)

        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 403, res.status_code

        res = self.app.post(url,
                            data={'title':'new title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 403, res.status_code

        blogpost = blog_repo.get_by()
        assert blogpost.title == 'title', blogpost.title


    def test_blogpost_update_errors(self):
        """Test blogposts update for non existing projects raises errors"""
        self.register()
        user = user_repo.get(1)
        app1 = AppFactory.create(owner=user)
        app2 = AppFactory.create(owner=user)
        blogpost = BlogpostFactory.create(app=app1, title='title', body='body')

        # To a non-existing app
        url = "/app/non-existing-app/%s/update" % blogpost.id
        res = self.app.post(url, data={'title':'new title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 404, res.status_code

        # To a non-existing post
        url = "/app/%s/999999/update" % app1.short_name
        res = self.app.post(url, data={'title':'new title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 404, res.status_code

        # To an existing post but with a project in the URL it does not belong to
        url = "/app/%s/%s/update" % (app2.short_name, blogpost.id)
        res = self.app.post(url, data={'title':'new title', 'body':'body'},
                            follow_redirects=True)
        assert res.status_code == 404, res.status_code


    @patch('pybossa.view.applications.redirect', wraps=redirect)
    def test_blogpost_delete_by_owner(self, mock_redirect):
        """Test blogposts, project owner can delete"""
        self.register()
        user = user_repo.get(1)
        app = AppFactory.create(owner=user)
        blogpost = BlogpostFactory.create(app=app, title='title', body='body')
        url = "/app/%s/%s/delete" % (app.short_name, blogpost.id)
        redirect_url = '/app/%s/blog' % app.short_name

        res = self.app.post(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        mock_redirect.assert_called_with(redirect_url)

        blogpost = blog_repo.get_by(title='title')
        assert blogpost is None, blogpost



    def test_blogpost_delete_by_anonymous(self):
        """Test blogpost delete, anonymous users are redirected to signin"""
        app = AppFactory.create()
        blogpost = BlogpostFactory.create(app=app, title='title', body='body')
        url = "/app/%s/%s/delete" % (app.short_name, blogpost.id)

        res = self.app.post(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert "Please sign in to access this page" in res.data

        blogpost = blog_repo.get_by()
        assert blogpost is not None


    @with_context
    def test_blogpost_delete_by_non_owner(self):
        """Test blogpost delete by non owner of the project is forbidden"""
        self.register()
        user = user_repo.get(1)
        app = AppFactory.create(owner=user)
        blogpost = BlogpostFactory.create(app=app, title='title', body='body')
        url = "/app/%s/new-blogpost" % app.short_name
        self.signout()
        url = "/app/%s/%s/delete" % (app.short_name, blogpost.id)
        self.register(name='notowner', email='user2@user.com')

        res = self.app.post(url, follow_redirects=True)
        assert res.status_code == 403, res.status_code

        blogpost = blog_repo.get_by()
        assert blogpost is not None


    def test_blogpost_delete_errors(self):
        """Test blogposts delete for non existing projects raises errors"""
        self.register()
        user = user_repo.get(1)
        app1 = AppFactory.create(owner=user)
        app2 = AppFactory.create(owner=user)
        blogpost = BlogpostFactory.create(app=app1, title='title', body='body')

        # To a non-existing app
        url = "/app/non-existing-app/%s/delete" % blogpost.id
        res = self.app.post(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        # To a non-existing post
        url = "/app/%s/999999/delete" % app1.short_name
        res = self.app.post(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        # To an existing post but with a project in the URL it does not belong to
        url = "/app/%s/%s/delete" % (app2.short_name, blogpost.id)
        res = self.app.post(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code
