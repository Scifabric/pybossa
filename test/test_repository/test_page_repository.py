# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2019 Scifabric LTD.
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

from default import Test, db, with_context
from nose.tools import assert_raises
from factories import PageFactory, ProjectFactory
from pybossa.repositories import PageRepository
from pybossa.exc import WrongObjectError, DBIntegrityError


class TestPageRepository(Test):

    def setUp(self):
        super(TestPageRepository, self).setUp()
        self.page_repo = PageRepository(db)

    @with_context
    def test_get_return_none_if_no_page(self):
        """Test get method returns None if there is no page with the
        specified id"""

        page = self.page_repo.get(2)

        assert page is None, page

    @with_context
    def test_get_returns_page(self):
        """Test get method returns a page if exists"""

        page = PageFactory.create()

        retrieved_page = self.page_repo.get(page.id)

        assert page == retrieved_page, retrieved_page

    @with_context
    def test_get_by(self):
        """Test get_by returns a page with the specified attribute"""

        page = PageFactory.create(slug="algo")

        retrieved_page = self.page_repo.get_by(slug="algo")

        assert page == retrieved_page, retrieved_page

    @with_context
    def test_get_by_returns_none_if_no_page(self):
        """Test get_by returns None if no page matches the query"""

        PageFactory.create()

        page = self.page_repo.get_by(project_id=10000)

        assert page is None, page

    @with_context
    def test_filter_by_no_matches(self):
        """Test filter_by returns an empty list if no pages match the query"""

        PageFactory.create()

        retrieved_pages = self.page_repo.filter_by(project_id=100)

        assert isinstance(retrieved_pages, list)
        assert len(retrieved_pages) == 0, retrieved_pages

    @with_context
    def test_filter_by_one_condition(self):
        """Test filter_by returns a list of pages that meet the filtering
        condition"""

        PageFactory.create_batch(3, slug="algo")
        should_be_missing = PageFactory.create(slug="new")

        retrieved_pages = self.page_repo.filter_by(slug="algo")

        assert len(retrieved_pages) == 3, retrieved_pages
        assert should_be_missing not in retrieved_pages, retrieved_pages

    @with_context
    def test_filter_by_limit_offset(self):
        """Test that filter_by supports limit and offset options"""

        PageFactory.create_batch(4)
        all_pages = self.page_repo.filter_by()

        first_two = self.page_repo.filter_by(limit=2)
        last_two = self.page_repo.filter_by(limit=2, offset=2)

        assert len(first_two) == 2, first_two
        assert len(last_two) == 2, last_two
        assert first_two == all_pages[:2]
        assert last_two == all_pages[2:]

    @with_context
    def test_filter_by_multiple_conditions(self):
        """Test filter_by supports multiple-condition queries"""

        h1 = PageFactory.create(slug='url')
        h2 = PageFactory.create(slug='url')

        retrieved_pages = self.page_repo.filter_by(project_id=h2.project_id,
                                                   slug='url')

        assert len(retrieved_pages) == 1, retrieved_pages
        assert h2 in retrieved_pages, retrieved_pages

    @with_context
    def test_save(self):
        """Test save persist the page"""

        page = PageFactory.build()
        project = ProjectFactory.create()
        page.project_id = project.id
        assert self.page_repo.get(page.id) is None

        self.page_repo.save(page)

        assert self.page_repo.get(page.id) == page, "Helping material not saved"

    @with_context
    def test_save_fails_if_integrity_error(self):
        """Test save raises a DBIntegrityError if the instance to be saved lacks
        a required value"""

        page = PageFactory.build(project_id=None)

        assert_raises(DBIntegrityError, self.page_repo.save, page)

    @with_context
    def test_save_only_saves_pages(self):
        """Test save raises a WrongObjectError when an object which is not
        a Blogpost instance is saved"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.page_repo.save, bad_object)

    @with_context
    def test_update(self):
        """Test update persists the changes made to the page"""

        info = {'key': 'val'}
        page = PageFactory.create(info=info)
        info_new = {'f': 'v'}
        page.info = info_new

        self.page_repo.update(page)
        updated_page = self.page_repo.get(page.id)

        assert updated_page.info == info_new, updated_page

    @with_context
    def test_update_fails_if_integrity_error(self):
        """Test update raises a DBIntegrityError if the instance to be updated
        lacks a required value"""

        page = PageFactory.create()
        page.project_id = None

        assert_raises(DBIntegrityError, self.page_repo.update, page)

    @with_context
    def test_update_only_updates_pages(self):
        """Test update raises a WrongObjectError when an object which is not
        a Page instance is updated"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.page_repo.update, bad_object)

    @with_context
    def test_delete(self):
        """Test delete removes the page instance"""

        page = PageFactory.create()

        self.page_repo.delete(page)
        deleted = self.page_repo.get(page.id)

        assert deleted is None, deleted

    @with_context
    def test_delete_only_deletes_pages(self):
        """Test delete raises a WrongObjectError if is requested to delete other
        than a page"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.page_repo.delete, bad_object)
