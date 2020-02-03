# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import os
import ssl
import json
import urllib.request as rq

# version of urllib.request.urlopen()
# which handles certificate issues properly
def urlopen(url, **kwargs):

    def certifi_open(url, **kwargs):
        try:
            import certifi
            ssl_context = ssl.create_default_context(cafile = os.path.relpath(certifi.where()))
            return rq.urlopen(url, context=ssl_context, **kwargs)
        except ImportError:
            return rq.urlopen(url, **kwargs)

    if os.name == 'posix':
        return certifi_open(url, **kwargs)
    else:
        return rq.urlopen(url, **kwargs)

# version of urllib.request.urlretrieve()
# which handles certificate issues properly
def urlretrieve(url, filename, **kwargs):

    def certifi_retrieve(url, filename, **kwargs):
        try:
            import certifi
            ssl_context = ssl.create_default_context(cafile = os.path.relpath(certifi.where()))
            return rq.urlretrieve(url, filename, context=ssl_context, **kwargs)
        except ImportError:
            return rq.urlretrieve(url, filename, **kwargs)

    if os.name == 'posix':
        return certifi_retrieve(url, filename, **kwargs)
    else:
        return rq.urlretrieve(url, filename, **kwargs)

# we dont use requests for anything significant other than getting 
# a json, this is a dummy module with one feature implemented (.get )
def get(url):

    def get_json():
        json_to_parse = urlopen(url)
        found_json = json_to_parse.read().decode()
        wfile = json.JSONDecoder()
        return wfile.decode(found_json)        

    processed = lambda: None
    processed.json = get_json
    return processed

