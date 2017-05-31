# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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
from factories import HelpingMaterialFactory, ProjectFactory
from pybossa.repositories import HelpingMaterialRepository
from pybossa.exc import WrongObjectError, DBIntegrityError



class TestHelpingMaterialRepository(Test):

    def setUp(self):
        super(TestHelpingMaterialRepository, self).setUp()
        self.helping_repo = HelpingMaterialRepository(db)

    @with_context
    def test_get_return_none_if_no_helpingmaterial(self):
        """Test get method returns None if there is no helpingmaterial with the
        specified id"""

        helpingmaterial = self.helping_repo.get(2)

        assert helpingmaterial is None, helpingmaterial


    @with_context
    def test_get_returns_helpingmaterial(self):
        """Test get method returns a helpingmaterial if exists"""

        helpingmaterial = HelpingMaterialFactory.create()

        retrieved_helpingmaterial = self.helping_repo.get(helpingmaterial.id)

        assert helpingmaterial == retrieved_helpingmaterial, retrieved_helpingmaterial


    @with_context
    def test_get_by(self):
        """Test get_by returns a helpingmaterial with the specified attribute"""

        helpingmaterial = HelpingMaterialFactory.create(media_url="algo")

        retrieved_helpingmaterial = self.helping_repo.get_by(media_url="algo")

        assert helpingmaterial == retrieved_helpingmaterial, retrieved_helpingmaterial


    @with_context
    def test_get_by_returns_none_if_no_helpingmaterial(self):
        """Test get_by returns None if no helpingmaterial matches the query"""

        HelpingMaterialFactory.create()

        helpingmaterial = self.helping_repo.get_by(project_id=10000)

        assert helpingmaterial is None, helpingmaterial


    @with_context
    def test_filter_by_no_matches(self):
        """Test filter_by returns an empty list if no helpingmaterials match the query"""

        HelpingMaterialFactory.create()

        retrieved_helpingmaterials = self.helping_repo.filter_by(project_id=100)

        assert isinstance(retrieved_helpingmaterials, list)
        assert len(retrieved_helpingmaterials) == 0, retrieved_helpingmaterials


    @with_context
    def test_filter_by_one_condition(self):
        """Test filter_by returns a list of helpingmaterials that meet the filtering
        condition"""

        HelpingMaterialFactory.create_batch(3, media_url="algo")
        should_be_missing = HelpingMaterialFactory.create(media_url="new")

        retrieved_helpingmaterials = self.helping_repo.filter_by(media_url="algo")

        assert len(retrieved_helpingmaterials) == 3, retrieved_helpingmaterials
        assert should_be_missing not in retrieved_helpingmaterials, retrieved_helpingmaterials


    @with_context
    def test_filter_by_limit_offset(self):
        """Test that filter_by supports limit and offset options"""

        HelpingMaterialFactory.create_batch(4)
        all_helpingmaterials = self.helping_repo.filter_by()

        first_two = self.helping_repo.filter_by(limit=2)
        last_two = self.helping_repo.filter_by(limit=2, offset=2)

        assert len(first_two) == 2, first_two
        assert len(last_two) == 2, last_two
        assert first_two == all_helpingmaterials[:2]
        assert last_two == all_helpingmaterials[2:]


    @with_context
    def test_filter_by_multiple_conditions(self):
        """Test filter_by supports multiple-condition queries"""

        h1 = HelpingMaterialFactory.create(media_url='url')
        h2 = HelpingMaterialFactory.create(media_url='url')

        retrieved_helpingmaterials = self.helping_repo.filter_by(project_id=h2.project_id,
                                                                 media_url='url')

        assert len(retrieved_helpingmaterials) == 1, retrieved_helpingmaterials
        assert h2 in retrieved_helpingmaterials, retrieved_helpingmaterials


    @with_context
    def test_save(self):
        """Test save persist the helpingmaterial"""

        helpingmaterial = HelpingMaterialFactory.build()
        project = ProjectFactory.create()
        helpingmaterial.project_id = project.id
        assert self.helping_repo.get(helpingmaterial.id) is None

        self.helping_repo.save(helpingmaterial)

        assert self.helping_repo.get(helpingmaterial.id) == helpingmaterial, "Helping material not saved"


    @with_context
    def test_save_fails_if_integrity_error(self):
        """Test save raises a DBIntegrityError if the instance to be saved lacks
        a required value"""

        helpingmaterial = HelpingMaterialFactory.build(project_id=None)

        assert_raises(DBIntegrityError, self.helping_repo.save, helpingmaterial)


    @with_context
    def test_save_only_saves_helpingmaterials(self):
        """Test save raises a WrongObjectError when an object which is not
        a Blogpost instance is saved"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.helping_repo.save, bad_object)


    @with_context
    def test_update(self):
        """Test update persists the changes made to the helpingmaterial"""

        info = {'key': 'val'}
        helpingmaterial = HelpingMaterialFactory.create(info=info)
        info_new = {'f': 'v'}
        helpingmaterial.info = info_new

        self.helping_repo.update(helpingmaterial)
        updated_helpingmaterial = self.helping_repo.get(helpingmaterial.id)

        assert updated_helpingmaterial.info == info_new, updated_helpingmaterial


    @with_context
    def test_update_fails_if_integrity_error(self):
        """Test update raises a DBIntegrityError if the instance to be updated
        lacks a required value"""

        helpingmaterial = HelpingMaterialFactory.create()
        helpingmaterial.project_id = None

        assert_raises(DBIntegrityError, self.helping_repo.update, helpingmaterial)


    @with_context
    def test_update_only_updates_helpingmaterials(self):
        """Test update raises a WrongObjectError when an object which is not
        a HelpingMaterial instance is updated"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.helping_repo.update, bad_object)


    @with_context
    def test_delete(self):
        """Test delete removes the helpingmaterial instance"""

        helpingmaterial = HelpingMaterialFactory.create()

        self.helping_repo.delete(helpingmaterial)
        deleted = self.helping_repo.get(helpingmaterial.id)

        assert deleted is None, deleted


    @with_context
    def test_delete_only_deletes_helpingmaterials(self):
        """Test delete raises a WrongObjectError if is requested to delete other
        than a helpingmaterial"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.helping_repo.delete, bad_object)
