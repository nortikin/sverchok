# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import json
import urllib.request as rq


# we dont use requests for anything significant other than getting 
# a json, this is a dummy module with one feature implemented (.get )


def get(url):

    def get_json():
        json_to_parse = rq.urlopen(url)
        found_json = json_to_parse.read().decode()
        wfile = json.JSONDecoder()
        return wfile.decode(found_json)        

    processed = lambda: None
    processed.json = get_json
    return processed

