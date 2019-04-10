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

from pybossa.model.performance_stats import PerformanceStats, StatType
from . import BaseFactory, factory, performance_repo


class PerformanceStatsFactory(BaseFactory):
    class Meta:
        model = PerformanceStats

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        stat = model_class(*args, **kwargs)
        performance_repo.save(stat)
        return stat

    id = factory.Sequence(lambda n: n)
    project_id = 1
    field = 'test'
    user_id = 1
    user_key = ''
    stat_type = StatType.confusion_matrix
    info = {}
