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
    def test_post_project_config_setting(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/project-config?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = ""
        fields = {
            'config': {'target_bucket': 'bucket'},
            'data_access': ['L1', 'L2'],
            'select_users': ['1', '2']
        }
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps(fields),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert data['flash'] == 'Configuration updated successfully'

