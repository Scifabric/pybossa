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

from base import web, model, Fixtures, db, redis_flushall, assert_not_raises
from pybossa.auth import require
from nose.tools import assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from mock import patch
from test_authorization import mock_current_user



class TestBlogpostAuthorization:

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)

    def setUp(self):
        model.rebuild_db()
        self.root, self.user1, self.user2 = Fixtures.create_users()
        self.app = Fixtures.create_app('')
        self.app.owner = self.user1
        db.session.add_all([self.root, self.user1, self.user2, self.app])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        redis_flushall()


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.blogpost.current_user', new=mock_anonymous)
    def test_anonymous_user_create_blogpost(self):
        """Test anonymous users cannot create blogposts"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=None)

            assert_raises(Unauthorized, getattr(require, 'blogpost').create, blogpost)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.blogpost.current_user', new=mock_admin)
    def test_non_owner_authenticated_user_create_blogpost(self):
        """Test authenticated user cannot create blogpost if is not the app
        owner, even if is admin"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=self.root)

            assert_raises(Forbidden, getattr(require, 'blogpost').create, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_create_blogpost(self):
        """Test authenticated user can create blogpost if is app owner"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=self.user1)

            assert_not_raises(Exception, getattr(require, 'blogpost').create, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_create_blogpost_as_other_user(self):
        """Test authenticated user cannot create blogpost if is app owner but
        sets another person as the author of the blogpost"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=self.user2)

            assert_raises(Forbidden, getattr(require, 'blogpost').create, blogpost)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.blogpost.current_user', new=mock_anonymous)
    def test_anonymous_user_read_blogpost(self):
        """Test anonymous users can read blogposts"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=None)
            db.session.add(blogpost)
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').read, blogpost)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.blogpost.current_user', new=mock_admin)
    def test_non_owner_authenticated_user_read_blogpost(self):
        """Test authenticated user can read blogpost if is not the app owner"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=self.root)
            db.session.add(blogpost)
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').read, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_read_blogpost(self):
        """Test authenticated user can read blogpost if is the app owner"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=self.user1)
            db.session.add(blogpost)
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').read, blogpost)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.blogpost.current_user', new=mock_anonymous)
    def test_anonymous_user_update_blogpost(self):
        """Test anonymous users cannot update blogposts"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=None)
            db.session.add(blogpost)
            db.session.commit()

            assert_raises(Unauthorized, getattr(require, 'blogpost').update, blogpost)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.blogpost.current_user', new=mock_admin)
    def test_non_owner_authenticated_user_update_blogpost(self):
        """Test authenticated user cannot update a blogpost if is not the post
        owner, even if is admin"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=self.user1)
            db.session.add(blogpost)
            db.session.commit()

            assert_raises(Forbidden, getattr(require, 'blogpost').update, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_update_blogpost(self):
        """Test authenticated user can update blogpost if is the post owner"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=self.user1)
            db.session.add(blogpost)
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').update, blogpost)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.blogpost.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_blogpost(self):
        """Test anonymous users cannot delete blogposts"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=None)
            db.session.add(blogpost)
            db.session.commit()

            assert_raises(Unauthorized, getattr(require, 'blogpost').delete, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_delete_blogpost(self):
        """Test authenticated user cannot delete a blogpost if is not the post
        owner or is not admin"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=self.root)
            db.session.add(blogpost)
            db.session.commit()

            assert_raises(Forbidden, getattr(require, 'blogpost').delete, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_delete_blogpost(self):
        """Test authenticated user can delete blogpost if is the post owner"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=self.user1)
            db.session.add(blogpost)
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').delete, blogpost)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.blogpost.current_user', new=mock_admin)
    def test_admin_authenticated_user_delete_blogpost(self):
        """Test authenticated user can delete a blogpost if is admin"""

        with web.app.test_request_context('/'):
            blogpost = model.blogpost.Blogpost(title='title', app=self.app, owner=self.user1)
            db.session.add(blogpost)
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').delete, blogpost)
