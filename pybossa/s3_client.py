# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2016 Scifabric LTD.
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

import requests
from xml.dom import minidom


class S3Client(object):

    def objects(self, bucket_name):
        response = requests.get('https://%s.s3.amazonaws.com/' % bucket_name)
        if response.status_code == 404:
            raise NoSuchBucket('Bucket "%s" does not exist' % bucket_name)
        if response.status_code == 403:
            raise PrivateBucket('Bucket "%s" is private' % bucket_name)
        xml_data = minidom.parseString(response.text)
        contents = xml_data.getElementsByTagName('Contents')
        return [content.getElementsByTagName('Key')[0].firstChild.nodeValue
            for content in contents if not self._is_folder(content)]

    def _is_folder(self, content):
        size = content.getElementsByTagName('Size')[0].firstChild.nodeValue
        name = content.getElementsByTagName('Key')[0].firstChild.nodeValue
        return name.endswith('/') and size == '0'

class NoSuchBucket(Exception):
    status_code = 404

class PrivateBucket(Exception):
    status_code = 403
