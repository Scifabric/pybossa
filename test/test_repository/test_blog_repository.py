# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
# Cache global variables for timeouts

from default import Test, db
from nose.tools import assert_raises
from factories import BlogpostFactory
from pybossa.repositories import BlogRepository
from pybossa.exc import WrongObjectError, DBIntegrityError



class TestBlogRepository(Test):

    def setUp(self):
        super(TestBlogRepository, self).setUp()
        self.blog_repo = BlogRepository(db)


    def test_get_return_none_if_no_blogpost(self):
        """Test get method returns None if there is no blogpost with the
        specified id"""

        blogpost = self.blog_repo.get(2)

        assert blogpost is None, blogpost


    def test_get_returns_blogpost(self):
        """Test get method returns a blogpost if exists"""

        blogpost = BlogpostFactory.create()

        retrieved_blogpost = self.blog_repo.get(blogpost.id)

        assert blogpost == retrieved_blogpost, retrieved_blogpost


    def test_get_by(self):
        """Test get_by returns a blogpost with the specified attribute"""

        blogpost = BlogpostFactory.create(title='My blog', body='myblogpost')

        retrieved_blogpost = self.blog_repo.get_by(title=blogpost.title)

        assert blogpost == retrieved_blogpost, retrieved_blogpost


    def test_get_by_returns_none_if_no_blogpost(self):
        """Test get_by returns None if no blogpost matches the query"""

        BlogpostFactory.create(title='My blog', body='myblogpost')

        blogpost = self.blog_repo.get_by(title='notitle')

        assert blogpost is None, blogpost


    def test_filter_by_no_matches(self):
        """Test filter_by returns an empty list if no blogposts match the query"""

        BlogpostFactory.create(title='My blog', body='myblogpost')

        retrieved_blogposts = self.blog_repo.filter_by(title='no title')

        assert isinstance(retrieved_blogposts, list)
        assert len(retrieved_blogposts) == 0, retrieved_blogposts


    def test_filter_by_one_condition(self):
        """Test filter_by returns a list of blogposts that meet the filtering
        condition"""

        BlogpostFactory.create_batch(3, title='my blogpost')
        should_be_missing = BlogpostFactory.create(title='another blogpost')

        retrieved_blogposts = self.blog_repo.filter_by(title='my blogpost')

        assert len(retrieved_blogposts) == 3, retrieved_blogposts
        assert should_be_missing not in retrieved_blogposts, retrieved_blogposts


    def test_filter_by_multiple_conditions(self):
        """Test filter_by supports multiple-condition queries"""

        BlogpostFactory.create(title='my blogpost', body='body')
        blogpost = BlogpostFactory.create(title='my blogpost', body='other body')

        retrieved_blogposts = self.blog_repo.filter_by(title='my blogpost',
                                                       body='other body')

        assert len(retrieved_blogposts) == 1, retrieved_blogposts
        assert blogpost in retrieved_blogposts, retrieved_blogposts


    def test_save(self):
        """Test save persist the blogpost"""

        blogpost = BlogpostFactory.build()
        assert self.blog_repo.get(blogpost.id) is None

        self.blog_repo.save(blogpost)

        assert self.blog_repo.get(blogpost.id) == blogpost, "Blogpost not saved"


    def test_save_fails_if_integrity_error(self):
        """Test save raises a DBIntegrityError if the instance to be saved lacks
        a required value"""

        blogpost = BlogpostFactory.build(title=None)

        assert_raises(DBIntegrityError, self.blog_repo.save, blogpost)


    def test_save_only_saves_blogposts(self):
        """Test save raises a WrongObjectError when an object which is not
        a Blogpost instance is saved"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.blog_repo.save, bad_object)


    def test_update(self):
        """Test update persists the changes made to the blogpost"""

        blogpost = BlogpostFactory.create(body='this is a blogpost')
        blogpost.body = 'new content'

        self.blog_repo.update(blogpost)
        updated_blogpost = self.blog_repo.get(blogpost.id)

        assert updated_blogpost.body == 'new content', updated_blogpost


    def test_update_fails_if_integrity_error(self):
        """Test update raises a DBIntegrityError if the instance to be updated
        lacks a required value"""

        blogpost = BlogpostFactory.create()
        blogpost.title = None

        assert_raises(DBIntegrityError, self.blog_repo.update, blogpost)


    def test_update_only_updates_blogposts(self):
        """Test update raises a WrongObjectError when an object which is not
        a Project (App) instance is updated"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.blog_repo.update, bad_object)


    def test_delete(self):
        """Test delete removes the blogpost instance"""

        blogpost = BlogpostFactory.create()

        self.blog_repo.delete(blogpost)
        deleted = self.blog_repo.get(blogpost.id)

        assert deleted is None, deleted


    def test_delete_only_deletes_blogposts(self):
        """Test delete raises a WrongObjectError if is requested to delete other
        than a blogpost"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.blog_repo.delete, bad_object)
