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
"""Flickr module for authentication."""
from flask_oauthlib.client import OAuth
import functools
import requests


class FlickrClient(object):

    """Class for Flickr integration."""

    def __init__(self, api_key, logger=None):
        self.api_key = api_key
        self.logger = logger

    def get_user_albums(self, session):
        """Get user albums from Flickr."""
        if session.get('flickr_user') is not None:
            url = 'https://api.flickr.com/services/rest/'
            payload = {'method': 'flickr.photosets.getList',
                       'api_key': self.api_key,
                       'user_id': self._get_user_nsid(session),
                       'format': 'json',
                       'primary_photo_extras':'url_q',
                       'nojsoncallback': '1'}
            res = requests.get(url, params=payload)
            if res.status_code == 200 and res.json().get('stat') == 'ok':
                albums = res.json()['photosets']['photoset']
                return [self._extract_album_info(album) for album in albums]
            if self.logger is not None:
                msg = ("Bad response from Flickr:\nStatus: %s, Content: %s"
                       % (res.status_code, res.json()))
                self.logger.error(msg)
        return []

    def _get_user_nsid(self, session):
        """Get session ID."""
        return session.get('flickr_user').get('user_nsid')

    def _extract_album_info(self, album):
        """Extract album information."""
        info = {'title': album['title']['_content'],
                'photos': album['photos'],
                'id': album['id'],
                'thumbnail_url': album['primary_photo_extras']['url_q']}
        return info
