
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

    def test_all_node_docs_in_trees(self):
        """
        Check that each node documentation file is mentioned in corresponding index file.
        """

        def check(index_file_path, doc_file_path):
            (name, ext) = splitext(basename(doc_file_path))
            found = False
            with open(index_file_path, 'r') as index:
                for line in index:
                    line = line.strip()
                    if line == name:
                        found = True
                        break
            return found

        def check_dir(directory, fnames):
            dir_name = basename(directory)
            index_name = dir_name + "_index.rst"
            index_file_path = join(directory, index_name)
            bad_files = []
            for fname in fnames:
                if fname.endswith("_index.rst"):
                    continue
                if not check(index_file_path, fname):
                    bad_files.append(fname)
            if bad_files:
                self.fail("Not all node documentation files are mentioned in their corresponding indexes for category `{}'; missing are:\n{}".format(index_name, "\n".join(bad_files)))

        docs_dir = self.get_nodes_docs_directory()

        for directory, subdirs, fnames in walk(docs_dir):
            with self.subTest(directory=basename(directory)):
                check_dir(directory, fnames)

    def test_node_docs_refs_from_trees(self):

        def check_dir(directory):
            dir_name = basename(directory)
            index_name = dir_name + "_index.rst"
            index_file_path = join(directory, index_name)
            bad_files = []

            if exists(index_file_path):
                with open(index_file_path, 'r') as index:
                    start = False
                    for line in index:
                        line = line.strip()
                        if not line:
                            continue
                        if ":maxdepth:" in line:
                            start = True
                            continue
                        if not start:
                            continue
                        doc_name = line + ".rst"
                        doc_path = join(directory, doc_name)
                        if not exists(doc_path):
                            bad_files.append(doc_name)

                if bad_files:
                    self.fail("The following files, which are referenced from {}, do not exist:\n{}".format(index_name, "\n".join(bad_files)))

        docs_dir = self.get_nodes_docs_directory()

        for directory, subdirs, fnames in walk(docs_dir):
            with self.subTest(directory=basename(directory)):
                check_dir(directory)

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
viewer_typography.py
viewer_skin.py
viewer_idx28.py
viewer_curves.py
viewer_gp.py
vd_draw_experimental.py
viewer_polyline.py
blenddata_to_svdata2.py
obj_edit.py
BMOperatorsMK2.py
uv_texture.py
csg_booleanMK2.py
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
edge_split.py
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
vd_attr_node.py
scalar_field_point.py
bvh_nearest_new.py
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

            if known:
                info("Category %s: Tolerating unexistance of the documentation for the following nodes for now:\n%s", dir_name, "\n".join(known))

            if bad_files:
                self.fail("Not all nodes of category `{}' have corresponding documentation; missing are:\n{}".format(dir_name, "\n".join(bad_files)))

        for directory, subdirs, fnames in walk(nodes_dir):
            with self.subTest(directory=basename(directory)):
                check_category(directory)


