# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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
import json
import io
from default import db, with_context
from test_api import TestAPI
from factories import UserFactory, HelpingMaterialFactory, ProjectFactory
from pybossa.repositories import HelpingMaterialRepository
from mock import patch

helping_repo = HelpingMaterialRepository(db)


class TestHelpingMaterialAPI(TestAPI):

    @with_context
    def test_query_helpingmaterial(self):
        """Test API query for helpingmaterial endpoint works"""
        owner = UserFactory.create()
        user = UserFactory.create()
        project = ProjectFactory(owner=owner)
        helpingmaterials = HelpingMaterialFactory.create_batch(9, project_id=project.id)
        helpingmaterial = HelpingMaterialFactory.create()

        # As anon
        url = '/api/helpingmaterial'
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 10, data

        # As user
        res = self.app.get(url + '?api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # As owner
        res = self.app.get(url + '?api_key=' + owner.api_key)
        data = json.loads(res.data)
        assert len(data) == 9, data

        # Valid field but wrong value
        res = self.app.get(url + "?media_url=wrongvalue")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get(url + '?info=container::' +
                           helpingmaterials[0].info['container'] + '&project_id=' + str(project.id))
        data = json.loads(res.data)
        # One result
        assert len(data) == 9, data
        # Correct result
        assert data[0]['project_id'] == helpingmaterials[0].project_id, data
        assert data[0]['media_url'] == helpingmaterials[0].media_url, data

        # Limits
        res = self.app.get(url + "?limit=1")
        data = json.loads(res.data)
        for item in data:
            assert item['media_url'] == helpingmaterial.media_url, item
        assert len(data) == 1, data

        # Keyset pagination
        res = self.app.get(url + '?limit=1&last_id=' + str(helpingmaterials[8].id))
        data = json.loads(res.data)
        assert len(data) == 1, len(data)
        assert data[0]['id'] == helpingmaterial.id

        # Errors
        res = self.app.get(url + "?something")
        err = json.loads(res.data)
        err_msg = "AttributeError exception should be raised"
        res.status_code == 415, err_msg
        assert res.status_code == 415, err_msg
        assert err['action'] == 'GET', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == 'AttributeError', err_msg

        # Desc filter
        url = "/api/helpingmaterial?orderby=wrongattribute"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should be 415."
        assert data['status'] == 'failed', data
        assert data['status_code'] == 415, data
        assert 'has no attribute' in data['exception_msg'], data

        # Desc filter
        url = "/api/helpingmaterial?orderby=id"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        helpingmaterials.append(helpingmaterial)
        helpingmaterials_by_id = sorted(helpingmaterials, key=lambda x: x.id, reverse=False)
        for i in range(len(helpingmaterials)):
            assert helpingmaterials_by_id[i].id == data[i]['id']

        # Desc filter
        url = "/api/helpingmaterial?orderby=id&desc=true"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        helpingmaterials_by_id = sorted(helpingmaterials, key=lambda x: x.id, reverse=True)
        for i in range(len(helpingmaterials)):
            assert helpingmaterials_by_id[i].id == data[i]['id']

        # Test priority filtering
        helpingmaterials.append(HelpingMaterialFactory.create(priority=1.0,
                                                              project_id=project.id))
        helpingmaterials.append(HelpingMaterialFactory.create(priority=0.5,
                                                              project_id=project.id))
        helpingmaterials.append(HelpingMaterialFactory.create(priority=0.1,
                                                              project_id=project.id))

        url = "/api/helpingmaterial?orderby=priority&desc=true"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        helpingmaterials_by_priority = sorted(helpingmaterials, key=lambda x: x.priority, reverse=True)
        for i in range(3):
            assert helpingmaterials_by_priority[i].id == data[i]['id'], (helpingmaterials_by_priority[i].id, data[i]['id'])

    @with_context
    def test_helpingmaterial_post(self):
        """Test API HelpingMaterialpost creation."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        project2 = ProjectFactory.create(owner=user)

        info = {'species': 'elefante'}
        payload = dict(info=info,
                       media_url='url',
                       project_id=project.id)

        # As anon
        url = '/api/helpingmaterial'
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 401, data
        assert data['status_code'] == 401, data

        # As a user
        url = '/api/helpingmaterial?api_key=%s' % user.api_key
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 403, data
        assert data['status_code'] == 403, data

        # As owner
        url = '/api/helpingmaterial?api_key=%s' % owner.api_key
        payload['project_id'] = project.id
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 200, data
        assert data['info'] == info, data
        assert data['media_url'] == 'url', data

        # As owner wrong 404 project_id
        url = '/api/helpingmaterial?api_key=%s' % owner.api_key
        payload['project_id'] = -1
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # As owner using wrong project_id
        url = '/api/helpingmaterial?api_key=%s' % owner.api_key
        payload['project_id'] = project2.id
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 403, data

        # As owner using wrong attribute
        url = '/api/helpingmaterial?api_key=%s' % owner.api_key
        payload['project_id'] = project2.id
        payload['foo'] = 'bar'
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # As owner using reserved key 
        url = '/api/helpingmaterial?api_key=%s' % owner.api_key
        payload['project_id'] = project.id
        payload['id'] = 3
        res = self.app.post(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 400, data
        assert data['exception_msg'] == 'Reserved keys in payload', data

    @with_context
    def test_update_helpingmaterial(self):
        """Test API HelpingMaterialpost update post (PUT)."""
        admin, user, owner = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        # As anon
        helpingmaterial.media_url = 'new'
        url = '/api/helpingmaterial/%s' % helpingmaterial.id
        res = self.app.put(url, data=json.dumps(helpingmaterial.dictize()))
        data = json.loads(res.data)
        assert res.status_code == 401, res.status_code

        # As user
        url = '/api/helpingmaterial/%s?api_key=%s' % (helpingmaterial.id, user.api_key)
        res = self.app.put(url, data=json.dumps(helpingmaterial.dictize()))
        data = json.loads(res.data)
        assert res.status_code == 403, res.status_code

        # As owner
        url = '/api/helpingmaterial/%s?api_key=%s' % (helpingmaterial.id, owner.api_key)
        payload = helpingmaterial.dictize()
        del payload['created']
        del payload['id']
        res = self.app.put(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert data['media_url'] == 'new', data

        # as owner with reserved key
        helpingmaterial.media_url = 'new'
        helpingmaterial.created = 'today'
        url = '/api/helpingmaterial/%s?api_key=%s' % (helpingmaterial.id, owner.api_key)
        payload = helpingmaterial.dictize()
        del payload['id']
        res = self.app.put(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 400, res.status_code
        assert data['exception_msg'] == 'Reserved keys in payload',  data

        # as owner with wrong key
        helpingmaterial.media_url = 'new admin'
        url = '/api/helpingmaterial/%s?api_key=%s' % (helpingmaterial.id, owner.api_key)
        payload = helpingmaterial.dictize()
        del payload['created']
        del payload['id']
        payload['foo'] = 'bar'
        res = self.app.put(url, data=json.dumps(payload))
        data = json.loads(res.data)
        assert res.status_code == 415, res.status_code
        assert 'foo' in data['exception_msg'], data

    @with_context
    @patch('pybossa.api.api_base.uploader.delete_file')
    def test_delete_helpingmaterial(self, mock_delete):
        """Test API HelpingMaterialpost delete post (DEL)."""
        mock_delete.return_value = True
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        file_info = {'file_name': 'name.jpg', 'container': 'user_3'}
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id,
                                                        info=file_info)
        helpingmaterial2 = HelpingMaterialFactory.create(project_id=project.id)

        # As anon
        url = '/api/helpingmaterial/%s' % helpingmaterial.id
        res = self.app.delete(url)
        assert res.status_code == 401, res.status_code

        # As user
        url = '/api/helpingmaterial/%s?api_key=%s' % (helpingmaterial.id, user.api_key)
        res = self.app.delete(url)
        assert res.status_code == 403, res.status_code

        # As owner
        url = '/api/helpingmaterial/%s?api_key=%s' % (helpingmaterial.id, owner.api_key)
        res = self.app.delete(url)
        assert res.status_code == 204, res.status_code
        mock_delete.assert_called_with(file_info['file_name'],
                                       file_info['container'])

        # As admin
        url = '/api/helpingmaterial/%s?api_key=%s' % (helpingmaterial2.id, admin.api_key)
        res = self.app.delete(url)
        assert res.status_code == 204, res.status_code

    @with_context
    def test_helpingmaterial_post_file(self):
        """Test API HelpingMaterialpost file upload creation."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        project2 = ProjectFactory.create(owner=user)

        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        # As anon
        url = '/api/helpingmaterial'
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 401, data
        assert data['status_code'] == 401, data

        # As a user
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/helpingmaterial?api_key=%s' % user.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data
        assert data['status_code'] == 403, data

        # As owner
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img,
                       info=json.dumps(dict(foo=1)))

        url = '/api/helpingmaterial?api_key=%s' % project.owner.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 200, data
        container = "user_%s" % owner.id
        assert data['info']['container'] == container, data
        assert data['info']['file_name'] == 'test_file.jpg', data
        assert data['info']['foo'] == 1, data
        assert 'test_file.jpg' in data['media_url'], data

        # As owner wrong 404 project_id
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/helpingmaterial?api_key=%s' % owner.api_key
        payload['project_id'] = -1
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # As owner using wrong project_id
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/helpingmaterial?api_key=%s' % owner.api_key
        payload['project_id'] = project2.id
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data

        # As owner using wrong attribute
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       wrong=img)

        url = '/api/helpingmaterial?api_key=%s' % owner.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # As owner using reserved key 
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/helpingmaterial?api_key=%s' % owner.api_key
        payload['project_id'] = project.id
        payload['id'] = 3
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 400, data
        assert data['exception_msg'] == 'Reserved keys in payload', data

    @with_context
    def test_helpingmaterial_put_file(self):
        """Test API HelpingMaterialpost file put upload works."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        project2 = ProjectFactory.create(owner=user)
        hp = HelpingMaterialFactory.create(project_id=project.id)

        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        # As anon
        url = '/api/helpingmaterial/%s' % hp.id
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 401, data
        assert data['status_code'] == 401, data

        # As a user
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/helpingmaterial/%s?api_key=%s' % (hp.id, user.api_key)
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data
        assert data['status_code'] == 403, data

        # As owner
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/helpingmaterial/%s?api_key=%s' % (hp.id,
                                                      project.owner.api_key)
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 200, data
        container = "user_%s" % owner.id
        assert data['info']['container'] == container, data
        assert data['info']['file_name'] == 'test_file.jpg', data
        assert 'test_file.jpg' in data['media_url'], data

        # As owner wrong 404 project_id
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/helpingmaterial/%s?api_key=%s' % (hp.id, owner.api_key)
        payload['project_id'] = -1
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # As owner using wrong project_id
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/helpingmaterial/%s?api_key=%s' % (hp.id, owner.api_key)
        payload['project_id'] = project2.id
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data

        # As owner using wrong attribute
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       wrong=img)

        url = '/api/helpingmaterial/%s?api_key=%s' % (hp.id, owner.api_key)
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # As owner using reserved key 
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        url = '/api/helpingmaterial/%s?api_key=%s' % (hp.id, owner.api_key)
        payload['project_id'] = project.id
        payload['id'] = 3
        res = self.app.put(url, data=payload,
                           content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 400, data
        assert data['exception_msg'] == 'Reserved keys in payload', data
