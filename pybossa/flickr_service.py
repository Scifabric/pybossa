# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SF Isle of Man Limited
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
"""Flickr module for authentication."""
from flask_oauthlib.client import OAuth
import functools


class FlickrService(object):

    """Class for Flickr integration."""

    def __init__(self, app=None):
        """Init method."""
        self.app = app
        self.client = None
        if app is not None:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):  # pragma: no cover
        """Method to init object following factories pattern."""
        from flask import session
        from pybossa.core import importer
        self.app = app
        self.client = OAuth().remote_app(
            'flickr',
            request_token_url='https://www.flickr.com/services/oauth/request_token',
            access_token_url='https://www.flickr.com/services/oauth/access_token',
            authorize_url='https://www.flickr.com/services/oauth/authorize',
            consumer_key=app.config['FLICKR_API_KEY'],
            consumer_secret=app.config['FLICKR_SHARED_SECRET'],
            access_token_method='GET')
        tokengetter = functools.partial(self.get_token, session)
        self.client.tokengetter(tokengetter)
        importer_params = {'api_key': app.config['FLICKR_API_KEY']}
        importer.register_flickr_importer(importer_params)

    def get_user_albums(self, session):
        """Get user albums from Flickr."""
        if (session.get('flickr_user') is not None and
                session.get('flickr_token') is not None):
            url = ('https://api.flickr.com/services/rest/?'
                   'method=flickr.photosets.getList&user_id=%s'
                   '&primary_photo_extras=url_q'
                   '&format=json&nojsoncallback=1'
                   % self._get_user_nsid(session))
            res = self.client.get(url, token='')
            if res.status == 200 and res.data.get('stat') == 'ok':
                albums = res.data['photosets']['photoset']
                return [self._extract_album_info(album) for album in albums]
            if self.app is not None:
                msg = ("Bad response from Flickr:\nStatus: %s, Content: %s"
                       % (res.status, res.data))
                self.app.logger.error(msg)
        return []

    def authorize(self, *args, **kwargs):
        """Authorize method."""
        return self.client.authorize(*args, **kwargs)

    def authorized_response(self):
        """Authorized response."""
        return self.client.authorized_response()

    def get_oauth_client(self):
        """Get OAuth client."""
        return self.client

    def get_token(self, session):
        """Get token from session."""
        token = session.get('flickr_token')
        if token is not None:
            token = (token['oauth_token'], token['oauth_token_secret'])
        return token

    def save_credentials(self, session, token, user):
        """Save credentials of user in session."""
        session['flickr_token'] = token
        session['flickr_user'] = user

    def remove_credentials(self, session):
        """Remove user credentials from session."""
        session.pop('flickr_token', None)
        session.pop('flickr_user', None)

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
