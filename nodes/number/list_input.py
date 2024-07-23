# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import EnumProperty, FloatVectorProperty, IntProperty, FloatProperty, IntVectorProperty, BoolProperty, CollectionProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, multi_socket
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
from sverchok.utils.sv_logging import sv_logger
from sverchok.utils.handle_blender_data import correct_collection_length
from mathutils import Vector

class SvListInputBoolEntry(bpy.types.PropertyGroup):
    def update_entry(self, context):
        if hasattr(context, 'node'):
            updateNode(context.node, context)
        else:
            sv_logger.debug("Node is not defined in this context, so will not update the node.")

    item_enable : BoolProperty(
        name = "Enable",
        description = "Enable Element in list",
        default=True,
        update=update_entry,
        ) # type: ignore
    
    elem: BoolProperty(
        name = "Boolean",
        default = True,
        update=update_entry,
    ) # type: ignore

class SvListInputIntEntry(bpy.types.PropertyGroup):
    def update_entry(self, context):
        if hasattr(context, 'node'):
            updateNode(context.node, context)
        else:
            sv_logger.debug("Node is not defined in this context, so will not update the node.")

    item_enable : BoolProperty(
        name = "Enable",
        description = "Enable Element in list",
        default=True,
        update=update_entry,
        ) # type: ignore
    
    elem: IntProperty(
        name = "Integer number",
        default = 0,
        update=update_entry,
    ) # type: ignore

class SvListInputFloatEntry(bpy.types.PropertyGroup):

    # share data with elements
    def get_elem(self):
        return self.elem

    def set_elem(self, value):
        self.elem = value
        
    def update_entry(self, context):
        if hasattr(context, 'node'):
            updateNode(context.node, context)
        else:
            sv_logger.debug("Node is not defined in this context, so will not update the node.")

    item_enable : BoolProperty(
        name = "Enable",
        description = "Enable Element in list",
        default=True,
        update=update_entry,
        ) # type: ignore
    
    elem: FloatProperty(
        name = "Float number",
        default = 0,
        #subtype='ANGLE',
        update=update_entry,
    ) # type: ignore
    
    NONE: FloatProperty(
        name = "Float number",
        default = 0,
        subtype='NONE',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore
    
    PERCENTAGE: FloatProperty(
        name = "Float number",
        default = 0,
        subtype='PERCENTAGE',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore
    
    FACTOR: FloatProperty(
        name = "Float number",
        default = 0,
        subtype='FACTOR',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    ANGLE: FloatProperty(
        name = "Float number",
        default = 0,
        subtype='ANGLE',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore
    
    TIME: FloatProperty(
        name = "Float number",
        default = 0,
        subtype='TIME',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore
    
    TIME_ABSOLUTE: FloatProperty(
        name = "Float number",
        default = 0,
        subtype='TIME_ABSOLUTE',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore
    
    DISTANCE: FloatProperty(
        name = "Float number",
        default = 0,
        subtype='DISTANCE',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore
    
    DISTANCE_CAMERA: FloatProperty(
        name = "Float number",
        default = 0,
        subtype='DISTANCE_CAMERA',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore
    
    TEMPERATURE: FloatProperty(
        name = "Float number",
        default = 0,
        subtype='TEMPERATURE',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore
    
    # WAVELENGTH: FloatProperty(
    #     name = "Float number",
    #     default = 0,
    #     subtype='WAVELENGTH',
    #     get = get_elem, set = set_elem,
    #     update=update_entry,
    # ) # type: ignore
    
    POWER: FloatProperty(
        name = "Float number",
        default = 0,
        subtype='POWER',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

class SvListInputVectorEntry(bpy.types.PropertyGroup):

    # share data with elements
    def get_elem(self):
        return self.elem

    def set_elem(self, value):
        self.elem = value

    def update_entry(self, context):
        if hasattr(context, 'node'):
            updateNode(context.node, context)
        else:
            sv_logger.debug("Node is not defined in this context, so will not update the node.")

    item_enable : BoolProperty(
        name = "Enable",
        description = "Enable Element in list",
        default=True,
        update=update_entry,
        ) # type: ignore
    
    elem: FloatVectorProperty(
        name = "Vector",
        default = (0., 0., 0.,),
        #subtype='COLOR', 
        #subtype='XYZ',
        update=update_entry,
    ) # type: ignore

    NONE: FloatVectorProperty(
        name = "Float number",
        default = (0., 0., 0.,),
        subtype='NONE',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    COLOR: FloatVectorProperty(
        name = "Color",
        default = (1., 1., 1.,),
        min = 0.0,
        max = 1.0,
        subtype='COLOR',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    TRANSLATION: FloatVectorProperty(
        name = "Translation",
        default = (0., 0., 0.,),
        subtype='TRANSLATION',
        get = get_elem, set = set_elem
    ) # type: ignore

    DIRECTION: FloatVectorProperty(
        name = "Float number",
        default = (1., 1., 1.,),
        subtype='DIRECTION',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    VELOCITY: FloatVectorProperty(
        name = "Float number",
        default = (0., 0., 0.,),
        subtype='VELOCITY',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    ACCELERATION: FloatVectorProperty(
        name = "Float number",
        default = (0., 0., 0.,),
        subtype='ACCELERATION',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    # MATRIX: FloatVectorProperty(
    #     name = "Float number",
    #     default = 0,
    #     subtype='MATRIX',
    #     get = get_elem, set = set_elem
    # ) # type: ignore

    EULER: FloatVectorProperty(
        name = "Float number",
        default = (0., 0., 0.,),
        subtype='EULER',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    QUATERNION: FloatVectorProperty(
        name = "Float number",
        default = (0., 0., 0.,),
        subtype='QUATERNION',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    AXISANGLE: FloatVectorProperty(
        name = "Float number",
        default = (0., 0., 0.,),
        subtype='AXISANGLE',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    XYZ: FloatVectorProperty(
        name = "Float number",
        default = (0., 0., 0.,),
        subtype='XYZ',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    XYZ_LENGTH: FloatVectorProperty(
        name = "Float number",
        default = (0., 0., 0.,),
        subtype='XYZ_LENGTH',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    COLOR_GAMMA: FloatVectorProperty(
        name = "Float number",
        default = (0., 0., 0.,),
        subtype='COLOR_GAMMA',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    COORDINATES: FloatVectorProperty(
        name = "Float number",
        default = (0., 0., 0.,),
        subtype='COORDINATES',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    LAYER: FloatVectorProperty(
        name = "Float number",
        default = (0., 0., 0.,),
        subtype='LAYER',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    LAYER_MEMBER: FloatVectorProperty(
        name = "Float number",
        default = (0., 0., 0.,),
        subtype='LAYER_MEMBER',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

class SvListInputColorEntry(bpy.types.PropertyGroup):

    # share data with elements
    def get_elem(self):
        return self.elem

    def set_elem(self, value):
        self.elem = value

    def update_entry(self, context):
        if hasattr(context, 'node'):
            updateNode(context.node, context)
        else:
            sv_logger.debug("Node is not defined in this context, so will not update the node.")

    item_enable : BoolProperty(
        name = "Enable",
        description = "Enable Element in list",
        default=True,
        update=update_entry,
        ) # type: ignore
    
    elem: FloatVectorProperty(
        name = "Vector",
        default = (1., 1., 1., 1.),
        size=4, min=0., max=1.,
        update=update_entry,
    ) # type: ignore

    NONE: FloatVectorProperty(
        name = "Color as vector",
        default = (1., 1., 1., 1.),
        subtype='NONE',
        size=4, min=0., max=1.,
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    COLOR: FloatVectorProperty(
        name = "Color",
        default = (1., 1., 1., 1.),
        size=4, min=0., max=1.,
        subtype='COLOR',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

    COLOR_GAMMA: FloatVectorProperty(
        name = "Color",
        default = (1., 1., 1., 1.),
        size=4, min=0., max=1.,
        subtype='COLOR_GAMMA',
        get = get_elem, set = set_elem,
        update=update_entry,
    ) # type: ignore

def Correct_ListInput_Length(self, context):
    if(self.mode=='BOOL_LIST_MODE'):
        correct_collection_length(self.bool_list_items, self.bool_list_counter)
    elif(self.mode=='INT_LIST_MODE'):
        correct_collection_length(self.int_list_items, self.int_list_counter)
    elif(self.mode=='FLOAT_LIST_MODE'):
        correct_collection_length(self.float_list_items, self.float_list_counter)
    elif(self.mode=='VECTOR_LIST_MODE'):
        correct_collection_length(self.vector_list_items, self.vector_list_counter)
    elif(self.mode=='COLOR_LIST_MODE'):
        correct_collection_length(self.color_list_items, self.color_list_counter)
    else:
        raise Exception(f"[func: Correct_ListInput_Length] unknown mode {self.mode}.")
    updateNode(self, context)
    pass

def invert_ListInput_Mask(self, context):
    if(self.mode=='BOOL_LIST_MODE'):
        items = self.bool_list_items
    elif(self.mode=='INT_LIST_MODE'):
        items = self.int_list_items
    elif(self.mode=='FLOAT_LIST_MODE'):
        items = self.float_list_items
    elif(self.mode=='VECTOR_LIST_MODE'):
        items = self.vector_list_items
    elif(self.mode=='COLOR_LIST_MODE'):
        items = self.color_list_items
    else:
        raise Exception(f"[func: invert_ListInput_Mask] unknown mode {self.mode}.")
    for item in items:
        item.item_enable = not(item.item_enable)
    updateNode(self, context)
    pass

# def copy_to_clipboard(self, context):
#     #context.window_manager.clipboard = '1234'
#     if self.mode == 'BOOL_LIST_MODE':
#         lst = [elem.elem for elem in self.bool_list_items if elem.item_enable==True]
#     elif self.mode == 'INT_LIST_MODE':
#         lst = [elem.elem for elem in self.int_list_items if elem.item_enable==True]
#     elif self.mode == 'FLOAT_LIST_MODE':
#         lst = [elem.elem for elem in self.float_list_items if elem.item_enable==True]
#     elif self.mode == 'VECTOR_LIST_MODE':
#         lst = []
#         [lst.extend(tuple(Vector(elem.elem))) for elem in self.color_list_items if elem.item_enable==True]
#         #lst = [str(tuple(Vector(elem.elem))) for elem in self.vector_list_items if elem.item_enable==True]
#     elif self.mode == 'COLOR_LIST_MODE':
#         lst = []
#         [lst.extend(tuple(elem.elem)) for elem in self.color_list_items if elem.item_enable==True]
#     else:
#         raise Exception(f"[func: process] unknown mode {self.mode}.")
#     #text = ','.join([str(elem) for elem in lst])
#     text = ', '.join([str(e) for e in lst])
#     context.window_manager.clipboard = text
#     pass

class SvListInputNodeMK2(Show3DProperties, SverchCustomTreeNode, bpy.types.Node):
    ''' Create a flat list of Integers, Floats, or Vectors.
    int: [[1,5,42]],
    float: [[1.0, -5.42, 12.0]]
    vectors: [[ (0,0,0), (1,2,-2)]]
    '''
    bl_idname = 'SvListInputNodeMK2'
    bl_label = 'List Input'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_INPUT'

    bool_list_counter: IntProperty(
        name='bool_list_counter',
        description='boolean',
        default=True,
        update=Correct_ListInput_Length)  # type: ignore
    bool_list_items : CollectionProperty(type=SvListInputBoolEntry) # type: ignore

    int_list_counter: IntProperty(
        name='int_list_counter',
        description='integer number',
        default=1,
        min=1,
        update=Correct_ListInput_Length)  # type: ignore
    int_list_items : CollectionProperty(type=SvListInputIntEntry) # type: ignore

    float_list_counter: IntProperty(
        name='float_list_counter',
        description='integer number',
        default=1,
        min=1,
        update=Correct_ListInput_Length)  # type: ignore
    float_list_items : CollectionProperty(type=SvListInputFloatEntry) # type: ignore

    vector_list_counter: IntProperty(
        name='vector_list_counter',
        description='vectors',
        default=1,
        min=1,
        update=Correct_ListInput_Length)  # type: ignore
    vector_list_items : CollectionProperty(type=SvListInputVectorEntry) # type: ignore

    color_list_counter: IntProperty(
        name='color_list_counter',
        description='Colors',
        default=1,
        min=1,
        update=Correct_ListInput_Length)  # type: ignore
    color_list_items : CollectionProperty(type=SvListInputColorEntry) # type: ignore

    invert_mask: BoolProperty(
        name = "Mask",
        description = "Invert list of mask",
        default=True,
        update=invert_ListInput_Mask,
    ) # type: ignore

    # copy_clipboard: BoolProperty(
    #     name = "Mask",
    #     description = "Invert list of mask",
    #     default=True,
    #     update=copy_to_clipboard,
    # ) # type: ignore

    def changeMode(self, context):
        if self.mode == 'BOOL_LIST_MODE':
            self.set_output_socketype(['SvStringsSocket'])
            self.outputs['data_output'].label = 'Boolean'
        elif self.mode == 'INT_LIST_MODE':
            self.set_output_socketype(['SvStringsSocket'])
            self.outputs['data_output'].label = 'Integers'
        elif self.mode == 'FLOAT_LIST_MODE':
            self.set_output_socketype(['SvStringsSocket'])
            self.outputs['data_output'].label = 'Floats'
        elif self.mode == 'VECTOR_LIST_MODE':
            self.set_output_socketype(['SvVerticesSocket'])
            self.outputs['data_output'].label = 'Vectors'
        elif self.mode == 'COLOR_LIST_MODE':
            self.set_output_socketype(['SvVerticesSocket'])
            self.outputs['data_output'].label = 'Colors'
        else:
            raise Exception(f"[func: changeMode] unknown mode {self.mode}.")
        Correct_ListInput_Length(self, context)
        pass

    modes = [
        ("BOOL_LIST_MODE", "Bool", "Boolean", "", 0),
        ("INT_LIST_MODE", "Int", "Integer", "", 1),
        ("FLOAT_LIST_MODE", "Float", "Float", "", 2),
        ("VECTOR_LIST_MODE", "Vector", "Vector", "", 3),
        ("COLOR_LIST_MODE", "Color", "Color", "", 4)
    ]

    mode: EnumProperty(
        items=modes,
        default='INT_LIST_MODE',
        update=changeMode
    ) # type: ignore

    subtypes_vector = [
        # # https://docs.blender.org/api/current/bpy_types_enum_items/property_subtype_number_array_items.html#rna-enum-property-subtype-number-array-items
        ("NONE", "None", "None", "", 0),
        #("COLOR", "Color", "Color", "", 1),
        ("TRANSLATION", "Translation", "Translation", "", 2),
        ("DIRECTION", "Direction", "Direction", "", 3),
        ("VELOCITY", "Velocity", "Velocity", "", 4),
        ("ACCELERATION", "Acceleration", "Acceleration", "", 5),
        #("MATRIX", "Matrix", "Matrix", "", 6),
        ("EULER", "Euler Angles", "Euler Angles", "", 7),
        ("QUATERNION", "Quaternion", "Quaternion", "", 8),
        ("AXISANGLE", "Axis-Angle", "Axis-Angle", "", 9),
        ("XYZ", "XYZ", "XYZ", "", 10),
        ("XYZ_LENGTH", "XYZ Length", "XYZ Length", "", 11),
        #("COLOR_GAMMA", "Color Gamma", "Color Gamma", "", 12),
        ("COORDINATES", "Coordinates", "Coordinates", "", 13),
        # ("LAYER", "Layer", "Layer", "", 14),
        # ("LAYER_MEMBER", "Layer Member", "Layer Member", "", 15),
    ]

    subtype_vector: EnumProperty(
        name='Subtypes',
        items=subtypes_vector,
        default='NONE',
        #update=changeSubType
    ) # type: ignore

    subtypes_color = [
        # # https://docs.blender.org/api/current/bpy_types_enum_items/property_subtype_number_array_items.html#rna-enum-property-subtype-number-array-items
        ("NONE", "None", "None", "", 0),
        ("COLOR", "Color", "Color", "", 1),
        ("COLOR_GAMMA", "Color Gamma", "Color Gamma", "", 12),
    ]

    subtype_color: EnumProperty(
        name='Subtypes',
        items=subtypes_color,
        default='COLOR',
        #update=changeSubType
    ) # type: ignore

    subtypes_float = [
        # https://docs.blender.org/api/current/bpy_types_enum_items/property_subtype_number_items.html#rna-enum-property-subtype-number-items
        ("NONE", "None", "None", "", 0),
        #("PERCENTAGE", "Percentage", "Percentage", "", 1),
        #("FACTOR", "Factor", "Factor", "", 2),
        ("ANGLE", "Angle", "Angle", "", 3),
        #("TIME", "Time", "Time", "", 4),
        ("TIME_ABSOLUTE", "Time(abs)", "Time absolute", "", 5),
        ("DISTANCE", "Distance", "Distance", "", 6),
        ("DISTANCE_CAMERA", "Distance(cam)", "Distance camera", "", 7),
        ("TEMPERATURE", "Temperature", "Temperature", "", 8),
        #("WAVELENGTH", "Wavelength", "Wavelength", "", 9), - Error in Blender ?
        ("POWER", "Power", "Power", "", 10),
    ]

    subtype_float: EnumProperty(
        name='Subtypes',
        items=subtypes_float,
        default='NONE',
        #update=changeSubTypeFloat
    ) # type:  ignore

    base_name = 'data '
    multi_socket_type = 'SvStringsSocket'

    def set_output_socketype(self, slot_bl_idnames):
        """
        1) if the input sockets are a mixed bag of bl_idnames we convert the output socket
        to a generic SvStringsSocket type
        2) if all input sockets where sv_get is successful are of identical bl_idname
        then set the output socket type to match that.
        3) no op if current output socket matches proposed new socket type.
        """

        if not slot_bl_idnames:
            return

        num_bl_idnames = len(set(slot_bl_idnames))
        new_socket_type = slot_bl_idnames[0] if num_bl_idnames == 1 else "SvStringsSocket"

        if self.outputs[0].bl_idname != new_socket_type:
            self.outputs[0].replace_socket(new_socket_type)

    def sv_init(self, context):
        self.width = 260
        if self.mode == 'BOOL_LIST_MODE':
            self.outputs.new('SvStringsSocket', 'data_output').label = 'Boolean'
        elif self.mode == 'INT_LIST_MODE':
            self.outputs.new('SvStringsSocket', 'data_output').label = 'Integers'
        elif self.mode == 'FLOAT_LIST_MODE':
            self.outputs.new('SvStringsSocket', 'data_output').label = 'Floats'
        elif self.mode == 'VECTOR_LIST_MODE':
            self.outputs.new('SvVerticesSocket', 'data_output').label = 'Vectors'
        elif self.mode == 'COLOR_LIST_MODE':
            self.outputs.new('SvVerticesSocket', 'data_output').label = 'Colors'
        else:
            raise Exception(f"[func: sv_init] unknown mode {self.mode}.")
        Correct_ListInput_Length(self, context)
        
        pass
        

    def draw_buttons(self, context, layout):
        if self.mode == 'BOOL_LIST_MODE':
            layout.prop(self, "bool_list_counter", text="List Length (bool)")
        elif self.mode == 'INT_LIST_MODE':
            layout.prop(self, "int_list_counter", text="List Length (int)")
        elif self.mode == 'FLOAT_LIST_MODE':
            layout.prop(self, "float_list_counter", text="List Length (float)")
        elif self.mode == 'VECTOR_LIST_MODE':
            layout.prop(self, "vector_list_counter", text="List Length (vectors)")
        elif self.mode == 'COLOR_LIST_MODE':
            layout.prop(self, "color_list_counter", text="List Length (colors)")
        else:
            raise Exception(f"[func: draw_buttons] unknown mode {self.mode}.")

        layout.row().prop(self, "mode", expand=True)
        if self.mode=='FLOAT_LIST_MODE':
            layout.row().prop(self, "subtype_float", expand=False, text='subtype')
        elif self.mode=='VECTOR_LIST_MODE':
            layout.row().prop(self, "subtype_vector", expand=False, text='subtype')
        elif self.mode=='COLOR_LIST_MODE':
            layout.row().prop(self, "subtype_color", expand=False, text='subtype')
            
        layout.row().prop(self, "invert_mask", text="Invert mask", toggle=True)
        #layout.row().prop(self, "copy_clipboard", text="Copy data to clipboard", toggle=True)
       
        align = True
        if self.mode=='VECTOR_LIST_MODE' or self.mode=='COLOR_LIST_MODE':
            align=False

        col = layout.column(align=align)
        J=0
        if self.mode == 'BOOL_LIST_MODE':
            for I, elem in enumerate(self.bool_list_items):
                split1r = col.row().split(factor=0.3)
                split1r_c1 = split1r.column()
                split1r_c1.prop(elem, f'elem', text=str(I))
                split1r_r = split1r.row()
                split1r_r_s = split1r_r.split(factor=0.3)
                split1r_r_s_c1 = split1r_r_s.column()
                split1r_r_s_c1.prop(elem, f'item_enable', icon_only=True)
                if elem.item_enable==False:
                    split1r_r_s_c2_label1 = '-'
                    split1r_r_s_c2_s_c2_label = ''
                else:
                    split1r_r_s_c2_label1 = f'{J}'
                    split1r_r_s_c2_s_c2_label = f'{elem.elem}'
                    J+=1
                split1r_r_s_c2 = split1r_r_s.column()
                split1r_r_s_c2_s = split1r_r_s_c2.split(factor=0.4)
                split1r_r_s_c2_s_c1 = split1r_r_s_c2_s.column()
                split1r_r_s_c2_s_c1.label(text=split1r_r_s_c2_label1)
                split1r_r_s_c2_s_c2 = split1r_r_s_c2_s.column()
                split1r_r_s_c2_s_c2.alignment='RIGHT'
                split1r_r_s_c2_s_c2.label(text=split1r_r_s_c2_s_c2_label)
                pass
        elif self.mode == 'INT_LIST_MODE':
            for I, elem in enumerate(self.int_list_items):
                s = col.row().split(factor=0.5)
                s_c1 = s.column()
                s_c1.prop(elem, f'elem', text=str(I))
                s_r2 = s.row()
                s_r2_s = s_r2.split(factor=0.2)
                s_r2_s_c1 = s_r2_s.column()
                s_r2_s_c1.prop(elem, f'item_enable', icon_only=True)
                if elem.item_enable==False:
                    split1r_r_s_c2_label1 = '-'
                    split1r_r_s_c2_s_c2_label = ''
                else:
                    split1r_r_s_c2_label1 = f'{J}'
                    split1r_r_s_c2_s_c2_label = f'{elem.elem}'
                    J+=1
                s_r2_s_c2 = s_r2_s.column()
                s_r2_s_c2_s = s_r2_s_c2.split(factor=0.3)
                s_r2_s_c2_s_c1 = s_r2_s_c2_s.column()
                s_r2_s_c2_s_c1.label(text=split1r_r_s_c2_label1)
                s_r2_s_c2_s_c2 = s_r2_s_c2_s.column()
                s_r2_s_c2_s_c2.alignment='RIGHT'
                s_r2_s_c2_s_c2.label(text=split1r_r_s_c2_s_c2_label)
                pass
        elif self.mode == 'FLOAT_LIST_MODE':
            for I, elem in enumerate(self.float_list_items):
                s = col.row().split(factor=0.5)
                s_c1 = s.column()
                s_c1.prop(elem, self.subtype_float, text=str(I))
                s_r2 = s.row()
                s_r2_s = s_r2.split(factor=0.2)
                s_r2_s_c1 = s_r2_s.column()
                s_r2_s_c1.prop(elem, f'item_enable', icon_only=True)
                if elem.item_enable==False:
                    split1r_r_s_c2_label1 = '-'
                    split1r_r_s_c2_s_c2_label = ''
                else:
                    split1r_r_s_c2_label1 = f'{J}'
                    split1r_r_s_c2_s_c2_label = f'{elem.elem}'
                    J+=1
                s_r2_s_c2 = s_r2_s.column()
                s_r2_s_c2_s = s_r2_s_c2.split(factor=0.3)
                s_r2_s_c2_s_c1 = s_r2_s_c2_s.column()
                s_r2_s_c2_s_c1.label(text=split1r_r_s_c2_label1)
                s_r2_s_c2_s_c2 = s_r2_s_c2_s.column()
                s_r2_s_c2_s_c2.alignment='RIGHT'
                s_r2_s_c2_s_c2.label(text=split1r_r_s_c2_s_c2_label)
                pass
        elif self.mode == 'VECTOR_LIST_MODE':
            for I, elem in enumerate(self.vector_list_items):
                s = col.row().split(factor=0.8)
                s_r1 = s.row()
                s_r1.prop(elem, self.subtype_vector, icon_only=True)
                s_r2 = s.row()
                s_r2_c1 = s_r2.column()
                s_r2_c1.prop(elem, f'item_enable', icon_only=True)
                if elem.item_enable==False:
                    s_r2_c2_label1 = '-'
                else:
                    s_r2_c2_label1 = f'{J}'
                    J+=1
                s_r2_c2 = s_r2.column()
                s_r2_c2.label(text=s_r2_c2_label1)
                pass
        elif self.mode == 'COLOR_LIST_MODE':
            for I, elem in enumerate(self.color_list_items):
                s = col.row().split(factor=0.8)
                s_r1 = s.row()
                s_r1.prop(elem, self.subtype_color, icon_only=True)
                s_r2 = s.row()
                s_r2_c1 = s_r2.column()
                s_r2_c1.prop(elem, f'item_enable', icon_only=True)
                if elem.item_enable==False:
                    s_r2_c2_label1 = '-'
                else:
                    s_r2_c2_label1 = f'{J}'
                    J+=1
                s_r2_c2 = s_r2.column()
                s_r2_c2.label(text=s_r2_c2_label1)
                pass
        else:
            raise Exception(f"[func: draw_buttons] unknown mode {self.mode}.")

    def draw_buttons_3dpanel(self, layout, in_menu=None):
        if not in_menu:
            menu = layout.row(align=True).operator('node.popup_3d_menu', text=f'Show: "{self.label or self.name}"')
            menu.tree_name = self.id_data.name
            menu.node_name = self.name
        else:
            layout.label(text=self.label or self.name)
            if self.mode == 'vector':
                colum_list = layout.column(align=True)
                for i in range(self.v_int):
                    row = colum_list.row(align=True)
                    for j in range(3):
                        row.prop(self, 'vector_list', index=i*3+j, text='XYZ'[j]+(self.label if self.label else self.name))
            else:
                colum_list = layout.column(align=True)
                for i in range(self.int_list_counter):
                    row = colum_list.row(align=True)
                    row.prop(self, self.mode, index=i, text=str(i)+(self.label if self.label else self.name))
                    row.scale_x = 0.8

    def process(self):
        data = []
        append = data.append
        if self.outputs[0].is_linked:
            
            if self.mode == 'BOOL_LIST_MODE':
                lst = [[elem.elem for elem in self.bool_list_items if elem.item_enable==True]]
            elif self.mode == 'INT_LIST_MODE':
                lst = [[elem.elem for elem in self.int_list_items if elem.item_enable==True]]
            elif self.mode == 'FLOAT_LIST_MODE':
                lst = [[elem.elem for elem in self.float_list_items if elem.item_enable==True]]
            elif self.mode == 'VECTOR_LIST_MODE':
                lst = [[tuple(Vector(elem.elem)) for elem in self.vector_list_items if elem.item_enable==True]]
            elif self.mode == 'COLOR_LIST_MODE':
                lst = [[tuple(elem.elem) for elem in self.color_list_items if elem.item_enable==True]]
            else:
                raise Exception(f"[func: process] unknown mode {self.mode}.")
            
            data = lst
            
        self.outputs[0].sv_set(data)

classes = [SvListInputBoolEntry, SvListInputIntEntry, SvListInputFloatEntry, SvListInputVectorEntry, SvListInputColorEntry, SvListInputNodeMK2]
register, unregister = bpy.utils.register_classes_factory(classes)