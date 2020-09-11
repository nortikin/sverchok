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
    root_path = str(Path(module.__file__).parent)
    for module_name in iter_submodule_names(root_path):
        nest_module = sys.modules.get(path + '.' + root_path + module_name, None)
        if nest_module is None:
            print("Looks like some module was not imported")
        else:
            clses = inspect.getmembers(nest_module, inspect.isclass)
            for _, cls in clses:
                if any(base in base_types for base in cls.__bases__):
                    yield cls


def iter_submodule_names(path, depth=0, root="", current_depth=1):
    """
    Return all sub modules of given module (all sub folders of given folder)
    :param path: absolute path - str
    :param depth: 0 means it returns all submodules, if 1 it returns only modules from given directory, if 2 ... so on
    :param root: for internal work
    :param current_depth: for internal work
    :return: module name - str
    """
    for _, module_name, is_package in pkgutil.iter_modules([str(path)]):
        if is_package and (depth == 0 or current_depth < depth):
            sub_path = f'{path} // {module_name}' 
            sub_root = root + module_name + "."
            yield from iter_submodule_names(sub_path, depth=depth, root=sub_root, current_depth=current_depth + 1)
        else:
            yield module_name
