import json
import urllib
import urllib.request

def get(url):

    def get_json():
        json_to_parse = urllib.urlopen(url)
        found_json = json_to_parse.read().decode()
        wfile = json.JSONDecoder()
        return wfile.decode(found_json)        

    processed = lambda: None
    processed.json = get_json()
    return processed

