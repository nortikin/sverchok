
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
                error("The following files are not mentioned in %s:\n%s", index_name, "\n".join(bad_files))
                self.fail("Not all node documentation files are mentioned in their corresponding indexes.")

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
                    error("The following files, which are referenced from %s, do not exist:\n%s", index_name, "\n".join(bad_files))
                    self.fail("Not all node documentation referenced from index files exist.")

        docs_dir = self.get_nodes_docs_directory()

        for directory, subdirs, fnames in walk(docs_dir):
            with self.subTest(directory=basename(directory)):
                check_dir(directory)

    def test_node_docs_existance(self):
        sv_init = sverchok.__file__
        nodes_dir = join(dirname(sv_init), "nodes")
        docs_dir = self.get_nodes_docs_directory()

        known_problems = """
vd_matrix.py
viewer_typography.py
viewer_skin.py
vd_basic_lines.py
viewer_bmesh.py
viewer_idx28.py
viewer_texture.py
viewer_curves.py
vd_draw_experimental.py
viewer_texture_lite.py
viewer_polyline.py
viewer_metaball.py
lamp_out.py
stethoscope_v28.py
text_out_mk2.py
scale_mk2.py
move_mk2.py
rotation_mk2.py
input_switch_mod.py
blenddata_to_svdata2.py
obj_edit.py
BMOperatorsMK2.py
cache.py
objects_in_lite.py
particles.py
group.py
dupli_instances_mk4.py
monad.py
curve_in.py
obj_remote_mk2.py
uv_texture.py
instancer.py
3dview_props.py
create_bvh_tree.py
particles_MK2.py
node_remote.py
mask_convert.py
join_tris.py
csg_booleanMK2.py
convex_hull_mk2.py
udp_client.py
cricket.py
lattice_analyzer.py
vertex_colors_mk3.py
sort_blenddata.py
object_raycast2.py
closest_point_on_mesh2.py
sample_uv_color.py
select_mesh_verts.py
scene_raycast2.py
sculpt_mask.py
weightsmk2.py
set_blenddata2.py
points_from_uv_to_mesh.py
custom_mesh_normals.py
getsetprop.py
get_asset_properties.py
color_uv_texture.py
armature_analyzer.py
filter_blenddata.py
matrix_array.py
scalar_mk3.py
easing.py
spiral.py
edge_split.py
multi_exec.py
sn_functor_b.py
topology_simple.py
sn_functor.py
color_in_mk1.py
normal.py
formula_deform_MK2.py
color_out_mk1.py
interpolation_mk2.py
formula_color.py
slice_lite.py
numpy_array.py
bmesh_obj_in.py
bmesh_out.py
bmesh_to_element.py
bmesh_analyzer_big.py
flip_normals.py
mesh_beautify.py
grid_fill.py
limited_dissolve.py
pulga_physics.py
extrude_multi_alt.py
limited_dissolve_mk2.py
extrude_separate_lite.py
mesh_separate_mk2.py
planar_edgenet_to_polygons.py
subdivide_lite.py
unsubdivide.py
triangulate_heavy.py
symmetrize.py
vd_attr_node.py
filter_empty_lists.py
volume.py
linked_verts.py
distance_point_plane.py
raycaster_lite.py
distance_point_line.py
distance_line_line.py
kd_tree_edges_mk2.py
deformation.py
bvh_overlap_polys.py
intersect_line_sphere.py
diameter.py
mesh_select.py
intersect_plane_plane.py
mesh_filter.py
image_components.py
bvh_nearest_new.py
edge_angles.py
normals.py
kd_tree_path.py
points_inside_mesh.py
bbox_mk2.py
distance_pp.py
kd_tree_MK2.py
path_length.py
proportional.py
area.py
object_insolation.py
select_similar.py
polygons_centers_mk3.py
""".split("\n")

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
                error("Category %s: The following nodes do not have corresponding documentation files:\n%s", dir_name, "\n".join(bad_files))
                self.fail("Not all nodes have corresponding documentation.")

        for directory, subdirs, fnames in walk(nodes_dir):
            with self.subTest(directory=basename(directory)):
                check_category(directory)


