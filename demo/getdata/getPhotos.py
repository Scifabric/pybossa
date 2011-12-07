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


import urllib2
import json
import datetime

url_api = 'http://0.0.0.0:5000/api/'

def createApp():
    """
    Creates the Flickr Person Finder application. First checks if the
    application already exists in PyBOSSA, otherwise it will create it.
    """

    # Data application
    name = u'Flickr Person Finder'
    short_name = u'FlickrPerson'
    description = u'Do you see a human in this photo?'
    data = dict(name = name, short_name = short_name, description = description)
    data = json.dumps(data)

    # Checking which apps have been already registered in the DB
    create_app = True
    apps = json.loads(urllib2.urlopen(url_api + 'app').read())
    for app in apps:
        if app['name'] == name: 
            print '{app_name} app is already registered in the DB'.format(app_name = name)
            return app['id']
    
    if create_app:
        print "The application is not registered in PyBOSSA. Creating it..."
        # Setting the POST action
        request = urllib2.Request(url_api + 'app')
        request.add_data(data)
        request.add_header('Content-type', 'application/json')

        # Create the app in PyBOSSA
        output = json.loads(urllib2.urlopen(request).read())
        if (output['id'] != None):
            print "Done!"
            return output['id']
        else:
            print "Error creating the application"
            return 0

def createBatch(app_id):
    """Creates a Batch of tasks for the application (app_id)"""
    # We set the name of the batch as the time and day (like in Berkeley BOSSA)
    name = datetime.datetime.now().strftime("%Y/%m/%d - %H:%M:%S")
    data = dict (name = name, app_id = app_id, calibration = 0)
    data = json.dumps(data)

    # Setting the POST action
    request = urllib2.Request(url_api + 'batch')
    request.add_data(data)
    request.add_header('Content-type', 'application/json')

    # Create the batch 
    output = json.loads(urllib2.urlopen(request).read())
    if (output['id'] != None):
        print "Batch created successfully"
        return output['id']
    else:
        return 0

def createTasks(app_id, batch_id):
    """Creates tasks for the application"""
    pass

def getFlickrPhotos(size="big"):
    # Flickr key and tag to search
    key = "1def541a422a4fe07880ab3204a1cc7e"
    tags = "rainforest"

    # Get the ID of the photos and load it in the output var
    query = "http://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=" + key + "&tags=" + tags + "&format=json&nojsoncallback=1"
    output = json.load(urllib2.urlopen(query))

    # For each photo ID create its direct URL according to its size: big, medium, small
    # (or thumbnail) + Flickr page hosting the photo
    photos = []
    for photo in output['photos']['photo']:
        # Query for getting the farm, secret, etc. for the photo
        query = "http://api.flickr.com/services/rest/?format=json&method=" + "flickr.photos.getInfo&api_key=" + key + "&photo_id=" + photo['id'] + "&secret=" + photo['secret'] + "&nojsoncallback=1";
        info = json.load(urllib2.urlopen(query))
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

app_id = createApp()
batch_id = createBatch(app_id)
