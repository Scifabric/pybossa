# -*- coding: utf8 -*-
import json
from mock import patch

from default import db, with_context
from factories import ProjectFactory, UserFactory
from helper import web
from pybossa.repositories import ProjectRepository, UserRepository

project_repo = ProjectRepository(db)
user_repo = UserRepository(db)


class TestAnswerFieldConfig(web.Helper):

    @with_context
    def test_get_config(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/answerfieldsconfig?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app.get(url)
        assert '<fields-config' in res.data, res.data
        assert '<consensus-config' in res.data, res.data

    @with_context
    def test_post_answer_field_config(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/answerfieldsconfig?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        fields = {'answer_fields': {
            'hello': {
                'type': 'categorical',
                'config': {
                    'labels': ['A', 'B', 'C']
                },
                'retry_for_consensus': True
            }
        }}
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps(fields),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert data['flash'] == 'Configuration updated successfully'

    @with_context
    def test_post_consensus_config(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/answerfieldsconfig?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        fields = {'consensus_config': {
            'consensus_threshold': 70,
            'max_retries': 10,
            'redundance_config': 2
        }}
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps(fields),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert data['flash'] == 'Configuration updated successfully'

    @with_context
    def test_post_invalid_config(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/answerfieldsconfig?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        res = self.app.post(url, content_type='application/json',
                            data='',
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert data['flash'] == 'An error occurred.'
        assert data['status'] == 'error'

    @with_context
    @patch('pybossa.view.projects.performance_stats_repo.bulk_delete')
    def test_update_delete_old_stats(self, delete):
        fields = {
            'hello': {
                'type': 'categorical',
                'config': {
                    'labels': ['A', 'B', 'C']
                }
            }
        }
        info = {'answer_fields': fields}
        project = ProjectFactory.create(
            published=True, info=info)
        url = '/project/%s/answerfieldsconfig?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        fields['hello']['config']['labels'] = ['A']
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps(info),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        delete.assert_called_once()
        args, _ = delete.call_args
        proj, field = args
        assert proj == project.id
        assert field == 'hello'

    @with_context
    @patch('pybossa.view.projects.performance_stats_repo.bulk_delete')
    def test_update_add_field_does_not_delete_stats(self, delete):
        fields = {
            'hello': {
                'type': 'categorical',
                'config': {
                    'labels': ['A', 'B', 'C']
                }
            }
        }
        info = {'answer_fields': fields}
        project = ProjectFactory.create(
            published=True, info=info)
        url = '/project/%s/answerfieldsconfig?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        fields['bye'] = {
            'config': {},
            'type': 'freetext'
        }
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps(info),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        delete.assert_not_called()

    @with_context
    @patch('pybossa.view.projects.performance_stats_repo.bulk_delete')
    def test_update_delete_field_deletes_stats(self, delete):
        fields = {
            'hello': {
                'type': 'categorical',
                'config': {
                    'labels': ['A', 'B', 'C']
                }
            }
        }
        info = {'answer_fields': fields}
        project = ProjectFactory.create(
            published=True, info=info)
        url = '/project/%s/answerfieldsconfig?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps({'answer_fields': {}}),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        delete.assert_called_once()
        args, _ = delete.call_args
        proj, field = args
        assert proj == project.id
        assert field == 'hello'


    @with_context
    @patch('pybossa.view.projects.performance_stats_repo.bulk_delete')
    def test_update_delete_multiple_fields(self, delete):
        fields = {
            'hello': {
                'type': 'freetext',
                'config': {}
            },
            '你好': {
                'type': 'freetext',
                'config': {}
            },
            'ciao': {
                'type': 'freetext',
                'config': {}
            },
            'hola': {
                'type': 'freetext',
                'config': {}
            }
        }
        info = {'answer_fields': fields}
        project = ProjectFactory.create(
            published=True, info=info)
        url = '/project/%s/answerfieldsconfig?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        fields.pop('hello')
        fields['Привет'] = {
            'type': 'freetext',
            'config': {}
        }
        fields['hola']['type'] = 'categorical'
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps({'answer_fields': fields}),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert delete.call_count == 2
        assert all(args[0] == project.id for args, _ in delete.call_args_list)
        deleted_fields = set(args[1] for args, _ in delete.call_args_list)
        assert deleted_fields == set(['hello', 'hola'])
