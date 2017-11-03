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
# Cache global variables for timeouts

from mock import patch
from default import Test, db, with_context
from nose.tools import assert_raises
from factories import BlogpostFactory
from pybossa.repositories import BlogRepository
from pybossa.exc import WrongObjectError, DBIntegrityError



class TestBlogRepository(Test):

    def setUp(self):
        super(TestBlogRepository, self).setUp()
        self.blog_repo = BlogRepository(db)

    @with_context
    def test_get_return_none_if_no_blogpost(self):
        """Test get method returns None if there is no blogpost with the
        specified id"""

        blogpost = self.blog_repo.get(2)

        assert blogpost is None, blogpost


    @with_context
    def test_get_returns_blogpost(self):
        """Test get method returns a blogpost if exists"""

        blogpost = BlogpostFactory.create()

        retrieved_blogpost = self.blog_repo.get(blogpost.id)

        assert blogpost == retrieved_blogpost, retrieved_blogpost


    @with_context
    def test_get_by(self):
        """Test get_by returns a blogpost with the specified attribute"""

        blogpost = BlogpostFactory.create(title='My blog', body='myblogpost')

        retrieved_blogpost = self.blog_repo.get_by(title=blogpost.title)

        assert blogpost == retrieved_blogpost, retrieved_blogpost


    @with_context
    def test_get_by_returns_none_if_no_blogpost(self):
        """Test get_by returns None if no blogpost matches the query"""

        BlogpostFactory.create(title='My blog', body='myblogpost')

        blogpost = self.blog_repo.get_by(title='notitle')

        assert blogpost is None, blogpost


    @with_context
    def test_filter_by_no_matches(self):
        """Test filter_by returns an empty list if no blogposts match the query"""

        BlogpostFactory.create(title='My blog', body='myblogpost')

        retrieved_blogposts = self.blog_repo.filter_by(title='no title')

        assert isinstance(retrieved_blogposts, list)
        assert len(retrieved_blogposts) == 0, retrieved_blogposts


    @with_context
    def test_filter_by_one_condition(self):
        """Test filter_by returns a list of blogposts that meet the filtering
        condition"""

        BlogpostFactory.create_batch(3, title='my blogpost')
        should_be_missing = BlogpostFactory.create(title='another blogpost')

        retrieved_blogposts = self.blog_repo.filter_by(title='my blogpost')

        assert len(retrieved_blogposts) == 3, retrieved_blogposts
        assert should_be_missing not in retrieved_blogposts, retrieved_blogposts


    @with_context
    def test_filter_by_limit_offset(self):
        """Test that filter_by supports limit and offset options"""

        BlogpostFactory.create_batch(4)
        all_blogposts = self.blog_repo.filter_by()

        first_two = self.blog_repo.filter_by(limit=2)
        last_two = self.blog_repo.filter_by(limit=2, offset=2)

        assert len(first_two) == 2, first_two
        assert len(last_two) == 2, last_two
        assert first_two == all_blogposts[:2]
        assert last_two == all_blogposts[2:]


    @with_context
    def test_filter_by_multiple_conditions(self):
        """Test filter_by supports multiple-condition queries"""

        BlogpostFactory.create(title='my blogpost', body='body')
        blogpost = BlogpostFactory.create(title='my blogpost', body='other body')

        retrieved_blogposts = self.blog_repo.filter_by(title='my blogpost',
                                                       body='other body')

        assert len(retrieved_blogposts) == 1, retrieved_blogposts
        assert blogpost in retrieved_blogposts, retrieved_blogposts

    @with_context

    @with_context
    @patch('pybossa.repositories.blog_repository.clean_project')
    def test_save(self, clean_project_mock):
        """Test save persist the blogpost"""

        blogpost = BlogpostFactory.build()
        assert self.blog_repo.get(blogpost.id) is None

        self.blog_repo.save(blogpost)

        assert self.blog_repo.get(blogpost.id) == blogpost, "Blogpost not saved"
        clean_project_mock.assert_called_with(blogpost.project_id)

    @with_context
    def test_save_fails_if_integrity_error(self):
        """Test save raises a DBIntegrityError if the instance to be saved lacks
        a required value"""

        blogpost = BlogpostFactory.build(title=None)

        assert_raises(DBIntegrityError, self.blog_repo.save, blogpost)


    @with_context
    def test_save_only_saves_blogposts(self):
        """Test save raises a WrongObjectError when an object which is not
        a Blogpost instance is saved"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.blog_repo.save, bad_object)


    @with_context
    @patch('pybossa.repositories.blog_repository.clean_project')
    def test_update(self, clean_project_mock):
        """Test update persists the changes made to the blogpost"""

        blogpost = BlogpostFactory.create(body='this is a blogpost')
        blogpost.body = 'new content'

        self.blog_repo.update(blogpost)
        updated_blogpost = self.blog_repo.get(blogpost.id)

        assert updated_blogpost.body == 'new content', updated_blogpost
        clean_project_mock.assert_called_with(blogpost.project_id)


    @with_context
    def test_update_fails_if_integrity_error(self):
        """Test update raises a DBIntegrityError if the instance to be updated
        lacks a required value"""

        blogpost = BlogpostFactory.create()
        blogpost.title = None

        assert_raises(DBIntegrityError, self.blog_repo.update, blogpost)


    @with_context
    def test_update_only_updates_blogposts(self):
        """Test update raises a WrongObjectError when an object which is not
        a Blogpost instance is updated"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.blog_repo.update, bad_object)


    @with_context
    @patch('pybossa.repositories.blog_repository.clean_project')
    def test_delete(self, clean_project_mock):
        """Test delete removes the blogpost instance"""

        blogpost = BlogpostFactory.create()

        self.blog_repo.delete(blogpost)
        deleted = self.blog_repo.get(blogpost.id)

        assert deleted is None, deleted
        clean_project_mock.assert_called_with(blogpost.project_id)

    @with_context
    def test_delete_only_deletes_blogposts(self):
        """Test delete raises a WrongObjectError if is requested to delete other
        than a blogpost"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.blog_repo.delete, bad_object)
