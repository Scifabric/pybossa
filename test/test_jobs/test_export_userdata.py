# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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
from default import Test, with_context, FakeResponse
from factories import UserFactory, ProjectFactory, TaskRunFactory
from pybossa.jobs import export_userdata, send_mail
from pybossa.core import user_repo
from pybossa.exporter.json_export import JsonExporter
from mock import patch, MagicMock
from flask import current_app, render_template, url_for
from flask_mail import Message

#@patch('pybossa.jobs.uploader')
class TestExportAccount(Test):

    @with_context
    @patch('pybossa.exporter.json_export.scheduler')
    @patch('pybossa.exporter.json_export.uploader')
    @patch('uuid.uuid1', return_value='random')
    @patch('pybossa.jobs.Message')
    @patch('pybossa.jobs.send_mail')
    # @patch('pybossa.jobs.JsonExporter')
    def test_export(self, m1, m2, m3, m4, m5):
        """Check email is sent to user."""
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        taskrun = TaskRunFactory.create(user=user)

        m4.delete_file.return_value = True

        export_userdata(user.id)

        upload_method = 'uploads.uploaded_file'

        personal_data_link = url_for(upload_method,
                                     filename="user_%s/%s_sec_personal_data.zip"
                                     % (user.id, 'random'),
                                     _external=True)
        personal_projects_link = url_for(upload_method,
                                         filename="user_%s/%s_sec_user_projects.zip"
                                         % (user.id, 'random'),
                                         _external=True)
        personal_contributions_link = url_for(upload_method,
                                              filename="user_%s/%s_sec_user_contributions.zip"
                                              % (user.id, 'random'),
                                              _external=True)


        body = render_template('/account/email/exportdata.md',
                           user=user.dictize(),
                           personal_data_link=personal_data_link,
                           personal_projects_link=personal_projects_link,
                           personal_contributions_link=personal_contributions_link,
                           config=current_app.config)

        html = render_template('/account/email/exportdata.html',
                           user=user.dictize(),
                           personal_data_link=personal_data_link,
                           personal_projects_link=personal_projects_link,
                           personal_contributions_link=personal_contributions_link,
                           config=current_app.config)
        subject = 'Your personal data'
        mail_dict = dict(recipients=[user.email_addr],
                     subject=subject,
                     body=body,
                     html=html)
        m1.assert_called_with(mail_dict)
        assert 'https' in personal_contributions_link

    @with_context
    @patch('pybossa.core.uploader.delete_file')
    def test_delete_file(self, m1):
        """Test delete file works."""
        from pybossa.jobs import delete_file
        delete_file('f', 'a')
        m1.assert_called_with('f', 'a')
