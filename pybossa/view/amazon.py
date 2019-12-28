# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
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
"""Amazon view for PYBOSSA."""
import json
from flask import Blueprint, Response
from pybossa.s3_client import S3Client, NoSuchBucket, PrivateBucket

blueprint = Blueprint('amazon', __name__)


@blueprint.route('/bucket/<string:bucket>')
def objects(bucket):
    try:
        bucket_content = S3Client().objects(bucket)
        return Response(json.dumps(bucket_content), mimetype='application/json')
    except (NoSuchBucket, PrivateBucket) as e:
        status_code = e.status_code
        error = dict(action='GET',
                     status="failed",
                     status_code=status_code,
                     exception_msg=str(e))
        return Response(json.dumps(error), status=status_code,
                        mimetype='application/json')
