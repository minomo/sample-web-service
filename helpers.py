# Original code of this file was published under the following lisence at
# https://github.com/google/physical-web/
#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.appengine.api import urlfetch, app_identity
import json
import logging


BASE_URL = 'https://' + app_identity.get_application_id() + '.appspot.com'


def GetConfig():
    import os.path
    if os.path.isfile('config.SECRET.json'):
        fname = 'config.SECRET.json'
    else:
        fname = 'config.SAMPLE.json'
    with open(fname) as configfile:
        return json.load(configfile)


def ShortenUrl(longUrl):
    config = GetConfig()
    apikey = config['oauth_keys']['goo.gl']
    url = 'https://www.googleapis.com/urlshortener/v1/url?key=' + apikey
    try:
        result = urlfetch.fetch(url,
                                validate_certificate=True,
                                method=urlfetch.POST,
                                payload=json.dumps({'longUrl': longUrl}),
                                headers={
                                    'Content-Type': 'application/json',
                                    'Referer': BASE_URL,
                                })

        if result.status_code == 200:
            return json.loads(result.content).get('id')
        else:
            logging.error('Bad response from %s. status is %u' %
                          (url, result.status_code))

    except urlfetch.Error as e:
        logging.exception(e)

    return None
