# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import random
import string
from itertools import cycle
from typing import List, Union

import numpy as np

import bpy
from mathutils import Matrix

from sverchok.data_structure import updateNode, update_with_kwargs, numpy_full_list, repeat_last
from sverchok.utils.handle_blender_data import correct_collection_length, delete_data_block
from sverchok.utils.sv_bmesh_utils import empty_bmesh, add_mesh_to_bmesh


class SvObjectData(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)

    # Object have not information about in which collection it is located
    # Keep here information about collection for performance reasons
    # Now object can be only in on collection
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)

    def ensure_object(self, data_block, name: str, object_template: bpy.types.Object = None):
        """Add object if it does not exist, if object_template is given new object will be copied from it"""
        if not self.obj:
            # it looks like it means only that the property group item was created newly
            if object_template:
                self.obj = object_template.copy()
                self.obj.data = data_block
            else:
                self.obj = bpy.data.objects.new(name=name, object_data=data_block)
        else:
            # in case if data block was changed
            self.obj.data = data_block

    def select(self):
        """Just select the object"""
        if self.obj:
            self.obj.select_set(True)

    def ensure_link_to_collection(self, collection: bpy.types.Collection = None):
        """Links object to scene or given collection, unlink from previous collection"""
        try:
            if collection:
                collection.objects.link(self.obj)
            else:
                # default collection
                bpy.context.scene.collection.objects.link(self.obj)
        except RuntimeError:
            # then the object already added, it looks like more faster way to ensure object is in the scene
            pass

        if self.collection != collection:
            # new collection was given, object should be removed from previous one
            if self.collection is None:
                # it means that it is scene default collection
                # from other hand if item only was created it also will be None but object is not in any collection yet
                try:
                    bpy.context.scene.collection.objects.unlink(self.obj)
                except RuntimeError:
                    pass
            else:
                self.collection.objects.unlink(self.obj)

            self.collection = collection

    def check_object_name(self, name: str) -> None:
        """If base name of an object was changed names of all instances also should be changed"""
        real_name = self.obj.name.rsplit('.', 1)[0]
        if real_name != name:
            self.obj.name = name

    def recreate_object(self, object_template: bpy.types.Object = None):
        """
        Object will be replaced by new object recreated from scratch or copied from given object_template if given
        Previous object will be removed, data block remains unchanged
        """
        # in case recreated object should have a chance to get the same name of previous object
        # previous object should be deleted first
        data_block = self.obj.data
        obj_name = self.obj.name
        bpy.data.objects.remove(self.obj)
        if object_template:
            new_obj = object_template.copy()
            new_obj.data = data_block
        else:
            new_obj = bpy.data.objects.new(name=obj_name, object_data=data_block)
        self.obj = new_obj

    def remove_data(self):
        """Should be called before removing item"""
        if self.obj:
            delete_data_block(self.obj)


class BlenderObjects:
    """Should be used for generating list of objects"""
    def show_objects_update(self, context, to_show: bool = None):
        """Hide / show objects. It should be only place to hide objects"""
        to_show = to_show if to_show is not None else self.show_objects
        [setattr(prop.obj, 'hide_viewport', not to_show) for prop in self.object_data]

    def selectable_objects_update(self, context):
        [setattr(prop.obj, 'hide_select', False if self.selectable_objects else True) for prop in self.object_data]

    def render_objects_update(self, context):
        [setattr(prop.obj, 'hide_render', False if self.render_objects else True) for prop in self.object_data]

    object_data: bpy.props.CollectionProperty(type=SvObjectData, options={'SKIP_SAVE'})

    show_objects: bpy.props.BoolProperty(
        default=True,
        description="Show / hide objects in viewport",
        update=update_with_kwargs(show_objects_update))

    selectable_objects: bpy.props.BoolProperty(
        default=True,
        description="Make objects selectable / unselectable",
        update=selectable_objects_update)

    render_objects: bpy.props.BoolProperty(
        default=True,
        description="Show / hide objects for render engines",
        update=render_objects_update)

    def regenerate_objects(self,
                           object_names: List[str],
                           data_blocks,
                           collections: List[bpy.types.Collection] = None,
                           object_template: List[bpy.types.Object] = None):
        """
        It will generate new or remove old objects, number of generated objects will be equal to given data_blocks
        Object_names list can contain one name. In this case Blender will add suffix to next objects (.001, .002,...)
        :param object_template: optionally, object which properties should be grabbed for instanced object
        :param collections: objects will be putted into collections if given, only one in list can be given
        :param data_blocks: nearly any data blocks - mesh, curves, lights ...
        :param object_names: usually equal to name of data block
        :param data_blocks: for now it is support only be bpy.types.Mesh
        """
        if collections is None:
            collections = [None]
        if object_template is None:
            object_template = [None]

        correct_collection_length(self.object_data, len(data_blocks))
        prop_group: SvObjectData
        input_data = zip(self.object_data, data_blocks, cycle(object_names), cycle(collections), cycle(object_template))
        for prop_group, data_block, name, collection, template in input_data:
            prop_group.ensure_object(data_block, name, template)
            prop_group.ensure_link_to_collection(collection)
            prop_group.check_object_name(name)

    def draw_object_properties(self, layout):
        """Should be used for adding hide, select, render objects properties"""
        layout.prop(self, 'show_objects', toggle=True, text='',
                    icon=f"RESTRICT_VIEW_{'OFF' if self.show_objects else 'ON'}")
        layout.prop(self, 'selectable_objects', toggle=True, text='',
                    icon=f"RESTRICT_SELECT_{'OFF' if self.selectable_objects else 'ON'}")
        layout.prop(self, 'render_objects', toggle=True, text='',
                    icon=f"RESTRICT_RENDER_{'OFF' if self.render_objects else 'ON'}")


class SvMeshData(bpy.types.PropertyGroup):
    mesh: bpy.props.PointerProperty(type=bpy.types.Mesh, options={'SKIP_SAVE'})

    def regenerate_mesh(self, mesh_name: str, verts, edges=None, faces=None, matrix: Matrix = None,
                        make_changes_test=True):
        """
        It takes vertices, edges and faces and updates mesh data block
        If it assume that topology is unchanged only position of vertices will be changed
        In this case it will be more efficient if vertices are given in np.array float32 format
        Can apply matrix to mesh optionally
        """
        if edges is None:
            edges = []
        if faces is None:
            faces = []

        if not self.mesh:
            # new mesh should be created
            self.mesh = bpy.data.meshes.new(name=mesh_name)
        if not make_changes_test or self.is_topology_changed(verts, edges, faces):
            with empty_bmesh(False) as bm:
                add_mesh_to_bmesh(bm, verts, edges, faces, update_indexes=False, update_normals=False)
                if matrix:
                    bm.transform(matrix)
                bm.to_mesh(self.mesh)
        else:
            self.update_vertices(verts)
            if matrix:
                self.mesh.transform(matrix)
        self.mesh.update()

    def set_smooth(self, is_smooth_mesh):
        """Make mesh smooth or flat"""
        if is_smooth_mesh:
            is_smooth = np.ones(len(self.mesh.polygons), dtype=bool)
        else:
            is_smooth = np.zeros(len(self.mesh.polygons), dtype=bool)
        self.mesh.polygons.foreach_set('use_smooth', is_smooth)

    def is_topology_changed(self, verts: list, edges: list, faces: list) -> bool:
        """
        Simple and fast test but not 100% robust.
        If number of vertices and faces are unchanged it assumes that topology is not changed
        This test is useful if mesh just changed its location.
        It is much faster just set new coordinate for each vector then recreate whole object
        """
        if not faces:
            # edges can be take in account if mesh does not have polygons
            # because Sverchok edges can exclude edges within polygons
            return len(self.mesh.vertices) != len(verts) or len(self.mesh.edges) != len(edges)
        else:
            number_is_changed = len(self.mesh.vertices) != len(verts) or len(self.mesh.polygons) != len(faces)
            # check several polygons indexes
            are_polygons_changed = any([list(p.vertices) != f for _, p, f in zip(range(5), self.mesh.polygons, faces)])
            return number_is_changed or are_polygons_changed

    def update_vertices(self, verts: Union[list, np.ndarray]):
        """
        Just update position of mesh vertices, order and number of given vertices should be the same as mesh
        numpy array with float32 type will be 10 times faster than any other input data
        """
        verts = np.array(verts, dtype=np.float32)  # todo will be this fast if it is already array float 32?
        self.mesh.vertices.foreach_set('co', np.ravel(verts))

    def remove_data(self):
        """
        This method should be called before deleting the property
        The mesh is belonged only to this property and should be deleted with it
        """
        if self.mesh:
            delete_data_block(self.mesh)


class SvLightData(bpy.types.PropertyGroup):
    light: bpy.props.PointerProperty(type=bpy.types.Light)

    def regenerate_light(self, light_name: str, light_type: str):
        if not self.light:
            # new mesh should be created
            self.light = bpy.data.lights.new(name=light_name, type=light_type)
        elif self.light.type != light_type:
            # in case if type was changed
            self.light.type = light_type

    def remove_data(self):
        """
        This method should be called before deleting the property
        The mesh is belonged only to this property and should be deleted with it
        """
        if self.light:
            delete_data_block(self.light)


class SvCurveData(bpy.types.PropertyGroup):
    """For now it is supporting only one spline per curve"""
    curve: bpy.props.PointerProperty(type=bpy.types.Curve)

    def regenerate_curve(self,
                         curve_name: str,
                         vertices: Union[List[list], List[np.ndarray]],
                         spline_type: str = 'POLY',
                         vertices_radius: Union[List[list], List[np.ndarray]] = None,
                         close_spline: bool = False,
                         use_smooth: bool = True,
                         tilt: Union[List[list], List[np.ndarray]] = None):
        # Be aware that curve consists multiple splines
        if not self.curve:
            self.curve = bpy.data.curves.new(name=curve_name, type='CURVE')  # type ['CURVE', 'SURFACE', 'FONT']
        if len(self.curve.splines) != len(vertices) \
                or any(len(s.points) != len(v) for s, v in zip(self.curve.splines, vertices)):
            # if at least on spline has wrong number of points whole list of splines should be recreated
            # thanks to Blender API
            self.curve.splines.clear()
            [self.curve.splines.new(spline_type) for _ in range(len(vertices))]
            [s.points.add(len(v) - 1) for s, v in zip(self.curve.splines, vertices)]

        for s, v, r, t in zip(self.curve.splines, vertices,
                              repeat_last(vertices_radius or [None]), repeat_last(tilt or [None])):
            v = np.asarray(v, dtype=np.float32)
            if r is None:
                r = np.ones(len(v), dtype=np.float32)
            r = np.asarray(r, dtype=np.float32)
            self._regenerate_spline(s, v, spline_type, r, t, close_spline, use_smooth)

    def remove_data(self):
        """
        This method should be called before deleting the property
        The mesh is belonged only to this property and should be deleted with it
        """
        if self.curve:
            delete_data_block(self.curve)

    @staticmethod
    def _regenerate_spline(spline: bpy.types.Spline,
                           vertices: np.ndarray,
                           spline_type: str = 'POLY',
                           vertices_radius: np.ndarray = None,
                           tilt: np.ndarray = None,
                           close_spline: bool = False,
                           use_smooth: bool = True):
        spline.type = spline_type
        spline.use_cyclic_u = close_spline
        spline.use_smooth = use_smooth

        # flatten vertices array and add W component (X, Y, Z, W), W is responsible for drawing NURBS curves
        w_vertices = np.concatenate((vertices, np.ones((len(vertices), 1), dtype=np.float32)), axis=1)
        flatten_vertices = np.ravel(w_vertices)
        spline.points.foreach_set('co', flatten_vertices)
        if vertices_radius is not None:
            spline.points.foreach_set('radius', numpy_full_list(vertices_radius, len(vertices)))
        if tilt is not None:
            spline.points.foreach_set('tilt', numpy_full_list(tilt, len(vertices)))


class SvViewerNode(BlenderObjects):
    """
    Mixin for all nodes which displays any objects in viewport
    """

    is_active: bpy.props.BoolProperty(name='Live', default=True, update=updateNode,
                                      description="When enabled this will process incoming data",)

    base_data_name: bpy.props.StringProperty(
        default='Alpha',
        description='stores the mesh name found in the object, this mesh is instanced',
        update=updateNode)

    collection: bpy.props.PointerProperty(type=bpy.types.Collection, update=updateNode,
                                          description="Collection where to put objects")

    def draw_viewer_properties(self, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.column().prop(self, 'is_active', toggle=True)

        self.draw_object_properties(row)  # hide, selectable, render

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "base_data_name", text="", icon='OUTLINER_OB_MESH')
        row.operator('node.sv_generate_random_object_name', text='', icon='FILE_REFRESH')

        row = col.row(align=True)
        row.scale_y = 2
        row.operator('node.sv_select_objects', text="Select")

        col.prop_search(self, 'collection', bpy.data, 'collections', text='', icon='GROUP')

    def init_viewer(self):
        """Should be called from descendant class"""
        self.base_data_name = bpy.context.scene.sv_object_names.get_available_name()
        self.use_custom_color = True

        self.outputs.new('SvObjectSocket', "Objects")

    def sv_copy(self, other):
        """
        Regenerate object names, and clean data
        Use super().sv_copy(other) to override this method
        """
        with self.sv_throttle_tree_update():
            self.base_data_name = bpy.context.scene.sv_object_names.get_available_name()
            # object and mesh lists should be clear other wise two nodes would have links to the same objects
            self.object_data.clear()

    def show_viewport(self, is_show: bool):
        """It should be called by node tree to show/hide objects"""
        if not self.show_objects:
            # just ignore request
            pass
        else:
            self.show_objects_update(None, is_show)

    def load_from_json(self, node_data: dict, import_version: float):
        """
        Manually serialization node properties
        Should be overridden in zis way: super().storage_get_data(storage); self.my_prop = storage['my_prop']
        """
        if import_version <= 0.08:
            collection_name = node_data['collection']
            if collection_name:
                collection = (bpy.data.collections.get(collection_name))
                if not collection:
                    collection = bpy.data.collections.new(collection_name)
                    bpy.context.collection.children.link(collection)
                self.collection = collection

    def draw_label(self):
        if self.hide:
            return f"{self.bl_label[:2]}V {self.base_data_name}"
        else:
            return self.bl_label


class SvObjectNames(bpy.types.PropertyGroup):
    available_name_number: bpy.props.IntProperty(default=0, min=0, max=24)
    greek_alphabet = [
        'Alpha', 'Beta', 'Gamma', 'Delta',
        'Epsilon', 'Zeta', 'Eta', 'Theta',
        'Iota', 'Kappa', 'Lamda', 'Mu',
        'Nu', 'Xi', 'Omicron', 'Pi',
        'Rho', 'Sigma', 'Tau', 'Upsilon',
        'Phi', 'Chi', 'Psi', 'Omega']

    def get_available_name(self):
        """It returns name from greek alphabet, if all names was used it returns random letters"""
        if self.available_name_number <= 23:
            name = self.greek_alphabet[self.available_name_number]
            self.available_name_number += 1
        else:
            name = self.get_random_name()

        return name

    @staticmethod
    def get_random_name():
        """Generate random name from random letters"""
        return ''.join(random.sample(set(string.ascii_uppercase), 6))


class SvSelectObjects(bpy.types.Operator):
    """It calls `select` method of every item in `object_data` collection of node"""
    bl_idname = 'node.sv_select_objects'
    bl_label = "Select objects"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def description(cls, context, properties):
        return "Select generated objects"

    def execute(self, context):
        prop: SvObjectData
        for prop in context.node.object_data:
            prop.select()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return hasattr(context.node, 'object_data')


class SvGenerateRandomObjectName(bpy.types.Operator):
    """
    It calls get_random_name fo sv_object_names property in scene
    and assign it to base_data_name property of node
    """
    bl_idname = 'node.sv_generate_random_object_name'
    bl_label = "Random name"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def description(cls, context, properties):
        return "Generate random name"

    def execute(self, context):
        context.node.base_data_name = bpy.context.scene.sv_object_names.get_random_name()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return hasattr(context.node, 'base_data_name')


class SvCreateMaterial(bpy.types.Operator):
    """It creates and add new material to a node"""
    bl_idname = 'node.sv_create_material'
    bl_label = "Create material"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def description(cls, context, properties):
        return "Crate new material"

    def execute(self, context):
        mat = bpy.data.materials.new('sv_material')
        mat.use_nodes = True
        context.node.material = mat
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return hasattr(context.node, 'material')


module_classes = [SvObjectData, SvMeshData, SvSelectObjects, SvObjectNames, SvGenerateRandomObjectName, SvLightData,
                  SvCurveData, SvCreateMaterial]


def register():
    [bpy.utils.register_class(cls) for cls in module_classes]
    bpy.types.Scene.sv_object_names = bpy.props.PointerProperty(type=SvObjectNames)


def unregister():
    [bpy.utils.unregister_class(cls) for cls in module_classes[::-1]]
