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

from base import model, db, assert_not_raises
from nose.tools import raises, assert_raises
from sqlalchemy.exc import IntegrityError, DataError


class TestBlogpostModel:

    def setUp(self):
        model.rebuild_db()
        self.user = model.User(
            email_addr="john.doe@example.com",
            name="johndoe",
            fullname="John Doe",
            locale="en")
        self.app = model.App(
            name='Application',
            short_name='app',
            description='desc',
            owner=self.user)
        db.session.add(self.user)
        db.session.add(self.app)
        db.session.commit()

    def tearDown(self):
        db.session.remove()


    def test_blogpost_title_length(self):
        valid_title = 'a' * 255
        invalid_title = 'a' * 256
        blogpost = model.Blogpost(title=valid_title, body="body", app=self.app)
        db.session.add(blogpost)

        assert_not_raises(DataError, db.session.commit)

        blogpost.title = invalid_title
        assert_raises(DataError, db.session.commit)

    def test_blogpost_belongs_to_app(self):
        blogpost = model.Blogpost(title='title', app = None)
        db.session.add(blogpost)

        assert_raises(IntegrityError, db.session.commit)

    def test_blogpost_is_deleted_after_app_deletion(self):
        blogpost = model.Blogpost(title='title', app=self.app)
        db.session.add(blogpost)
        db.session.commit()

        assert self.app in db.session
        assert blogpost in db.session

        db.session.delete(self.app)
        db.session.commit()
        assert self.app not in db.session
        assert blogpost not in db.session

    def test_blogpost_deletion_doesnt_delete_app(self):
        blogpost = model.Blogpost(title='title', app=self.app)
        db.session.add(blogpost)
        db.session.commit()

        assert self.app in db.session
        assert blogpost in db.session

        db.session.delete(blogpost)
        db.session.commit()
        assert self.app in db.session
        assert blogpost not in db.session

    def test_blogpost_owner_is_nullable(self):
        blogpost = model.Blogpost(title='title', app=self.app, owner=None)
        db.session.add(blogpost)

        assert_not_raises(IntegrityError, db.session.commit)

    def test_blogpost_is_not_deleted_after_owner_deletion(self):
        owner = model.User(
            email_addr="john.doe2@example.com",
            name="johndoe2",
            fullname="John Doe2",
            locale="en")
        blogpost = model.Blogpost(title='title', app=self.app, owner=owner)
        db.session.add(blogpost)
        db.session.commit()

        assert owner in db.session
        assert blogpost in db.session

        db.session.delete(owner)
        db.session.commit()
        assert owner not in db.session
        assert blogpost in db.session
        assert blogpost.owner == None, blogpost.owner
