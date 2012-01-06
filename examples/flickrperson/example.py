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

def create_app(name=None, short_name=None, description=None):
    """
    Creates the Flickr Person Finder application. 

    :arg string name: The application name.
    :arg string short_name: The slug application name.
    :arg string description: A short description of the application. 

    :returns: Application ID or 0 in case of error.
    :rtype: integer
    """
    print('Creating app')
    name = u'Flickr Person Finder'
    short_name = u'FlickrPerson'
    description = u'Do you see a human in this photo?'
    data = dict(name = name, short_name = short_name, description = description)
    data = json.dumps(data)

    # Checking which apps have been already registered in the DB
    apps = json.loads(urllib2.urlopen(url_api + 'app').read())
    for app in apps:
        if app['name'] == name: 
            print('{app_name} app is already registered in the DB'.format(app_name = name))
            return app['id']
    print("The application is not registered in PyBOSSA. Creating it...")
    # Setting the POST action
    request = urllib2.Request(url_api + 'app')
    request.add_data(data)
    request.add_header('Content-type', 'application/json')

    # Create the app in PyBOSSA
    output = json.loads(urllib2.urlopen(request).read())
    if (output['id'] != None):
        print("Done!")
        return output['id']
    else:
        print("Error creating the application")
        return 0

def create_batch(app_id):
    """
    Creates a Batch of tasks for the application (app_id)

    :arg string app_id: Application ID in PyBossa.
    :returns: PyBossa Batch ID or 0 in case of an error.
    :rtype: integer
    """
    print('Creating batch with app id: %s' % app_id)
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
        print("Batch created successfully")
        return output['id']
    else:
        return 0

def create_task(app_id, batch_id, photo):
    """
    Creates tasks for the application

    :arg integer app_id: Application ID in PyBossa.
    :arg integer batch_id: Batch ID in PyBossa.
    :returns: Task ID in PyBossa.
    :rtype: integer
    """
    # Data for the tasks
    info = dict (link = photo['link'], url = photo['url'])
    data = dict (app_id = app_id, batch_id = batch_id, state = 0, info = info, calibration = 0, priority_0 = 0)
    data = json.dumps(data)

    # Setting the POST action
    request = urllib2.Request(url_api + 'task')
    request.add_data(data)
    request.add_header('Content-type', 'application/json')

    # Create the task
    output = json.loads(urllib2.urlopen(request).read())
    if (output['id'] != None):
        return True
    else:
        return False

def get_flickr_photos(size="big"):
    """
    Gets public photos from Flickr feeds
    
    :arg string size: Size of the image that should be obtained from Flickr feed. 
    :returns: A list of photos.
    :rtype: list
    """
    # Get the ID of the photos and load it in the output var
    print('Contacting Flickr for photos')
    query = "http://api.flickr.com/services/feeds/photos_public.gne?nojsoncallback=1&format=json"
    urlobj = urllib2.urlopen(query)
    data = urlobj.read()
    urlobj.close()
    output = json.loads(data)
    print('Data retrieved from Flickr')

    # For each photo ID create its direct URL according to its size: big, medium, small
    # (or thumbnail) + Flickr page hosting the photo
    photos = []
    for idx, photo in enumerate(output['items']):
        print 'Retrieved photo: %s' % idx
        photos.append({'link': photo["link"], 'url':  photo["media"]["m"]})
    return photos

if __name__ == "__main__":
    app_id = create_app()
    # First of all we get the URL photos
    # WARNING: Sometimes the flickr feed returns a wrong escape character, so it may
    # fail at this step
    photos = get_flickr_photos()
    # Then, we have to create a bag of tasks (a Batch in BOSSA terminology)
    batch_id = create_batch(app_id)
    # Finally, we have to create a set of tasks for the application and batch
    # For this, we get first the photo URLs from Flickr
    for photo in photos:
        create_task(app_id, batch_id, photo)

