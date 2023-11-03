from sverchok.utils.testing import *


class DocumentationTests(SverchokTestCase):

    def setUp(self):
        self.node_file_names = set()
        self.doc_file_names = set()

        sv_root = Path(sverchok.__file__).parent
        nodes_folder = sv_root / 'nodes'
        for path in nodes_folder.rglob('*.py'):
            file_name = path.stem
            if file_name == '__init__':
                continue
            self.node_file_names.add(file_name)

        doc_folder = sv_root / 'docs' / 'nodes'
        for path in doc_folder.rglob('*.rst'):
            file_name = path.stem
            index_file = f'{path.parent.stem}_index'
            if file_name == index_file:
                continue
            self.doc_file_names.add(file_name)

    def get_nodes_docs_directory(self):
        sv_init = sverchok.__file__
        return join(dirname(sv_init), "docs", "nodes")

    def test_uniq_node_modules(self):
        sv_root = Path(sverchok.__file__).parent
        nodes_folder = sv_root / 'nodes'
        modules = dict()
        for path in nodes_folder.rglob('*.py'):
            file_name = path.stem
            if file_name == '__init__':
                continue
            with self.subTest(node_module=f"{file_name}.py"):
                if file_name in modules:
                    self.fail(f'There are two modules with the same name "{file_name}" \n'
                              f'File 1: {Path(modules[file_name]).relative_to(sv_root)} \n'
                              f'file 2: {Path(path).relative_to(sv_root)}')
                else:
                    modules[file_name] = path

    def test_unused_docs(self):
        for doc_name in self.doc_file_names:
            with self.subTest(documentation_file=f"{doc_name}.rst"):
                if doc_name not in self.node_file_names:
                    self.fail("The documentation file does not have respective python module")

    def test_node_docs_existance(self):
        known_problems = """
uv_texture.py
vertex_colors_mk3.py
sort_blenddata.py
object_raycast2.py
closest_point_on_mesh2.py
scene_raycast2.py
sculpt_mask.py
set_blenddata2.py
custom_mesh_normals.py
color_uv_texture.py
filter_blenddata.py
interpolation_mk2.py
numpy_array.py
mesh_beautify.py
pulga_physics.py
limited_dissolve.py
limited_dissolve_mk2.py
mesh_separate_mk2.py
approx_subd_to_nurbs.py
vd_attr_node_mk2.py
quads_to_nurbs.py
location.py
sun_position.py
flip_surface.py
""".split("\n")

        for module_name in self.node_file_names:
            with self.subTest(node_module=f"{module_name}.py"):
                if module_name not in self.doc_file_names:
                    if f'{module_name}.py' not in known_problems:
                        self.fail(f"Node module={module_name}.py does not have"
                                  f" documentation")
                else:
                    if f'{module_name}.py' in known_problems:
                        self.fail(f"Exclude the node module={module_name}.py"
                                  f" from the Known Problems list")
