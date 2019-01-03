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
from .base import BulkTaskImport, BulkImportException
from flask_babel import gettext
from apiclient.discovery import build
from apiclient.errors import HttpError
from urllib.parse import urlparse, parse_qs
import json
import re

class BulkTaskYoutubeImport(BulkTaskImport):

    importer_id = "youtube"

    def __init__(self, playlist_url, youtube_api_server_key):
        self.playlist_url = playlist_url
        self.youtube_api_server_key = youtube_api_server_key

    def tasks(self):
        if self.playlist_url:
            playlist_id = self._get_playlist_id(self.playlist_url)
            playlist = self._fetch_all_youtube_videos(playlist_id)
            return [self._extract_video_info(item) for item in playlist['items']]
        else:
            return []

    def _extract_video_info(self, item):
        """Extract youtube video information from snippet dict"""
        video_id = item['snippet']['resourceId']['videoId']
        video_url = 'https://www.youtube.com/watch?v=' + video_id
        oembed = '<iframe width="512" height="512" ' \
            'src="https://www.youtube.com/embed/{}" ' \
            'frameborder="0" allowfullscreen></iframe>'.format(video_id)
        info = {'video_url': video_url, 'oembed': oembed}
        return {'info': info}

    def _get_playlist_id(self, url):
        """Get playlist id from url"""
        url_data = urlparse(url)
        if not (url_data.scheme):
            msg = gettext("URL is not valid.")
            raise BulkImportException(msg)
        pattern = re.compile("^(www\.)?youtu(\.be|be\.com)")
        if not (pattern.match(url_data.hostname)):
            msg = gettext("URL is not a youtube domain.")
            raise BulkImportException(msg)
        params = parse_qs(url_data.query)
        if not ('list' in params):
            msg = gettext("No playlist in URL found.")
            raise BulkImportException(msg)
        return (params['list'][0])

    def _fetch_all_youtube_videos(self, playlistId):
        """
        Fetches a playlist of videos from youtube
        We splice the results together in no particular order

        Parameters:
            parm1 - (string) playlistId
        Returns:
            playListItem Dict
        """
        YOUTUBE_API_SERVICE_NAME = "youtube"
        YOUTUBE_API_VERSION = "v3"
        youtube = build(YOUTUBE_API_SERVICE_NAME,
                        YOUTUBE_API_VERSION,
                        developerKey=self.youtube_api_server_key)
        res = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlistId,
        maxResults="50"
        ).execute()

        nextPageToken = res.get('nextPageToken')
        while ('nextPageToken' in res):
            nextPage = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlistId,
            maxResults="50",
            pageToken=nextPageToken
            ).execute()
            res['items'] = res['items'] + nextPage['items']

            if 'nextPageToken' not in nextPage:
                res.pop('nextPageToken', None)
            else:
                nextPageToken = nextPage['nextPageToken']

        return res
