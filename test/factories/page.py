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

from pybossa.model.page import Page
from . import BaseFactory, factory, page_repo, ProjectFactory


class PageFactory(BaseFactory):
    class Meta:
        model = Page

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        page = model_class(*args, **kwargs)
        if kwargs.get('project_id') is None:
            project = ProjectFactory.create()
            page.project_id = project.id
        page_repo.save(page)
        return page

    id = factory.Sequence(lambda n: n)
    info = {'file_name': 'test.jpg',
            'container': 'user_3',
            'structure': ['Header', 'Blog', 'Footer']
            }
    slug = factory.Sequence(lambda n: u'slug-%d' % n)
    media_url = '/uploads/user_3/test.jpg'
