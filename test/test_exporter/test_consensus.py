# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2017 SciFabric LTD.
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

import json
from StringIO import StringIO
from zipfile import ZipFile

from default import Test, with_context
from pybossa.exporter.consensus_exporter import export_consensus
from mock import patch
from factories import ProjectFactory, TaskFactory, TaskRunFactory
from pandas import DataFrame

class TestConsensusExporter(Test):

    @with_context
    def test_export_consesus(self):
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, info={'test': 2}, n_answers=1)
        task2 = TaskFactory.create(project=project, info={'test': 2}, n_answers=1, calibration=1)
        task3 = TaskFactory.create(project=project, info={'test': 2}, n_answers=1, calibration=1)
        task_run = TaskRunFactory.create(task=task, info={'hello': u'你好'})
        task_run2 = TaskRunFactory.create(task=task2, info={'hello': u'你好'})
        with export_consensus(project, 'tsk', 'csv', False, None) as fp:
            zipfile = ZipFile(fp)
            filename = zipfile.namelist()[0]
            df = DataFrame.from_csv(StringIO(zipfile.read(filename)))
        rows = df.reset_index().to_dict(orient='records')
        assert len(rows) == 2
        row = rows[0]
        assert json.loads(row['task_run__info'])[task_run.user.name] == {'hello': u'你好'}
        assert any(r['gold'] for r in rows)

    @with_context
    def test_export_consesus_metadata(self):
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, info={'test': 2}, n_answers=1)
        task2 = TaskFactory.create(project=project, info={'test': 2}, n_answers=1, calibration=1)
        task3 = TaskFactory.create(project=project, info={'test': 2}, n_answers=1, calibration=1)
        task_run = TaskRunFactory.create(task=task, info={'hello': u'你好'})
        task_run2 = TaskRunFactory.create(task=task2, info={'hello': u'你好'})
        with export_consensus(project, 'tsk', 'csv', True, None) as fp:
            zipfile = ZipFile(fp)
            filename = zipfile.namelist()[0]
            df = DataFrame.from_csv(StringIO(zipfile.read(filename)))
        rows = df.reset_index().to_dict(orient='records')
        assert len(rows) == 2
        assert json.loads(rows[0]['task_run__info'])[task_run.user.name] == {'hello': u'你好'}
        assert any(r['gold'] for r in rows)
