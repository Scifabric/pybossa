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

from default import Test, db, with_context, assert_not_raises
from nose.tools import raises, assert_raises
from sqlalchemy.exc import IntegrityError, DataError
from pybossa.model.app import App
from pybossa.model.user import User
from pybossa.model.blogpost import Blogpost


class TestBlogpostModel(Test):

    def setUp(self):
        super(TestBlogpostModel, self).setUp()
        with self.flask_app.app_context():
            user = User(email_addr="john.doe@example.com",
                        name="johndoe",
                        fullname="John Doe",
                        locale="en")
            app = App(
                name='Application',
                short_name='app',
                description='desc',
                owner=user)
            db.session.add(user)
            db.session.add(app)
            db.session.commit()

    def configure_fixtures(self):
        self.app = db.session.query(App).first()
        self.user = db.session.query(User).first()


    @with_context
    def test_blogpost_title_length(self):
        """Test BLOGPOST model title length has a limit"""
        self.configure_fixtures()
        valid_title = 'a' * 255
        invalid_title = 'a' * 256
        blogpost = Blogpost(title=valid_title, body="body", app=self.app)
        db.session.add(blogpost)

        assert_not_raises(DataError, db.session.commit)

        blogpost.title = invalid_title
        assert_raises(DataError, db.session.commit)

    @with_context
    def test_blogpost_title_presence(self):
        """Test BLOGPOST a blogpost must have a title"""
        self.configure_fixtures()
        blogpost = Blogpost(title=None, body="body", app=self.app)
        db.session.add(blogpost)

        assert_raises(IntegrityError, db.session.commit)

    @with_context
    def test_blogpost_body_presence(self):
        """Test BLOGPOST a blogpost must have a body"""
        self.configure_fixtures()
        blogpost = Blogpost(title='title', body=None, app=self.app)
        db.session.add(blogpost)

        assert_raises(IntegrityError, db.session.commit)

    @with_context
    def test_blogpost_belongs_to_app(self):
        """Test BLOGPOSTS must belong to a project"""
        self.configure_fixtures()
        blogpost = Blogpost(title='title', body="body", app=None)

    @with_context
    def test_blogpost_belongs_to_app(self):
        """Test BLOGPOSTS must belong to a project"""
        self.configure_fixtures()
        blogpost = Blogpost(title='title', app = None)
        db.session.add(blogpost)

        assert_raises(IntegrityError, db.session.commit)

    @with_context
    def test_blogpost_is_deleted_after_app_deletion(self):
        """Test BLOGPOST no blogposts can exist after it's project has been removed"""
        self.configure_fixtures()
        blogpost = Blogpost(title='title', body="body", app=self.app)
        db.session.add(blogpost)
        db.session.commit()

        assert self.app in db.session
        assert blogpost in db.session

        db.session.delete(self.app)
        db.session.commit()
        assert self.app not in db.session
        assert blogpost not in db.session

    @with_context
    def test_blogpost_deletion_doesnt_delete_app(self):
        """Test BLOGPOST when deleting a blogpost it's parent project is not affected"""
        self.configure_fixtures()
        blogpost = Blogpost(title='title', body="body", app=self.app)
        db.session.add(blogpost)
        db.session.commit()

        assert self.app in db.session
        assert blogpost in db.session

        db.session.delete(blogpost)
        db.session.commit()
        assert self.app in db.session
        assert blogpost not in db.session

    @with_context
    def test_blogpost_owner_is_nullable(self):
        """Test BLOGPOST a blogpost owner can be none
        (if the user is removed from the system)"""
        self.configure_fixtures()
        blogpost = Blogpost(title='title', body="body", app=self.app, owner=None)
        db.session.add(blogpost)

        assert_not_raises(IntegrityError, db.session.commit)

    @with_context
    def test_blogpost_is_not_deleted_after_owner_deletion(self):
        """Test BLOGPOST a blogpost remains when it's owner user is removed
        from the system"""
        self.configure_fixtures()
        owner = User(
            email_addr="john.doe2@example.com",
            name="johndoe2",
            fullname="John Doe2",
            locale="en")
        blogpost = Blogpost(title='title', body="body", app=self.app, owner=owner)
        db.session.add(blogpost)
        db.session.commit()

        assert owner in db.session
        assert blogpost in db.session

        db.session.delete(owner)
        db.session.commit()
        assert owner not in db.session
        assert blogpost in db.session
        assert blogpost.owner == None, blogpost.owner
