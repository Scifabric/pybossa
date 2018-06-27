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

from pybossa.model.project import Project
from . import BaseFactory, factory, project_repo


class ProjectFactory(BaseFactory):
    class Meta:
        model = Project

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        project = model_class(*args, **kwargs)
        project_repo.save(project)
        return project

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: 'My (utf8=✓)Project number %d' % n)
    short_name = factory.Sequence(lambda n: '✓project%d' % n)
    description = 'Project description utf8=✓'
    allow_anonymous_contributors = True
    featured = False
    published = True
    webhook = None
    zip_download = True
    owner = factory.SubFactory('factories.UserFactory')
    owner_id = factory.LazyAttribute(lambda project: project.owner.id)
    category = factory.SubFactory('factories.CategoryFactory')
    category_id = factory.LazyAttribute(lambda project: project.category.id)
    info = {'task_presenter': '<div>utf8=✓</div>',
            'thumbnail': 'img.png',
            'container': 'container',
            'thumbnail_url': 'http://cdn.com/container/img.png',
            'onesignal': {'data': 'private'},
            'onesignal_app_id': 1
            }
    owners_ids = factory.LazyAttribute(lambda project: [project.owner.id])
