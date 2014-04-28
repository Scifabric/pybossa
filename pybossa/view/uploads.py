# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
"""
PyBossa Uploads view for LocalUploader application.

This module serves uploaded content like avatars.

"""
from flask import Blueprint, send_from_directory
from pybossa.core import uploader


blueprint = Blueprint('uploads', __name__)

@blueprint.route('/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(uploader.upload_folder, filename)
