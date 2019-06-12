import json

from default import db, with_context
from factories import ProjectFactory
from helper import web
from pybossa.repositories import ProjectRepository

project_repo = ProjectRepository(db)


class TestEnrichment(web.Helper):

    @with_context
    def test_post_enirchment_config(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/enrichment?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert res.status_code == 200 and 'enrichments' in data, res
        
        csrf = data['csrf']
        enrich_data = {
            'enrich_data': {
                'in_field_name': 'A',
                'task_state': 'e',
                'type': 'fun',
                'sub_type': 'picnic',
                'out_field_name': 'enrich_A'                
            }
        }
        res = self.app.post(url, content_type='application/json',
                            data=json.dumps(enrich_data),
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert res.status_code == 200 and \
            data['flash'] == 'Success! Project data enrichment updated', res

        project = project_repo.get(project.id)
        updated_enrichments = project.info['enrichments']
        assert enrich_data['enrich_data'] == updated_enrichments, 'Updated enrichment do not match'
