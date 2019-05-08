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
        assert 'Answer Field Config' in res.data, res.data
        assert 'Consensus Config' in res.data, res.data

    @with_context
    def test_post_answer_field_config(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/answerfieldsconfig?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        csrf = data['csrf']
        fields = {'answerFieldsConfig': {
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
        fields = {'consensusConfig': {
            'threshold': 70,
            'maxRetries': 10,
            'redundanceDelta': 2
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
