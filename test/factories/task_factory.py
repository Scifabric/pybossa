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

from pybossa.model.task import Task
from . import BaseFactory, factory, task_repo


class TaskFactory(BaseFactory):
    class Meta:
        model = Task

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        task = model_class(*args, **kwargs)
        task_repo.save(task)
        return task

    id = factory.Sequence(lambda n: n)
    project = factory.SubFactory('factories.ProjectFactory')
    project_id = factory.LazyAttribute(lambda task: task.project.id)
    state = 'ongoing'
    quorum = 0
    calibration = 0
    priority_0 = 0.0
    n_answers = 30
