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

from pybossa.model.blogpost import Blogpost
from . import BaseFactory, factory, blog_repo


class BlogpostFactory(BaseFactory):
    class Meta:
        model = Blogpost

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        blogpost = model_class(*args, **kwargs)
        blog_repo.save(blogpost)
        return blogpost

    owner = factory.SelfAttribute('project.owner')
    id = factory.Sequence(lambda n: n)
    title = 'Blogpost title'
    body = 'Blogpost body text'
    media_url = 'https://server.com/img.jpg'
    info = {'file_name': 'img.jpg',
            'container': 'user'}
    project = factory.SubFactory('factories.ProjectFactory')
    project_id = factory.LazyAttribute(lambda blogpost: blogpost.project.id)
    user_id = factory.LazyAttribute(
        lambda blogpost: blogpost.owner.id if blogpost.owner else None)
