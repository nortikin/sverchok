# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import sverchok
import sys
import inspect
from pathlib import Path


def iter_classes_from_module(module, base_types):
    """
    Iterate over all classes of given module which have base_type in parent classes
    nested modules are also scanned
    :param module: for example: sverchok.utils
    :param base_types: for example: [bpy.types.Node]
    :return: class
    """
    module_root = Path(module.__file__).parent
    sv_root = Path(sverchok.__file__).parent
    for path in module_root.rglob('*.py'):
        relative_path = path.relative_to(sv_root.parent).with_suffix('')
        relative_address = ".".join(relative_path.parts)
        nest_module = sys.modules.get(relative_address, None)
        if nest_module is None:
            pass
            # print(f'Looks like module="{relative_address}" was not imported')
        else:
            classes = inspect.getmembers(nest_module, inspect.isclass)
            for _, cls in classes:
                if any(base in base_types for base in cls.__bases__):
                    yield cls


def iter_submodule_names(path: Path, depth=0, _current_depth=1):
    """
    Return all sub modules of given module (all sub folders of given folder)
    :param path: Path object from 'pathlib' module, for example root path of Sverchok Path(sverchok.__file__).parent
    :param depth: 0 means it returns all submodules, if 1 it returns only modules from given directory, if 2 ... so on
    :param _current_depth: for internal work
    :return: module name - str
    """
    for sub_path in path.iterdir():
        if sub_path.is_dir() and (depth == 0 or _current_depth < depth):
            yield from iter_submodule_names(sub_path, depth=depth, _current_depth=_current_depth + 1)
        else:
            if sub_path.suffix == '.py':
                yield sub_path.stem
