#!/usr/bin/env python 
# -*- coding: utf-8 -*-

# This file is part of PyBOSSA.
# 
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.


import urllib
import json

def getFlickrPhotos(size="big"):
        # Flickr key and tag to search
        key = "1def541a422a4fe07880ab3204a1cc7e"
        tags = "rainforest"
        
        # Get the ID of the photos and load it in the output var
        query = "http://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=" + key + "&tags=" + tags + "&format=json&nojsoncallback=1"
        output = json.load(urllib.urlopen(query))
        
        # For each photo ID create its direct URL according to its size: big, medium, small
        # (or thumbnail) + Flickr page hosting the photo
        photos = []
        for photo in output['photos']['photo']:
                # Query for getting the farm, secret, etc. for the photo
                query = "http://api.flickr.com/services/rest/?format=json&method=" + "flickr.photos.getInfo&api_key=" + key + "&photo_id=" + photo['id'] + "&secret=" + photo['secret'] + "&nojsoncallback=1";
                info = json.load(urllib.urlopen(query))
                # Base URL for creating the URLs according to its size
                baseURL = 'http://farm' + str(info['photo']['farm']) + '.static.flickr.com/' + str(info['photo']['server']) + '/' + str(info['photo']['id']) + '_' + str(info['photo']['secret'])
                if (size == "big"):
                        PhotoURL = baseURL + '_b.jpg'
                elif (size == "medium"):
                        PhotoURL = baseURL + '_m.jpg'                                                                                                              
                else:
                        PhotoURL = baseURL + '_s.jpg'
                # Flickr Page hosting the photo (with all the Flickr goodies)
                # PhotoFlickrPage = 'http://www.flickr.com/photos/' + str(info['photo']['owner']['nsid']) + '/' + str(info['photo']['id'])
                photos.append(PhotoURL)
        return photos

photos = getFlickrPhotos()

for url in photos:
        print url
