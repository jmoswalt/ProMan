from urllib2 import Request, urlopen
import base64

from django.conf import settings
from django.utils import simplejson as json

class Harvest(object):
    def __init__(self):
        base_url = getattr(settings, 'HV_URL', None)
        api_user = getattr(settings, 'HV_USER', None)
        api_pass = getattr(settings, 'HV_PASS', None)
        self.base_url = base_url
        self.headers = {
            'Authorization': 'Basic %s' % (
                base64.b64encode('%s:%s' % (api_user, api_pass))),
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            }

    def _request(self, url):
        request = Request(
            url=self.base_url + url,
            headers=self.headers
            )

        response = urlopen(request)
        json_data = json.loads(response.read())
        if json_data:
            #data = [a for a in json_data]
            return json_data
        return None

    def projects(self, id=None):
        if id:
            return self._request('/projects/%s' % id)
        return self._request('/projects')

    def project_entries(self, id=None, start=None, end=None, billable=None):
        url = '/projects/%s/entries?from=%s&to=%s' % (id, start, end)
        if billable:
            url += "&billable=%s" % billable
        return self._request(url)

    def clients(self, id=None):
        if id:
            return self._request('/clients/%s' % id)
        return self._request('/clients')

    def client_contacts(self, id=None):
        if id:
            return self._request('/contacts/%s' % id)
        return self._request('/contacts')

    def users(self, id=None):
        if id:
            return self._request('/people/%s' % id)
        return self._request('/people')

def get_harvest_json(api_url):
    base_url = getattr(settings, 'HV_URL', None)
    api_user = getattr(settings, 'HV_USER', None)
    api_pass = getattr(settings, 'HV_PASS', None)
    
    if base_url and api_user and api_pass:
        url = base_url + api_url
        req = Request(url)
        req.add_header('Accept', 'application/json')
        req.add_header("Content-type", "application/json")
        req.add_header('Authorization', "Basic " + (api_user +":"+ api_pass).encode("base64").rstrip())
        res = urlopen(req)
        json_data = json.loads(res.read())
        return json_data
    return None