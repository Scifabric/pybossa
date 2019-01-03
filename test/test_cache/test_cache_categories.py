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

from default import Test, with_context
from pybossa.cache import categories as cached_categories
from factories import CategoryFactory, ProjectFactory


class TestCategoriesCache(Test):

    @with_context 
    def test_get_all_returns_all_categories(self):
        categories = [CategoryFactory.create()]

        assert cached_categories.get_all() == categories

    @with_context 
    def test_get_used_returns_only_categories_with_projects(self):
        used_category = CategoryFactory.create()
        ProjectFactory.create(category=used_category)
        unused_category = CategoryFactory.create()

        used_categories = cached_categories.get_used()

        assert used_categories[0]['id'] == used_category.id, used_categories


    @with_context 
    def test_get_used_returns_requiered_fields(self):
        used_category = CategoryFactory.create()
        ProjectFactory.create(category=used_category)
        fields = ('id', 'name', 'short_name', 'description')

        used_categories = cached_categories.get_used()

        for field in fields:
            assert field in list(used_categories[0].keys())
        assert len(fields) == len(list(used_categories[0].keys()))
