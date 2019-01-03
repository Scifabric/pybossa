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

from default import Test, db, with_context
from nose.tools import assert_raises
from sqlalchemy.exc import IntegrityError
from mock import patch
from pybossa.model.category import Category
from factories import CategoryFactory


class TestModelCategory(Test):

    @with_context
    def test_category_public_attributes(self):
        """Test CATEGORY public attributes works."""
        cat = CategoryFactory.create()
        assert cat.public_attributes().sort() == list(cat.dictize().keys()).sort()

    @with_context
    def test_blogpost_public_json(self):
        """Test CATEGORY to_public_json method works with extra fields."""
        cat = CategoryFactory.create()
        cat.info = {'secret': 'mysecret', 'public': 'hello'}
        err_msg = "There should be info keys"
        with patch.dict(self.flask_app.config, {'CATEGORY_INFO_PUBLIC_FIELDS': ['public']}):
            json = cat.to_public_json()
            assert list(json['info'].keys()).sort() == Category().public_info_keys().sort(), err_msg
            assert 'public' in list(json['info'].keys())
            assert 'secret' not in list(json['info'].keys())
