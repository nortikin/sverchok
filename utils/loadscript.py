import importlib
import importlib.abc
import importlib.util
import keyword
import sys
import inspect

import bpy
import bpy.types
from .. import nodes
from bpy.props import FloatProperty, IntProperty
from bpy.types import Node

from sverchok.node_tree import SverchCustomTreeNode


Float = FloatProperty
Int = IntProperty
Vertex = "vert"
Matrix = "matrix"
Face = "face"
Edge = "edge"

socket_types = {
    Float : "StringsSocket",
    Int : "StringsSocket",
    Vertex: "VerticesSocket",
    Matrix : "MatrixSocket",
    Face: "StringsSocket",
    Edge: "StringsSocket"
}

def get_signature(func):
    """
    Return two lists of tuple value with (type, name, dict_of_parameters)
    inputs, outputs
    """
    sig = inspect.signature(func)
    inputs_template = []
    for name, parameter in sig.parameter.items():
        if not parameter.default is None:
            socket_settings = {"default", parameter.default}
        else:
            socket_settings = {}
        socket_type = socket_types[parameter.annotation]
        inputs_template.append((name, socket_type, socket_settings))

    outputs_template = []
    for name, s_type in sig.return_annotation:
        socket_type = socket_types[s_type]
        outputs_template.append((name, socket_type))


def class_factory(func):
    cls_dict = {}
    module_name = func.__module__.split(".")[-1]
    cls_name = "SvScriptMK3_{}".format(func.__name__)

    input_template, output_template = get_signature(func)

    cls_dict["bl_idname"] = cls_name

    # draw etc
    cls_dict["bl_label"] = func.label if hasattr(func, "label") else func.__name__

    cls_dict["input_template"] = input_template
    cls_dict["output_template"] = output_template
    cls_dict["node_function"] = func

    bases = (SvScriptBase, SverchCustomTreeNode, Node)
    cls = type(cls_name, bases, cls_dict)



class SvScriptBase:
    """Base class for Script nodes"""

    module = StringProperty()

    def process(self):
        args = [s.sv_get() for s in self.inputs]
        # also have to deal with properties
        results = self.node_function(*args)

        for s, data in zip(self.outputs, results):
            if s.is_linked:
                s.sv_set(data)

    def sv_init(self, context):
        for socket_name, socket_bl_idname, prop_data in self.input_template:
            s = self.inputs.new(socket_bl_idname, socket_name)
            for name, value in prop_data.items():
                setattr(s, name, value)

        for socket_name, socket_bl_idname in self.output_template:
            self.outputs.new(socket_bl_idname, socket_name)



def node_func(*args, **values):
    def real_node_func(func):
        def annotate(func):
            for key, value in values.items():
                setattr(func, key, value)
            return func
        annotate(func)
        return func
    if args and callable(args[0]):
        return real_node_func(args[0])
    else:
        return real_node_func


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
    #global _script_modules
    #global _name_lookup

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

standard_header = """
from sverchok.utils.loadscript import (node_func, Int, Float, Vertex, Matrix, Face, Edge)
"""
# should be auto created .format(socket_types.keys())

standard_footer = """
def register():
    bpy.utils.register_class(_class)

def unregister():
    bpy.utils.unregister_class(_class)
"""


def script_preprocessor(text):
    lines = []
    inserted_header = False
    # try to be clever not upset line no reporting in exceptions
    for line in text.lines:
        if "@node_func" in line.body and not inserted_header:
            lines.append(standard_header)
            inserted_header = True

        if not line.body.strip() and not inserted_header:
            lines.append(inserted_header)
            inserted_header = True
            continue

        lines.append(line.body)

    lines.append(standard_footer)
    return "\n".join(lines)

class SvLoader(importlib.abc.SourceLoader):

    def __init__(self, text):
        self._text = text

    def get_data(self, path):
        # here we should insert things and preprocss the file to make it valid
        source = "".join(standard_header, bpy.data.texts[self._text].as_string(), standard_footer)
        return source

    def get_filename(self, fullname):
        return "<bpy.data.texts[{}]>".format(self._text)


def register():
    sys.meta_path.append(SvFinder())


def unregister():
    for mod in _script_modules.values():
        mod.unregister()

    for finder in sys.meta_path[:]:
        if isinstance(finder, SvFinder):
            sys.meta_path.remove(finder)
