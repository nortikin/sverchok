# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import sys
import inspect
import pkgutil
from pathlib import Path


def iter_classes_from_module(module, base_types):
    """
    Iterate over all classes of given module which have base_type in parent classes
    nested modules are also scanned
    :param module: for example: sverchok.utils
    :param base_types: for example: [bpy.types.Node]
    :return: class
    """
    path = module.__name__
    for module_name in iter_submodule_names(Path(module.__file__).parent):
        nest_module = sys.modules.get(path + '.' + module_name, None)
        if nest_module is None:
            print("Looks like some module was not imported")
        else:
            clses = inspect.getmembers(nest_module, inspect.isclass)
            for _, cls in clses:
                if any(base in base_types for base in cls.__bases__):
                    yield cls


def iter_submodule_names(path, root=""):
    """
    Return all sub modules of given module (all sub folders of given folder)
    :param path: absolute path - str
    :param root: for internal work
    :return: module name - str
    """
    for _, module_name, is_package in pkgutil.iter_modules([str(path)]):
        if is_package:
            sub_path = path / module_name
            sub_root = root + module_name + "."
            yield from iter_submodule_names(sub_path, sub_root)
        else:
            yield root + module_name
