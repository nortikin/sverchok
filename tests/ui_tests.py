
from os import walk
from os.path import basename, splitext, dirname, join, exists
from glob import glob
import importlib
from inspect import getmembers, isclass

import sverchok
from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info, error
from sverchok.node_tree import SverchCustomTreeNode

class UiTests(SverchokTestCase):
    def test_all_nodes_have_icons(self):
        def has_icon(node_class):
            has_sv_icon = hasattr(node_class, "sv_icon") 
            has_bl_icon = hasattr(node_class, "bl_icon") and node_class.bl_icon and node_class.bl_icon != 'OUTLINER_OB_EMPTY'
            #debug("Icon: %s: BL %s, SV %s", node_class.__name__, getattr(node_class, 'bl_icon', None), getattr(node_class, 'sv_icon', None))
            return has_sv_icon or has_bl_icon

        ignore_list = [
                    'SvGroupInputsNode',
                    'SvGroupNode',
                    'SvGroupOutputsNode',
                    'SvIterationNode',
                    'SvGroupInputsNodeExp',
                    'SvGroupOutputsNodeExp',
                    'SvMonadGenericNode',
                    'SvMonadInfoNode',
                ]
        
        sv_init = sverchok.__file__
        nodes_dir = join(dirname(sv_init), "nodes")

        def check_category(directory):
            category = basename(directory)
            from sverchok.node_tree import SverchCustomTreeNode
            for py_path in glob(join(directory, "*.py")):
                py_file = basename(py_path)
                py_name, ext = splitext(py_file)
                module = importlib.import_module(f"sverchok.nodes.{category}.{py_name}")
                for node_class_name, node_class in getmembers(module, isclass):
                    if node_class.__module__ != module.__name__:
                        continue
                    if node_class_name in ignore_list:
                        continue
                    debug("Check: %s: %s: %s", node_class, node_class.__bases__, SverchCustomTreeNode in node_class.__bases__)
                    if SverchCustomTreeNode in node_class.mro():
                        with self.subTest(node = node_class_name):
                            if not has_icon(node_class):
                                self.fail(f"Node <{node_class_name}> does not have icon!")

        for directory, subdirs, fnames in walk(nodes_dir):
            dir_name = basename(directory)
            if dir_name == "nodes":
                continue
            with self.subTest(directory=dir_name):
                check_category(directory)

