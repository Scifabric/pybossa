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

from default import Test, db, assert_not_raises #, redis_flushall, assert_not_raises
from pybossa.auth import require
from pybossa.model.blogpost import Blogpost
from pybossa.model.user import User
from pybossa.model.app import App
from nose.tools import assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from mock import patch
from test_authorization import mock_current_user



class TestBlogpostAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)

    def setUp(self):
        super(TestBlogpostAuthorization, self).setUp()
        with self.flask_app.app_context():
            self.create()


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.blogpost.current_user', new=mock_anonymous)
    def test_anonymous_user_create_blogpost(self):
        """Test anonymous users cannot create blogposts"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            blogpost = Blogpost(title='title', app=app, owner=None)

            assert_raises(Unauthorized, getattr(require, 'blogpost').create, blogpost)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.blogpost.current_user', new=mock_admin)
    def test_non_owner_authenticated_user_create_blogpost(self):
        """Test authenticated user cannot create blogpost if is not the app
        owner, even if is admin"""

        with self.flask_app.app_context():
            app = db.session.query(App).first()
            root = db.session.query(User).first()
            blogpost = Blogpost(title='title', app=app, owner=root)
            print blogpost

            assert_raises(Forbidden, getattr(require, 'blogpost').create, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_create_blogpost(self):
        """Test authenticated user can create blogpost if is app owner"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            # User.id == 1 is root, so getting user1
            user1 = db.session.query(User).get(2)
            blogpost = Blogpost(title='title', app=app, owner=user1)

            assert_not_raises(Exception, getattr(require, 'blogpost').create, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_create_blogpost_as_other_user(self):
        """Test authenticated user cannot create blogpost if is app owner but
        sets another person as the author of the blogpost"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            user2 = db.session.query(User).get(3)
            blogpost = Blogpost(title='title', app=app, owner=user2)

            assert_raises(Forbidden, getattr(require, 'blogpost').create, blogpost)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.blogpost.current_user', new=mock_anonymous)
    def test_anonymous_user_read_blogpost(self):
        """Test anonymous users can read blogposts"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            blogpost = Blogpost(title='title', app=app, owner=None)
            db.session.add(blogpost)
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').read, blogpost)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.blogpost.current_user', new=mock_admin)
    def test_non_owner_authenticated_user_read_blogpost(self):
        """Test authenticated user can read blogpost if is not the app owner"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            root = db.session.query(User).first()
            blogpost = Blogpost(title='title', app=app, owner=root)
            db.session.add(blogpost)
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').read, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_read_blogpost(self):
        """Test authenticated user can read blogpost if is the app owner"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            user1 = db.session.query(User).get(2)
            blogpost = Blogpost(title='title', app=app, owner=user1)
            db.session.add(blogpost)
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').read, blogpost)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.blogpost.current_user', new=mock_anonymous)
    def test_anonymous_user_update_blogpost(self):
        """Test anonymous users cannot update blogposts"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            blogpost = Blogpost(title='title', app=app, owner=None)
            db.session.add(blogpost)
            db.session.commit()

            assert_raises(Unauthorized, getattr(require, 'blogpost').update, blogpost)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.blogpost.current_user', new=mock_admin)
    def test_non_owner_authenticated_user_update_blogpost(self):
        """Test authenticated user cannot update a blogpost if is not the post
        owner, even if is admin"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            user1 = db.session.query(User).get(2)
            blogpost = Blogpost(title='title', app=app, owner=user1)
            db.session.add(blogpost)
            db.session.commit()

            assert_raises(Forbidden, getattr(require, 'blogpost').update, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_update_blogpost(self):
        """Test authenticated user can update blogpost if is the post owner"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            user1 = db.session.query(User).get(2)
            blogpost = Blogpost(title='title', app=app, owner=user1)
            db.session.add(blogpost)
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').update, blogpost)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.blogpost.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_blogpost(self):
        """Test anonymous users cannot delete blogposts"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            blogpost = Blogpost(title='title', app=app, owner=None)
            db.session.add(blogpost)
            db.session.commit()

            assert_raises(Unauthorized, getattr(require, 'blogpost').delete, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_delete_blogpost(self):
        """Test authenticated user cannot delete a blogpost if is not the post
        owner or is not admin"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            root = db.session.query(User).get(1)
            blogpost = Blogpost(title='title', app=app, owner=root)
            db.session.add(blogpost)
            db.session.commit()

            assert_raises(Forbidden, getattr(require, 'blogpost').delete, blogpost)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_delete_blogpost(self):
        """Test authenticated user can delete blogpost if is the post owner"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            user1 = db.session.query(User).get(2)
            blogpost = Blogpost(title='title', app=app, owner=user1)
            db.session.add(blogpost)
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').delete, blogpost)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.blogpost.current_user', new=mock_admin)
    def test_admin_authenticated_user_delete_blogpost(self):
        """Test authenticated user can delete a blogpost if is admin"""

        with self.flask_app.test_request_context('/'):
            app = db.session.query(App).first()
            user1 = db.session.query(User).get(2)
            blogpost = Blogpost(title='title', app=app, owner=user1)
            db.session.add(blogpost)
            db.session.commit()

            assert_not_raises(Exception, getattr(require, 'blogpost').delete, blogpost)
