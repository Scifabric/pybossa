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

    # @with_context
    # def test_post_project_setting(self):
    #     project = ProjectFactory.create(published=True)
    #     url = '/project/%s/summary?api_key=%s' % (project.short_name, project.owner.api_key)
    #     res = self.app_get_json(url)
    #     data = json.loads(res.data)
    #     csrf = data['csrf']
    #     fields = {'project': {
    #         'target_bucket': "bucket",
    #         'data_access': ['L1'],
    #         'project_users': []
    #     }}
    #     res = self.app.post(url, content_type='application/json',
    #                         data=json.dumps(fields),
    #                         headers={'X-CSRFToken': csrf})
    #     data = json.loads(res.data)
    #     assert data['flash'] == 'Configuration updated successfully'

    # def test_post_ownership_setting(self):
    #     project = ProjectFactory.create(published=True)
    #     url = '/project/%s/summary?api_key=%s' % (project.short_name, project.owner.api_key)
    #     res = self.app_get_json(url)
    #     data = json.loads(res.data)
    #     csrf = data['csrf']
    #     fields = {'project': {
    #         'target_bucket': "bucket",
    #         'data_access': ['L1'],
    #         'project_users': []
    #     }}
    #     res = self.app.post(url, content_type='application/json',
    #                         data=json.dumps(fields),
    #                         headers={'X-CSRFToken': csrf})
    #     assert res.get('ok')
    #     data = json.loads(res.data)
    #     assert data['flash'] == 'Configuration updated successfully'

    # def test_post_task_setting(self):
    #     project = ProjectFactory.create(published=True)
    #     url = '/project/%s/summary?api_key=%s' % (project.short_name, project.owner.api_key)
    #     res = self.app_get_json(url)
    #     data = json.loads(res.data)
    #     csrf = data['csrf']
    #     fields = {'ownership': {
    #         'coowners': []
    #     }}
    #     res = self.app.post(url, content_type='application/json',
    #                         data=json.dumps(fields),
    #                         headers={'X-CSRFToken': csrf})
    #     assert res.get('ok')
    #     data = json.loads(res.data)
    #     assert data['flash'] == 'Configuration updated successfully'

    # def test_post_answer_fields_setting(self):
    #     project = ProjectFactory.create(published=True)
    #     url = '/project/%s/summary?api_key=%s' % (project.short_name, project.owner.api_key)
    #     res = self.app_get_json(url)
    #     data = json.loads(res.data)
    #     csrf = data['csrf']
    #     fields = {
    #         'answer_fields': {
    #             'hello': {
    #                 'type': 'categorical',
    #                 'config': {
    #                     'labels': ['A', 'B', 'C']
    #                 },
    #                 'retry_for_consensus': True
    #             }
    #         },
    #         'consensus_config': {}
    #     }
    #     res = self.app.post(url, content_type='application/json',
    #                         data=json.dumps(fields),
    #                         headers={'X-CSRFToken': csrf})
    #     assert res.get('ok')
    #     data = json.loads(res.data)
    #     assert data['flash'] == 'Configuration updated successfully'


    # def test_post_quiz_setting(self):
    #     project = ProjectFactory.create(published=True)
    #     url = '/project/%s/summary?api_key=%s' % (project.short_name, project.owner.api_key)
    #     res = self.app_get_json(url)
    #     data = json.loads(res.data)
    #     csrf = data['csrf']
    #     fields = {'quiz': {
    #         'config': {
    #             "enabled": False,
    #             "questions": 10,
    #             "passing": 5,
    #             "completion_mode": "all_questions"
    #         },
    #         'reset': []
    #     }}
    #     res = self.app.post(url, content_type='application/json',
    #                         data=json.dumps(fields),
    #                         headers={'X-CSRFToken': csrf})
    #     assert res.get('ok')
    #     data = json.loads(res.data)
    #     assert data['flash'] == 'Configuration updated successfully'

    # def test_get_user_list(self):
    #     project = ProjectFactory.create(published=True)
    #     url = '/project/%s/summary/coowners?api_key=%s' % (project.short_name, project.owner.api_key)
    #     res = self.app_get_json(url)
    #     data = json.loads(res.data)
    #     csrf = data['csrf']
    #     fields = {'project': {
    #         'target_bucket': "bucket",
    #         'data_access': ['L1'],
    #         'project_users': []
    #     }}
    #     res = self.app.post(url, content_type='application/json',
    #                         data=json.dumps(fields),
    #                         headers={'X-CSRFToken': csrf})
    #     assert res.get('ok')
    #     data = json.loads(res.data)
    #     assert data['flash'] == 'Configuration updated successfully'
