# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2016 SciFabric LTD.
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

import boto3

class S3Client(object):

    def __init__(self, role_ARN, identity_token, username=''):
        sts = boto3.client('sts')
        response = sts.assume_role_with_web_identity(
            RoleArn=role_ARN,
            RoleSessionName=username,
            WebIdentityToken=identity_token,
            ProviderId='www.amazon.com'
        )
        print response
        self.credentials = response['Credentials']
        session = boto3.session.Session(
                    aws_access_key_id=self.credentials['AccessKeyId'],
                    aws_secret_access_key=self.credentials['SecretAccessKey'],
                    aws_session_token=self.credentials['SessionToken'])
        s3 = session.resource('s3')
