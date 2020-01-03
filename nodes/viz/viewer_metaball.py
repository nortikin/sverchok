# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from mathutils import Matrix
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import Matrix_generate, match_long_repeat, updateNode, get_data_nesting_level, ensure_nesting_level, describe_data_shape
from sverchok.utils.sv_obj_helper import SvObjHelper


def decompose_matrices(matrices):
    # center, rotation, scale = origin.decompose()
    # center[:3], rotation, scale[0], scale[1], scale[2]
    # this returns [all centers, all_rotations, all_scale_x, all_scale_y, sall_scale_z]
    return list(zip(*[(m[0][:3], m[1], m[2][0], m[2][1], m[2][2]) for m in [matrix.decompose() for matrix in matrices]]))

def flatten_list(data):
    return np.array(data).flatten()


def get_data_nesting_level_mod(data):
    try:
        if isinstance(data[0], Matrix):
            return 1
        elif isinstance(data[0][0], Matrix):
            return 2
        return 0
    except:
        return 0


class SvMetaballOutNode(bpy.types.Node, SverchCustomTreeNode, SvObjHelper):
    """
    Triggers: Output Metaball obj.
    Tooltip: Create Blender's metaball  dynamic object.
    
    A short description for reader of node code
    """

    bl_idname = 'SvMetaballOutNode'
    bl_label = 'Metaball'
    bl_icon = 'META_BALL'
    sv_icon = 'SV_METABALL'

    data_kind: StringProperty(default='META')

    meta_types = [
        ("BALL", "Ball", "Ball", "META_BALL", 1),
        ("CAPSULE", "Capsule", "Capsule", "META_CAPSULE", 2),
        ("PLANE", "Plane", "Plane", "META_PLANE", 3),
        ("ELLIPSOID", "Ellipsoid", "Ellipsoid", "META_ELLIPSOID", 4),
        ("CUBE", "Cube", "Cube", "META_CUBE", 5)]

    meta_type_by_id = dict((item[4], item[0]) for item in meta_types)
    meta_deconvert = {item[0]: item[4] for item in meta_types}

    meta_type: EnumProperty(
        name='Meta type', description="Meta object type",
        items=meta_types, update=updateNode)

    radius: FloatProperty(
        name='Radius', description='Metaball radius',
        default=1.0, min=0.0, update=updateNode)

    stiffness: FloatProperty(
        name='Stiffness', description='Metaball stiffness',
        default=2.0, min=0.0, update=updateNode)

    view_resolution: FloatProperty(
        name='Resolution (viewport)', description='Resolution for viewport',
        default=0.2, min=0.0, max=1.0, update=updateNode)

    render_resolution: FloatProperty(
        name='Resolution (render)', description='Resolution for rendering',
        default=0.1, min=0.0, max=1.0, update=updateNode)

    threshold: FloatProperty(
        name='Threshold', description='Influence of meta elements',
        default=0.6, min=0.0, max=5.0, update=updateNode)

    def get_metaball_name(self, idx):
        # Metaball names magic:
        # If you name metaball object like "Alpha.001",
        # it will be considered as being in the same "meta group"
        # as other metaball objects named "Alpha", "Alpha.002" 
        # and so on. But! if there is no object named "Alpha"
        # (without index) in the scene, then objects named 
        # "Alpha.001" (with index) will not be displayed correctly.
        # So, we have to name first object without index,
        # and all other with index.
        if idx == 1:
            return self.basedata_name
        else:
            #return f'{self.basedata_name}.{(idx-1):04d}'
            return self.basedata_name + '.' + str("%04d" % (idx-1))

    def create_metaball(self, index):
        object_name = self.get_metaball_name(index)
        metaball_data = bpy.data.metaballs.new(object_name)
        metaball_object = self.create_object(object_name, index, metaball_data)

        return metaball_object

    def find_metaball(self, index):
        name = self.get_metaball_name(index)
        return bpy.data.objects.get(name)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Types').prop_name = "meta_type"
        self.inputs.new('SvMatrixSocket', 'Origins')
        self.inputs.new('SvStringsSocket', "Radius").prop_name = "radius"
        self.inputs.new('SvStringsSocket', "Stiffness").prop_name = "stiffness"
        self.inputs.new('SvStringsSocket', 'Negation')
        self.outputs.new('SvObjectSocket', "Objects")

    def draw_buttons(self, context, layout):
        self.draw_live_and_outliner(context, layout)
        self.draw_object_buttons(context, layout)
        layout.prop(self, "threshold")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        self.draw_ext_object_buttons(context, layout)
        layout.prop(self, "view_resolution")
        layout.prop(self, "render_resolution")

    def process(self):
        if not self.activate:
            return

        if not self.inputs['Origins'].is_linked:
            return

        origins = self.inputs['Origins'].sv_get()
        radiuses = self.inputs['Radius'].sv_get()
        stiffnesses = self.inputs['Stiffness'].sv_get()
        negation = self.inputs['Negation'].sv_get(default=[[0]])
        types = self.inputs['Types'].sv_get()

        level = get_data_nesting_level_mod(origins)
        if level == 2:
            # We have list of lists of matrices.
            # Create a meta object per each list of matrices.
            self.debug("Will create META object for each list of input matrices")
            radiuses = radiuses[0]
            stiffnesses = stiffnesses[0]
            negation = negation[0]
            types = types[0]
        elif level == 1:
            # We have list of matrices.
            # Create single meta object.
            #origins = [Matrix_generate(origin) for origin in origins]
            self.debug("Will create single META object")
            # self.debug(describe_data_shape(origins))
            origins = [origins]
        else:
            raise Exception("`Origins' input of Metaball node requires data nesting level 3 or 4, not {}".format(level))

        inputs = match_long_repeat([origins, radiuses, stiffnesses, negation, types])
        object_index = 0
        for m_origins, m_radiuses, m_stiffnesses, m_negation, m_types in zip(*inputs):
            object_index += 1

            metaball_object = self.find_metaball(object_index)
            if not metaball_object:
                metaball_object = self.create_metaball(object_index)
                self.debug("Created new metaball #%s", object_index)

            metaball_object.data.resolution = self.view_resolution
            metaball_object.data.render_resolution = self.render_resolution
            metaball_object.data.threshold = self.threshold

            if isinstance(m_origins, Matrix):
                m_origins = [m_origins]
            m_radiuses    = ensure_nesting_level(m_radiuses, 1)
            m_stiffnesses = ensure_nesting_level(m_stiffnesses, 1)
            m_negation    = ensure_nesting_level(m_negation, 1)
            m_types       = ensure_nesting_level(m_types, 1)

            items = match_long_repeat([m_origins, m_radiuses, m_stiffnesses, m_negation, m_types])
           
            elements = metaball_object.data.elements 
            diff = len(elements) - len(items[0])

            # print('elements:', len(elements), 'vs', diff, ' -->len items[0]', len(items[0]))

            if not diff == 0:

                # less items than current elements, clearing is faster
                new_num_to_create = abs(diff) if diff < 0 else len(items[0])
                if diff > 0:
                    elements.clear()

                _ = [elements.new() for i in range(new_num_to_create)]

            # set up all flat lists.
            full_origins, full_radii, full_stiff, full_negation, full_types = items
            full_negation_bools = [bool(n) for n in full_negation]
            full_centers, full_rotations, full_size_x, full_size_y, full_size_z = decompose_matrices(full_origins)

            # pass all flat lists
            # elements.foreach_set('type', full_types_int)
            _ = [setattr(element, 'type', _type) for element, _type in zip(elements, full_types)]
            elements.foreach_set('radius', full_radii)
            elements.foreach_set('stiffness', full_stiff)
            elements.foreach_set('use_negative', full_negation_bools)
            elements.foreach_set('co', flatten_list(full_centers))
            elements.foreach_set('rotation', flatten_list(full_rotations))
            elements.foreach_set('size_x', full_size_x)
            elements.foreach_set('size_y', full_size_y)
            elements.foreach_set('size_z', full_size_z)

        
        self.remove_non_updated_objects(object_index)
        self.set_corresponding_materials()
        objects = self.get_children()

        if 'Objects' in self.outputs:
            self.outputs['Objects'].sv_set(objects)


classes = [SvMetaballOutNode]
register, unregister = bpy.utils.register_classes_factory(classes)
