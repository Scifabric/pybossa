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

from pybossa.model.category import Category
from . import BaseFactory, factory, project_repo


class CategoryFactory(factory.Factory):
    class Meta:
        model = Category

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        category = model_class(*args, **kwargs)
        project_repo.save_category(category)
        return category

    @classmethod
    def _setup_next_sequence(cls):
        return 1

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: 'category_name_%d' % n)
    short_name = factory.Sequence(lambda n: 'category_short_name_%d' % n)
    description = 'Category description for testing purposes'
