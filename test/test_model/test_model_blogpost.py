# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.

from default import Test, db, with_context, assert_not_raises
from nose.tools import raises, assert_raises
from sqlalchemy.exc import IntegrityError, DataError
from pybossa.model.project import Project
from pybossa.model.user import User
from pybossa.model.category import Category
from pybossa.model.blogpost import Blogpost


class TestBlogpostModel(Test):

    def setUp(self):
        super(TestBlogpostModel, self).setUp()
        with self.flask_app.app_context():
            user = User(email_addr="john.doe@example.com",
                        name="johndoe",
                        fullname="John Doe",
                        locale="en")
            category = Category(name='cat', short_name='cat', description='cat')
            project = Project(name='Application', short_name='app', description='desc',
                      owner=user, category=category)
            db.session.add(user)
            db.session.add(project)
            db.session.commit()

    def configure_fixtures(self):
        self.project = db.session.query(Project).first()
        self.user = db.session.query(User).first()


    @with_context
    def test_blogpost_title_length(self):
        """Test BLOGPOST model title length has a limit"""
        self.configure_fixtures()
        valid_title = 'a' * 255
        invalid_title = 'a' * 256
        blogpost = Blogpost(title=valid_title, body="body", project=self.project)
        db.session.add(blogpost)

        assert_not_raises(DataError, db.session.commit)

        blogpost.title = invalid_title
        assert_raises(DataError, db.session.commit)

    @with_context
    def test_blogpost_title_presence(self):
        """Test BLOGPOST a blogpost must have a title"""
        self.configure_fixtures()
        blogpost = Blogpost(title=None, body="body", project=self.project)
        db.session.add(blogpost)

        assert_raises(IntegrityError, db.session.commit)

    @with_context
    def test_blogpost_body_presence(self):
        """Test BLOGPOST a blogpost must have a body"""
        self.configure_fixtures()
        blogpost = Blogpost(title='title', body=None, project=self.project)
        db.session.add(blogpost)

        assert_raises(IntegrityError, db.session.commit)

    @with_context
    def test_blogpost_belongs_to_project(self):
        """Test BLOGPOSTS must belong to a project"""
        self.configure_fixtures()
        blogpost = Blogpost(title='title', body="body", project=None)

    @with_context
    def test_blogpost_belongs_to_project(self):
        """Test BLOGPOSTS must belong to a project"""
        self.configure_fixtures()
        blogpost = Blogpost(title='title', project=None)
        db.session.add(blogpost)

        assert_raises(IntegrityError, db.session.commit)

    @with_context
    def test_blogpost_is_deleted_after_project_deletion(self):
        """Test BLOGPOST no blogposts can exist after its project has been removed"""
        self.configure_fixtures()
        blogpost = Blogpost(title='title', body="body", project=self.project)
        db.session.add(blogpost)
        db.session.commit()

        assert self.project in db.session
        assert blogpost in db.session

        db.session.delete(self.project)
        db.session.commit()
        assert self.project not in db.session
        assert blogpost not in db.session

    @with_context
    def test_blogpost_deletion_doesnt_delete_project(self):
        """Test BLOGPOST when deleting a blogpost its parent project is not affected"""
        self.configure_fixtures()
        blogpost = Blogpost(title='title', body="body", project=self.project)
        db.session.add(blogpost)
        db.session.commit()

        assert self.project in db.session
        assert blogpost in db.session

        db.session.delete(blogpost)
        db.session.commit()
        assert self.project in db.session
        assert blogpost not in db.session

    @with_context
    def test_blogpost_owner_is_nullable(self):
        """Test BLOGPOST a blogpost owner can be none
        (if the user is removed from the system)"""
        self.configure_fixtures()
        blogpost = Blogpost(title='title', body="body", project=self.project, owner=None)
        db.session.add(blogpost)

        assert_not_raises(IntegrityError, db.session.commit)

    @with_context
    def test_blogpost_is_not_deleted_after_owner_deletion(self):
        """Test BLOGPOST a blogpost remains when its owner user is removed
        from the system"""
        self.configure_fixtures()
        owner = User(
            email_addr="john.doe2@example.com",
            name="johndoe2",
            fullname="John Doe2",
            locale="en")
        blogpost = Blogpost(title='title', body="body", project=self.project, owner=owner)
        db.session.add(blogpost)
        db.session.commit()

        assert owner in db.session
        assert blogpost in db.session

        db.session.delete(owner)
        db.session.commit()
        assert owner not in db.session
        assert blogpost in db.session
        assert blogpost.owner == None, blogpost.owner

    @with_context
    def test_blogpost_public_json(self):
        """Test BLOGPOST to public json works."""
        self.configure_fixtures()
        owner = User(
            email_addr="john.doe2@example.com",
            name="johndoe2",
            fullname="John Doe2",
            locale="en")
        blogpost = Blogpost(title='title', body="body", project=self.project, owner=owner)
        db.session.add(blogpost)
        db.session.commit()

        tmp = blogpost.to_public_json()
        assert list(tmp.keys()).sort() == Blogpost().public_attributes().sort()
        assert Blogpost().public_info_keys() == []
