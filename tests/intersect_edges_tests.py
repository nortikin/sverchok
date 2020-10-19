from sverchok.core.update_system import process_tree
from sverchok.utils.testing import *


class IntersectEdgesTest2(ReferenceTreeTestCase):
    # There are 2 3x3 planes intersecting
    reference_file_name = "intersecting_planes.blend.gz"

    def test_intersect_edges(self):
        process_tree(self.tree)

        node = self.tree.nodes["Intersect Edges MK2"]

        result_verts = get_output_socket_data(node, "Verts_out")
        result_edges = get_output_socket_data(node, "Edges_out")
        info("Result: %s", result_verts)

        #self.store_reference_sverchok_data("intersecting_planes_result_verts.txt", result_verts)
        self.assert_sverchok_data_equals_file(result_verts, "intersecting_planes_result_verts.txt", precision=8)
        #self.store_reference_sverchok_data("intersecting_planes_result_faces.txt", result_edges)
        self.assert_sverchok_data_equals_file(result_edges, "intersecting_planes_result_faces.txt", precision=8)
