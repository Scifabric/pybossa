# -*- coding: utf8 -*-
import json
from mock import patch

from default import db, with_context
from factories import ProjectFactory, UserFactory
from helper import web
from pybossa.repositories import ProjectRepository, UserRepository

project_repo = ProjectRepository(db)
user_repo = UserRepository(db)


class TestSummary(web.Helper):
    @with_context
    def test_get_config(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/summary?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app.get(url)
        assert 'setting' in res.data, res.data
        assert 'ownership-setting' in res.data, res.data
        assert 'task-setting' in res.data, res.data
        assert 'fields-config' in res.data, res.data
        assert 'consensus-config' in res.data, res.data
        assert 'quiz-setting' in res.data, res.data

    @with_context
    def test_post_project_setting(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/summary?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        fields = {'project': {
            'config': {},
            'data_access': ['L1'],
            'select_users': ['1111']
        }}
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps(fields),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert data['flash'] == 'Configuration updated successfully'

    @with_context
    def test_post_ownership_setting(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/summary?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        fields = {'ownership': {
            'coowners': ['1111']
        }}
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps(fields),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert data['flash'] == 'Configuration updated successfully'

    @with_context
    def test_post_task_setting(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/summary?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        fields = {'task': {
            'sched': 'locked_scheduler',
            'minutes': 1,
            'seconds': 30,
            'default_n_answers': 1,
            'n_answers': 2,
            'rand_within_priority': False
        }}
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps(fields),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert data['status'] == 'success'

    @with_context
    def test_post_answer_fields_setting(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/summary?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        fields = {
            'answer_fields': {
                'hello': {
                    'type': 'categorical',
                    'config': {
                        'labels': ['A', 'B', 'C']
                    },
                    'retry_for_consensus': True
                }
            },
            'consensus_config': {}
        }
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps(fields),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert data['flash'] == 'Configuration updated successfully'

    @with_context
    def test_post_quiz_setting(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/summary?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        fields = {'quiz': {
            'config': {
                "enabled": False,
                "questions": 10,
                "passing": 5,
                "completion_mode": "all_questions"
            },
            'reset': []
        }}
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps(fields),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert data['flash'] == 'Configuration updated successfully'

    @with_context
    def test_invalid_post(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/summary?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        fields = {}
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps(fields),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert data['flash'] == 'An error occurred.', data['flash']
        assert data['status'] == 'error'


