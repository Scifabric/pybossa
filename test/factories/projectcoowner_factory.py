# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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

from pybossa.model.project_coowner import ProjectCoowner
from . import BaseFactory, factory, projectcoowner_repo


class ProjectCoownerFactory(BaseFactory):
    class Meta:
        model = ProjectCoowner

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        projectcoowner = model_class(*args, **kwargs)
        projectcoowner_repo.save(projectcoowner)
        return projectcoowner

    id = factory.Sequence(lambda n: n)
    project = factory.SubFactory('factories.ProjectFactory')
    project_id = factory.LazyAttribute(lambda coowner: coowner.project.id)
    coowner = factory.SubFactory('factories.UserFactory')
    coowner_id = factory.LazyAttribute(lambda coowner: coowner.user.id)
