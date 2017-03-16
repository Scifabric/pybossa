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
# Cache global variables for timeouts
"""
Local module for uploading files to a PYBOSSA local filesystem.

This module exports:
    * Local class: for uploading files to a local filesystem.

"""
import pyrax
import traceback
import time
from flask import current_app, url_for
from pybossa.core import timeouts
from pybossa.cache import memoize
from pybossa.uploader import Uploader
from werkzeug import secure_filename

class RackspaceUploader(Uploader):

    """Rackspace Cloud Files uploader class."""

    cf = None
    cont_name = 'pybossa'

    def init_app(self, app, cont_name=None):
        """Init method to create a generic uploader."""
        super(self.__class__, self).init_app(app)
        try:
            pyrax.set_setting("identity_type", "rackspace")
            pyrax.set_credentials(username=app.config['RACKSPACE_USERNAME'],
                                  api_key=app.config['RACKSPACE_API_KEY'],
                                  region=app.config['RACKSPACE_REGION'])
            self.cf = pyrax.cloudfiles
            if cont_name:
                self.cont_name = cont_name
            return self.cf.get_container(self.cont_name)
        except pyrax.exceptions.NoSuchContainer:
            c = self.cf.create_container(self.cont_name)
            self.cf.make_container_public(self.cont_name)
            return c

    def get_container(self, name):
        """Create a container for the given asset."""
        try:
            return self.cf.get_container(name)
        except pyrax.exceptions.NoSuchContainer:
            c = self.cf.create_container(name)
            self.cf.make_container_public(name)
            return c

    def _upload_file_to_rackspace(self, file, container, attempt=0):
        """Upload file to rackspace."""
        try:
            chksum = pyrax.utils.get_checksum(file)
            self.cf.upload_file(container,
                                file,
                                obj_name=secure_filename(file.filename),
                                etag=chksum)
            return True
        except Exception as e:
            print("Uploader exception")  # TODO: Log this!
            traceback.print_exc()
            attempt += 1
            if (attempt < 3):
                time.sleep(1)   # Wait one second and try again
                return self._upload_file_to_rackspace(file, container, attempt)
            else:
                print("Tried to upload two times. Failed!")   # TODO: Log this!
                raise

    def _upload_file(self, file, container):
        """Upload a file into a container."""
        try:
            cnt = self.get_container(container)
            obj = cnt.get_object(file.filename)
            obj.delete()
            return self._upload_file_to_rackspace(file, container)
        except pyrax.exceptions.NoSuchObject:
            return self._upload_file_to_rackspace(file, container)
        except pyrax.exceptions.UploadFailed:
            return False

    @memoize(timeout=timeouts.get('AVATAR_TIMEOUT'))
    def _lookup_url(self, endpoint, values):
        """Return Rackspace URL for object."""
        try:
            # Create failover urls for avatars
            if '_avatar' in values['filename']:
                failover_url = url_for('static',
                                       filename='img/placeholder.user.png')
            else:
                failover_url = url_for('static',
                                       filename='img/placeholder.project.png')
            cont = self.get_container(values['container'])
            if cont.cdn_enabled:
                return "%s/%s" % (cont.cdn_ssl_uri, values['filename'])
            else:
                msg = ("Rackspace Container %s was not public"
                       % values['container'])
                current_app.logger.warning(msg)
                cont.make_public()
                return "%s/%s" % (cont.cdn_ssl_uri, values['filename'])
        except:
            current_app.logger.error(traceback.print_exc())
            return failover_url

    def delete_file(self, name, container):
        """Delete file from container."""
        try:
            cnt = self.get_container(container)
            obj = cnt.get_object(name)
            obj.delete()
            return True
        except:
            return False

    def file_exists(self, name, container):
        """Check if a file exists in a container"""
        try:
            cnt = self.get_container(container)
            obj = cnt.get_object(name)
            return obj is not None
        except pyrax.exceptions.NoSuchObject:
            return False
