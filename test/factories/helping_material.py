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

from pybossa.model.helpingmaterial import HelpingMaterial
from . import BaseFactory, factory, helping_repo, ProjectFactory


class HelpingMaterialFactory(BaseFactory):
    class Meta:
        model = HelpingMaterial

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        helpingmaterial = model_class(*args, **kwargs)
        if kwargs.get('project_id') is None:
            project = ProjectFactory.create()
            helpingmaterial.project_id = project.id
        helping_repo.save(helpingmaterial)
        return helpingmaterial

    id = factory.Sequence(lambda n: n)
    info = {'file_name': 'test.jpg',
            'container': 'user_3'}
    media_url = '/uploads/user_3/test.jpg'
