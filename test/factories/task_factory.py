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

from pybossa.model.task import Task
from . import BaseFactory, factory, task_repo


class TaskFactory(factory.Factory):
    class Meta:
        model = Task

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        task = model_class(*args, **kwargs)
        task_repo.save(task)
        return task

    @classmethod
    def _setup_next_sequence(cls):
        return 1

    id = factory.Sequence(lambda n: n)
    app = factory.SubFactory('factories.AppFactory')
    app_id = factory.LazyAttribute(lambda task: task.app.id)
    state = u'ongoing'
    quorum = 0
    calibration = 0
    priority_0 = 0.0
    n_answers = 30
