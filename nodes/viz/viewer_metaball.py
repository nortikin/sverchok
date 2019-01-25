# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from mathutils import Matrix
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import Matrix_generate, match_long_repeat, updateNode, get_data_nesting_level, ensure_nesting_level, describe_data_shape
from sverchok.utils.sv_obj_helper import SvObjHelper


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
    Triggers: meta ball
    Tooltip: Create Blender's metaball object
    
    A short description for reader of node code
    """

    bl_idname = 'SvMetaballOutNode'
    bl_label = 'Metaball'
    bl_icon = 'META_BALL'

    data_kind: StringProperty(default='META')

    meta_types = [
        ("BALL", "Ball", "Ball", "META_BALL", 1),
        ("CAPSULE", "Capsule", "Capsule", "META_CAPSULE", 2),
        ("PLANE", "Plane", "Plane", "META_PLANE", 3),
        ("ELLIPSOID", "Ellipsoid", "Ellipsoid", "META_ELLIPSOID", 4),
        ("CUBE", "Cube", "Cube", "META_CUBE", 5)]

    meta_type_by_id = dict((item[4], item[0]) for item in meta_types)

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
        self.inputs.new('StringsSocket', 'Types').prop_name = "meta_type"
        self.inputs.new('MatrixSocket', 'Origins')
        self.inputs.new('StringsSocket', "Radius").prop_name = "radius"
        self.inputs.new('StringsSocket', "Stiffness").prop_name = "stiffness"
        self.inputs.new('StringsSocket', 'Negation')
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

        def setup_element(element, item):
            (origin, radius, stiffness, negate, meta_type) = item
            center, rotation, scale = origin.decompose()
            element.co = center[:3]
            if isinstance(meta_type, int):
                if meta_type not in self.meta_type_by_id:
                    raise Exception("`Types' input expects an integer number from 1 to 5")
                meta_type = self.meta_type_by_id[meta_type]
            element.type = meta_type
            element.radius = radius
            element.stiffness = stiffness
            element.rotation = rotation
            element.size_x = scale[0]
            element.size_y = scale[1]
            element.size_z = scale[2]
            element.use_negative = bool(negate)

        origins = self.inputs['Origins'].sv_get()
        radiuses = self.inputs['Radius'].sv_get()
        stiffnesses = self.inputs['Stiffness'].sv_get()
        negation = self.inputs['Negation'].sv_get(default=[[0]])
        types = self.inputs['Types'].sv_get()

        level = get_data_nesting_level_mod(origins)
        if level == 1:
            # We have list of lists of matrices.
            # Create a meta object per each list of matrices.
            self.debug("Will create META object for each list of input matrices")
            radiuses = radiuses[0]
            stiffnesses = stiffnesses[0]
            negation = negation[0]
            types = types[0]
        elif level == 2:
            # We have list of matrices.
            # Create single meta object.
            #origins = [Matrix_generate(origin) for origin in origins]
            self.debug("Will create single META object")
            self.debug(describe_data_shape(origins))
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
            items = list(zip(*items))

            # D.elements.foreach_set
            # D.elements.foreach_set('co', full_list_of_locations)

            if len(items) == len(metaball_object.data.elements):
                #self.debug('Updating existing metaball data')

                for (item, element) in zip(items, metaball_object.data.elements):
                    setup_element(element, item)
            else:
                self.debug('Recreating metaball #%s data', object_index)
                metaball_object.data.elements.clear()

                for item in items:
                    element = metaball_object.data.elements.new()
                    setup_element(element, item)
        
        self.remove_non_updated_objects(object_index)
        self.set_corresponding_materials()
        objects = self.get_children()

        if 'Objects' in self.outputs:
            self.outputs['Objects'].sv_set(objects)


classes = [SvMetaballOutNode]
register, unregister = bpy.utils.register_classes_factory(classes)
