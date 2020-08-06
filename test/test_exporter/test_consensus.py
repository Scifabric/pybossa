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
from pybossa.exporter.consensus_exporter import export_consensus, format_consensus
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

    @with_context
    @patch('pybossa.exporter.consensus_exporter.get_user_info')
    def test_format_consensus_categorical(self, user_info):
        user_info.return_value = {'name': 'joe'}
        consensus = {
            "context.name": {
                "answser_field_config": {
                    "config": {},
                    "type": "categorical",
                    "retry_for_consensus": False
                },
                "contributorsMetConsensus": [1],
                "percentage": 100.0,
                "contributorsConsensusPercentage": [{
                    "percentage": 100.0,
                    "user_id": 1
                }],
                "value": "hello"
            },
        }
        task_run = {"joe": {'context': {'name': 'hello'}}}
        rows = [dict(task_id=1,
                    project_id=1,
                    task_run__id=10,
                    task_run__user_id=2,
                    task_run__info=task_run,
                    consensus={'consensus':consensus} )]

        expect = [{
            "contributor_name": "joe",
            "answer_percentage": 100.0,
            "contributor_answer": 'hello'
        }]
        res = format_consensus(rows)
        assert res[0]['consensus__context.name__contributorsConsensusPercentage'] == expect

    @with_context
    @patch('pybossa.exporter.consensus_exporter.get_user_info')
    def test_format_consensus_categorical_list(self, user_info):
        user_info.return_value = {'name': 'joe'}
        consensus = {
            "context.0.name": {
                "answser_field_config": {
                    "config": {},
                    "type": "categorical",
                    "retry_for_consensus": False
                },
                "contributorsMetConsensus": [1],
                "percentage": 100.0,
                "contributorsConsensusPercentage": [{
                    "percentage": 100.0,
                    "user_id": 1
                }],
                "value": "hello"
            },
        }
        task_run = {"joe": {'context': [{'name': 'hello'}]}}
        rows = [dict(task_id=1,
                    project_id=1,
                    task_run__id=10,
                    task_run__user_id=2,
                    task_run__info=task_run,
                    consensus={'consensus':consensus} )]

        expect = [{
            "contributor_name": "joe",
            "answer_percentage": 100.0,
            "contributor_answer": 'hello'
        }]
        res = format_consensus(rows)
        assert res[0]['consensus__context.0.name__contributorsConsensusPercentage'] == expect

    @with_context
    @patch('pybossa.exporter.consensus_exporter.get_user_info')
    def test_format_consensus_categorical_nested(self, user_info):
        user_info.return_value = {'name': 'joe'}
        consensus = {
            "context.2000.ny.name": {
                "answser_field_config": {
                    "config": {
                        "keys": ['name'],
                        "keyValues": [
                            "born_year",
                            "born_state"
                        ]
                    },
                    "type": "categorical_nested",
                    "retry_for_consensus": False
                },
                "contributorsMetConsensus": [1],
                "percentage": 100.0,
                "contributorsConsensusPercentage": [{
                    "percentage": 100.0,
                    "user_id": 1
                }],
                "value": "hello"
            },
        }
        task_run = {"joe": {'context': [
            {'name': 'hello','born_year': 2000, 'born_state': 'ny'},
            {'name': 'world','born_year': 2020, 'born_state': 'ny'}
            ]}}
        rows = [dict(task_id=1,
                    project_id=1,
                    task_run__id=10,
                    task_run__user_id=2,
                    task_run__info=task_run,
                    consensus={'consensus':consensus} )]

        expect = [{
            "contributor_name": "joe",
            "answer_percentage": 100.0,
            "contributor_answer": 'hello'
        }]
        res = format_consensus(rows)
        assert res[0]['consensus__context.2000.ny.name__contributorsConsensusPercentage'] == expect

    @with_context
    @patch('pybossa.exporter.consensus_exporter.get_user_info')
    def test_format_consensus_invalid_type(self, user_info):
        user_info.return_value = {'name': 'joe'}
        consensus = {
            "context.name": {
                "answser_field_config": {
                    "config": {},
                    "type": "other",
                    "retry_for_consensus": False
                },
                "contributorsMetConsensus": [1],
                "percentage": 100.0,
                "contributorsConsensusPercentage": [{
                    "percentage": 100.0,
                    "user_id": 1
                }],
                "value": "hello"
            },
        }
        task_run = {"joe": {'context': {'name': 'hello'}}}
        rows = [dict(task_id=1,
                    project_id=1,
                    task_run__id=10,
                    task_run__user_id=2,
                    task_run__info=task_run,
                    consensus={'consensus':consensus} )]

        expect = [{
            "contributor_name": "joe",
            "answer_percentage": 100.0,
            "contributor_answer": None
        }]
        res = format_consensus(rows)
        assert res[0]['consensus__context.name__contributorsConsensusPercentage'] == expect
