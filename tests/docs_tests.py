
import unittest
from os.path import basename, splitext, dirname, join, exists
from os import walk
from glob import glob

import sverchok
from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info, error

class DocumentationTests(SverchokTestCase):

    def get_nodes_docs_directory(self):
        sv_init = sverchok.__file__
        return join(dirname(sv_init), "docs", "nodes")

    def test_unused_docs(self):
        sv_init = sverchok.__file__
        nodes_dir = join(dirname(sv_init), "nodes")
        docs_dir = self.get_nodes_docs_directory()

        def check_dir(directory):
            dir_name = basename(directory)
            bad_files = []
            for doc_path in glob(join(directory, "*.rst")):
                if doc_path.endswith("_index.rst"):
                    continue
                doc_file = basename(doc_path)
                doc_name, ext = splitext(doc_file)
                py_name = doc_name + ".py"
                py_path = join(nodes_dir, dir_name, py_name)
                if not exists(py_path):
                    bad_files.append(doc_file)

            if bad_files:
                error("Category %s: The following documentation files do not have respective python modules:\n%s", dir_name, "\n".join(bad_files))
                self.fail("There are excessive documentation files.")

        for directory, subdirs, fnames in walk(docs_dir):
            with self.subTest(directory=basename(directory)):
                check_dir(directory)

    def test_node_docs_existance(self):
        sv_init = sverchok.__file__
        nodes_dir = join(dirname(sv_init), "nodes")
        docs_dir = self.get_nodes_docs_directory()

        known_problems = """
obj_edit.py
BMOperatorsMK2.py
uv_texture.py
vertex_colors_mk3.py
sort_blenddata.py
object_raycast2.py
closest_point_on_mesh2.py
scene_raycast2.py
sculpt_mask.py
set_blenddata2.py
points_from_uv_to_mesh.py
custom_mesh_normals.py
color_uv_texture.py
filter_blenddata.py
interpolation_mk2.py
numpy_array.py
bmesh_obj_in.py
bmesh_out.py
bmesh_to_element.py
bmesh_analyzer_big.py
mesh_beautify.py
pulga_physics.py
limited_dissolve.py
limited_dissolve_mk2.py
mesh_separate_mk2.py
symmetrize.py
approx_subd_to_nurbs.py
vd_attr_node_mk2.py
scalar_field_point.py
quads_to_nurbs.py
location.py
sun_position.py""".split("\n")

        def check_category(directory):
            dir_name = basename(directory)
            bad_files = []
            known = []

            for module_path in glob(join(directory, "*.py")):
                module_file = basename(module_path)
                if module_file == "__init__.py":
                    continue
                module_name, ext = splitext(module_file)
                doc_name = module_name + ".rst"
                doc_path = join(docs_dir, dir_name, doc_name)
                if not exists(doc_path):
                    if module_file in known_problems:
                        known.append(module_file)
                    else:
                        bad_files.append(module_file)

            category = dir_name
            
            if known:
                explicitly_missing = "\n".join(known)
                info(f"{category=}: Tolerating missing documentation for the following nodes for now:\n{explicitly_missing=}")

            if bad_files:
                missing = "\n".join(bad_files)
                self.fail(f"Not all nodes of {category=} have corresponding documentation; \n{missing=}")

        for directory, subdirs, fnames in walk(nodes_dir):
            with self.subTest(directory=basename(directory)):
                check_category(directory)
