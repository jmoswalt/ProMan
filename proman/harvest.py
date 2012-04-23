from urllib2 import Request, urlopen

from django.conf import settings
from django.utils import simplejson as json

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