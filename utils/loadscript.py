import importlib
import importlib.abc
import importlib.util
import keyword
import sys

import bpy
import bpy.types
from .. import nodes

_script_modules = {}
_name_lookup = {}

def make_valid_identifier(name):
    """Create a valid python identifier from name for use a a part of class name"""
    if not name[0].isalpha():
        name = "Sv" + name
    return "".join(ch for ch in name if ch.isalnum() or ch == "_")

def load_script(text):
    """
    Will load the blender text file as a module in nodes.script
    """
    global _script_modules
    global _name_lookup

    if text.endswith(".py"):
        name = text.rstrip(".py")
    else:
        name = text

    if not name.isidentifier() or keyword.iskeyword(name):
        print("bad text name: {}".format(text))
        return

    name = make_valid_identifier(name)
    _name_lookup[name] = text

    # we should introduce simple auto renamning or name mangling system
    if name in _script_modules:
        mod = _script_modules[name]
        importlib.reload(mod)
    else:
        mod = importlib.import_module("sverchok.nodes.script.{}".format(name))
        _script_modules[name] = mod


    return
    # here we need to deal with module, class registration and similar things

class SvFinder(importlib.abc.MetaPathFinder):

    def find_spec(self, fullname, path, target=None):
        if fullname.startswith("sverchok.nodes.script."):
            name = fullname.split(".")[-1]
            text_name = _name_lookup.get(name, "")
            print(name, text_name)
            if text_name in bpy.data.texts:
                print("what")
                return importlib.util.spec_from_loader(fullname, SvLoader(text_name))
            else:
                print("noep")

        elif fullname == "sverchok.nodes.script":
            # load Module, right now uses real but empty module, will perhaps change
            pass

        return None


class SvLoader(importlib.abc.SourceLoader):

    def __init__(self, text):
        self._text = text

    def get_data(self, path):
        # here we should insert things and preprocss the file to make it valid
        return bpy.data.texts[self._text].as_string()

    def get_filename(self, fullname):
        return "<bpy.data.texts[{}]>".format(self._text)


sys.meta_path.append(SvFinder())
