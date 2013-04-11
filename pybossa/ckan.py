import requests
import json


class Ckan(object):

    def __init__(self, url, api_key):
        self.url = url
        self.headers = {'Authorization': api_key,
                        'Content-type': 'application/json'}
        self.package = None
        self.resource = dict(task=None, task_run=None)

    def package_exists(self, name):
        pkg = {'id': name}
        r = requests.get(self.url + "/action/package_show",
                         headers=self.headers,
                         params=pkg)
        output = r.json()
        if output.get('success'):
            self.package = output['result']
            return output['result']
        else:
            return False

    def package_create(self, app, user, url):
        pkg = {'name': app.short_name,
               'title': app.name,
               'author': user.fullname,
               'url': url}
        r = requests.post(self.url + "/action/package_create",
                          headers=self.headers,
                          data=json.dumps(pkg))
        self.package = r.json()
        return self.package

    def resource_create(self, name):
        print self.package
        rsrc = {'package_id': self.package['id'],
                'url': self.package['url'],
                'description': name}
        print rsrc
        r = requests.post(self.url + "/action/resource_create",
                          headers=self.headers,
                          data=json.dumps(rsrc))
        print r.text
        print r.json()
        self.resource[name] = r.json()
        return self.resource[name]
