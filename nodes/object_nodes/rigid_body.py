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

import numpy as np

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, BoolVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_repeat, fullList, get_data_nesting_level, describe_data_shape)

from itertools import zip_longest

rigid_body_params = {
        'type'                          : {'node_property_name': 'rigid_body_type1'                        , 'socket_name': 'rigid_body_type', 'values': [], },
        'mass'                          : {'node_property_name': 'rigid_body_mass1'                        , 'socket_name': 'rigid_body_mass', 'values': [], },
        'enabled'                       : {'node_property_name': 'rigid_body_enabled1'                     , 'socket_name': 'rigid_body_enabled', 'values': [], },
        'kinematic'                     : {'node_property_name': 'rigid_body_kinematic1'                   , 'socket_name': 'rigid_body_kinematic', 'values': [], },
        'collision_shape'               : {'node_property_name': 'rigid_body_collision_shape1'             , 'socket_name': 'rigid_body_collision_shape', 'values': [], },
        'mesh_source'                   : {'node_property_name': 'rigid_body_mesh_source1'                 , 'socket_name': 'rigid_body_mesh_source', 'values': [], },
        'use_deform'                    : {'node_property_name': 'rigid_body_use_deform1'                  , 'socket_name': 'rigid_body_use_deform', 'values': [], },
        'friction'                      : {'node_property_name': 'rigid_body_friction1'                    , 'socket_name': 'rigid_body_friction', 'values': [], },
        'restitution'                   : {'node_property_name': 'rigid_body_restitution1'                 , 'socket_name': 'rigid_body_restitution', 'values': [], },
        'use_margin'                    : {'node_property_name': 'rigid_body_use_margin1'                  , 'socket_name': 'rigid_body_use_margin', 'values': [], },
        'collision_margin'              : {'node_property_name': 'rigid_body_collision_margin1'            , 'socket_name': 'rigid_body_collision_margin', 'values': [], },
        'collision_collections'         : {'node_property_name': 'rigid_body_collision_collections1'       , 'socket_name': 'rigid_body_collision_collections', 'values': [], },
        'linear_damping'                : {'node_property_name': 'rigid_body_linear_damping1'              , 'socket_name': 'rigid_body_linear_damping', 'values': [], },
        'angular_damping'               : {'node_property_name': 'rigid_body_angular_damping1'             , 'socket_name': 'rigid_body_angular_damping', 'values': [], },
        'use_deactivation'              : {'node_property_name': 'rigid_body_use_deactivation1'            , 'socket_name': 'rigid_body_use_deactivation', 'values': [], },
        'use_start_deactivated'         : {'node_property_name': 'rigid_body_use_start_deactivated1'       , 'socket_name': 'rigid_body_use_start_deactivated', 'values': [], },
        'deactivate_linear_velocity'    : {'node_property_name': 'rigid_body_deactivate_linear_velocity1'  , 'socket_name': 'rigid_body_deactivate_linear_velocity', 'values': [], },
        'deactivate_angular_velocity'   : {'node_property_name': 'rigid_body_deactivate_angular_velocity1' , 'socket_name': 'rigid_body_deactivate_angular_velocity', 'values': [], },
        #{'object': '', 'node': 'rigid_body_', },
    }

lst_rigid_body_params = [
    "type",
    "mass",
    "enabled",
    "kinematic",
    "collision_shape",
    "mesh_source",
    "use_deform",
    "friction",
    "restitution",
    "use_margin",
    "collision_margin",
    "collision_collections",
    "linear_damping",
    "angular_damping",
    "use_deactivation",
    "use_start_deactivated",
    "deactivate_linear_velocity",
    "deactivate_angular_velocity",
]


def copy_rigid_body_animation(obj, list_target_objects, only_clear=False):
    if not obj.animation_data or not obj.animation_data.action:
        return

    src_action = obj.animation_data.action

    def is_rb_curve(fcurve):
        return any(
            fcurve.data_path == f"rigid_body.{param}"
            or fcurve.data_path.startswith(f"rigid_body.{param}[")
            for param in lst_rigid_body_params
        )

    src_fcurves = []

    for slot in src_action.slots:
        if slot and hasattr(slot, "fcurves"):
            for fc in slot.fcurves:
                if is_rb_curve(fc):
                    src_fcurves.append(fc)
                pass
        pass

    for target in list_target_objects:

        if not target.rigid_body:
            continue

        # --- ОЧИСТКА АНИМАЦИИ ---
        if target.animation_data:
            if target.animation_data.action:
                bpy.data.actions.remove(target.animation_data.action)
            target.animation_data_clear()
        if only_clear==True:
            continue

        target.animation_data_create()

        # создаём новый action
        new_action = bpy.data.actions.new(name=f"{target.name}_RB_Action")
        target.animation_data.action = new_action

        for fc in src_fcurves:
            new_fc = new_action.fcurves.new(
                data_path=fc.data_path,
                index=fc.array_index
            )

            new_fc.keyframe_points.add(len(fc.keyframe_points))

            for i, kp in enumerate(fc.keyframe_points):
                new_kp = new_fc.keyframe_points[i]

                new_kp.co = kp.co[:]
                new_kp.handle_left = kp.handle_left[:]
                new_kp.handle_right = kp.handle_right[:]

                new_kp.handle_left_type = kp.handle_left_type
                new_kp.handle_right_type = kp.handle_right_type
                new_kp.interpolation = kp.interpolation

            new_fc.update()
        pass
    pass

class SvRigidBodyNode(SverchCustomTreeNode, bpy.types.Node):
    '''Set Set rigid Body params per object'''

    bl_idname = 'SvRigidBodyNode'
    bl_label = "Rigid Body (Objects)"
    bl_icon = 'RIGID_BODY'
    is_scene_dependent = False
    is_animation_dependent = False
    
    copy_objects_animation : BoolProperty(
        name        = "Copy Animation",
        description = "Copy animation keys of mapped objects to objects",
        default     = False,
        options     = {'SKIP_SAVE'},
        update      = updateNode,
    )
    clear_objects_animation : BoolProperty(
        name        = "Clear Animation",
        description = "Copy animation keys of mapped objects to objects",
        default     = False,
        options     = {'SKIP_SAVE'},
        update      = updateNode,
    )

    node_in_use : BoolProperty(
        name        = "Enable",
        description = "On - add Rigid Body settings to all objects\nOff - remove Rigid Body settings from all objects.",
        default     = True,
        update      = updateNode,
    )
    
    object_in_pointer: bpy.props.PointerProperty(
        name        = "Objects",
        description = "Objects where to copy Rigid Body settings",
        type        = bpy.types.Object,
    )

    rigid_body_settings1: bpy.props.PointerProperty(
        name        = "Rigid Body settings",
        description = "Where to get Rigid Body settings for objects",
        type        = bpy.types.Object,
    )

    source_object_pointer_data_from_modes = [
            ('RIGID_BODY_DATA_FROM,OBJECTS' , "Objects"      , "Apply Rigid Body settings from objects"      , 0),
            ('RIGID_BODY_DATA_FROM,SETTINGS', "Node Settings", "Apply Rigid Body settings from input sockets", 1),
        ]

    source_object_pointer_data_from1 : EnumProperty(
        name        = "Type",
        description = "Role of object in Rigid Body Simulations",
        items       = source_object_pointer_data_from_modes,
        default     = 'RIGID_BODY_DATA_FROM,OBJECTS',
        update      = updateNode,
    )
    
    objects_map1 : bpy.props.IntProperty(
        name        = "Objects map",
        description = "Objects map to Rigid Body settings",
        default     = 0,
        #min        = 0,
        update      = updateNode,
    )

    objects_map_mode_modes = [
            ('RIGID_BODY_MAP,MAPPING' , "Mapping" , "Mapping objects by input socket data", 0),
            ('RIGID_BODY_MAP,INDEXING', "Indexing", "Mapping objects by indexes (ignore mapping)"  , 1),
        ]

    objects_map_mode1 : EnumProperty(
        name        = "Objects map mode",
        description = "Mappings Objects by map or by Indexes",
        items       = objects_map_mode_modes,
        default     = 'RIGID_BODY_MAP,MAPPING',
        update      = updateNode,
    )

    rigid_body_type_modes = [
            ('RIGID_BODY_TYPE,ACTIVE' , "Active" , "Object is directly controller by simulation results", 0),
            ('RIGID_BODY_TYPE,PASSIVE', "Passive", "Object is directly controller by animation system"  , 1),
        ]

    rigid_body_type1 : EnumProperty(
        name        = "Type",
        description = "Role of object in Rigid Body Simulations",
        items       = rigid_body_type_modes,
        default     = 'RIGID_BODY_TYPE,ACTIVE',
        update      = updateNode,
    )
    
    rigid_body_mass1: FloatProperty(
        name        = "Mass",
        description = "How much the object 'weighs' irrespective of gravity",
        default     = 1.0,
        min         = 0.001,
        precision   = 3,
        update      = updateNode,
    )
    
    rigid_body_enabled1 : BoolProperty(
        name        = "Dynamic",
        description = "On - enable Simulation of Rigid Body\nOff - disable Simulation\nDisable before remove node. Rigid Body actively participates to the simulation",
        default     = True,
        update = updateNode)

    rigid_body_kinematic1 : BoolProperty(
        name        = "Animated",
        description = "Allow rigid Body to be controlled by the animation system",
        default     = False,
        update      = updateNode,
    )

    rigid_body_collision_shape_modes = [
            ('RIGID_BODY_SHAPE_MODE,BOX'          , "Box"            , "Box-like shapes (i.e. cubes), including planes (i.e. ground planes)"                                      , 'MESH_CUBE'       , 0),
            ('RIGID_BODY_SHAPE_MODE,SPHERE'       , "Sphere"         , ""                                                                                                         , 'MESH_UVSPHERE'   , 1),
            ('RIGID_BODY_SHAPE_MODE,CAPSULE'      , "Capsule"        , ""                                                                                                         , 'MESH_CAPSULE'    , 2),
            ('RIGID_BODY_SHAPE_MODE,CYLINDER'     , "Cylinder"       , ""                                                                                                         , 'MESH_CYLINDER'   , 3),
            ('RIGID_BODY_SHAPE_MODE,CONE'         , "Cone"           , ""                                                                                                         , 'MESH_CONE'       , 4),
            ('RIGID_BODY_SHAPE_MODE,CONVEX_HULL'  , "Convex Hull"    , "A mesh-like surface encompassing (i.e. shrinkwrap over) all vertices (best results with fewer vertices)"  , 'MESH_ICOSPHERE'  , 5),
            ('RIGID_BODY_SHAPE_MODE,MESH'         , "Mesh"           , "Mesh consisting of triangles only, allowing for more detailed interactions than convex hulls"             , 'MESH_MONKEY'     , 6),
            ('RIGID_BODY_SHAPE_MODE,COMPOUND'     , "Compound Parent", "Combines all of its direct rigid body children into one rigid object"                                     , 'MESH_DATA'       , 7),
        ]

    rigid_body_collision_shape1 : EnumProperty(
        name        = "Shape",
        description = "Collision Shape of object in Rigid Body Simulations",
        items       = rigid_body_collision_shape_modes,
        default     = 'RIGID_BODY_SHAPE_MODE,CONVEX_HULL',
        update      = updateNode,
    )

    rigid_body_mesh_source_modes = [
            ('RIGID_BODY_MESH_SOURCE,BASE'   , "Base"   , "Base mesh"                                  , 0),
            ('RIGID_BODY_MESH_SOURCE,DEFORM' , "Deform" , "Deformations (shape keys, deform modifiers)", 1),
            ('RIGID_BODY_MESH_SOURCE,FINAL'  , "Final"  , "All modifiers"                              , 2),
        ]

    rigid_body_mesh_source1 : EnumProperty(
        name        = "Source",
        description = "Source of the mesh used to create collision shape",
        items       = rigid_body_mesh_source_modes,
        default     = 'RIGID_BODY_MESH_SOURCE,DEFORM',
        update      = updateNode,
    )
    
    rigid_body_use_deform1 : BoolProperty(
        name        = "Deforming",
        description = "Rigid body deforms during simulation",
        default     = False,
        update      = updateNode,
    )

    rigid_body_friction1: FloatProperty(
        name        = "Friction",
        description = "Resistance of object to movement",
        default     = 0.000,
        min         = 0.0,
        max         = 1.0,
        update      = updateNode,
    )

    rigid_body_restitution1: FloatProperty(
        name        = "Bounciness",
        default     = 0.000,
        min         = 0.0,
        max         = 1.0,
        description = "Tendency of object to bounce after colliding with another (0 = stays still, 1 = perfectly elastic)",
        update      = updateNode,
    )
    
    rigid_body_use_margin1 : BoolProperty(
        name        = "Collision Margin",
        default     = False,
        description = "Use custom collision margin (some shapes will have a visible gap around them)",
        update      = updateNode)

    rigid_body_collision_margin1: FloatProperty(
        name        = "Margin",
        description = "Threshold of distance near surface where collisions are still considered (best results when non-zero)",
        default     = 0.000,
        min         = 0.0,
        max         = 1.0,
        update      = updateNode,
    )
    
    rigid_body_collision_collections1: BoolVectorProperty(
        name        = "Collision Collection",
        description = "Collision collections rigid body belongs to",
        size=20,
        update      = updateNode,
    )

    rigid_body_linear_damping1: FloatProperty(
        name        = "Damping Translation",
        description = "Amount of linear velocity that is lost over time",
        default     = 0.000,
        min         = 0.04,
        max         = 1.0,
        precision   = 3,
        update      = updateNode,
    )

    rigid_body_angular_damping1: FloatProperty(
        name        = "Rotation",
        description = "Amount of angular velocity that is lost over time",
        default     = 0.000,
        min         = 0.1,
        max         = 1.0,
        precision   = 3,
        update      = updateNode,
    )
    
    rigid_body_use_deactivation1 : BoolProperty(
        name        = "Deactivation",
        description = "Enable deactivation of resting rigid bodies (increases performance and stability but can cause glitches)",
        default     = False,
        update      = updateNode)
    
    rigid_body_use_start_deactivated1 : BoolProperty(
        name        = "Start Deactivated",
        description = "Deactivate rigid body at the start of the simulation",
        default     = False,
        update      = updateNode,
    )

    rigid_body_deactivate_linear_velocity1: FloatProperty(
        name        = "Velocity Linear",
        description = "Linear Velocity below which simulation stops simulating object",
        default     = 0.4,
        min         = 0.0,
        #max        = 1.0,
        update      = updateNode,
    )

    rigid_body_deactivate_angular_velocity1: FloatProperty(
        name        = "Angular",
        description = "Angular Velocity below which simulation stops simulating object",
        default     = 0.000,
        min         = 0.5,
        #max        = 1.0,
        update      = updateNode,
    )
    
    def custom_draw_collision_collections(self, socket, context, layout, post_process=False):
        if self.source_object_pointer_data_from1=='RIGID_BODY_DATA_FROM,OBJECTS':
            layout.enabled = False
        if post_process==False:
            return 'POST_PROCESS'
        if socket.is_linked==True:
            layout.enabled = False
        root = layout.row(align=True)
        row = root.row()
        row.alignment = 'LEFT'
        grid = root.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True)
        grid1 = grid.grid_flow(row_major=True, columns=5, even_columns=True, even_rows=True, align=True)
        for I in range(0,5):
            grid1.prop(self, "rigid_body_collision_collections1", index=I, text=str(I), toggle=True)
        for I in range(10,15):
            grid1.prop(self, "rigid_body_collision_collections1", index=I, text=str(I), toggle=True)
        grid2 = grid.grid_flow(row_major=True, columns=5, even_columns=True, even_rows=True, align=True)
        for I in range(5,10):
            grid2.prop(self, "rigid_body_collision_collections1", index=I, text=str(I), toggle=True)
        for I in range(15,20):
            grid2.prop(self, "rigid_body_collision_collections1", index=I, text=str(I), toggle=True)

        pass


    def sv_draw_buttons(self, context, layout):
        box = layout.box()
        box.prop(self, 'node_in_use', text=('Rigid Body Activated' if self.node_in_use==True else 'Rigid Body Removed'), icon=('X' if self.node_in_use==True else 'RIGID_BODY') )
        #box.prop(self, 'source_object_pointer' )
        elem = box.column(align=True)
        elem.column().label(text='Apply Rigid Body settings from:')
        elem.row(align=True).prop(self, 'source_object_pointer_data_from1', expand=True)
        # col = elem.row()
        # col.enabled = True if self.source_object_pointer_data_from1=='RIGID_BODY_DATA_FROM,OBJECTS' else False
        # col.prop(self, 'copy_objects_animation', toggle=True)
        # col.prop(self, 'clear_objects_animation', toggle=True)
        elem.column().label(text='Objects map mode:')
        elem.row(align=True).prop(self, 'objects_map_mode1', expand=True)

        pass

    def custom_draw_input_sockets_objects_map(self, socket, context, layout):
        if self.objects_map_mode1=='RIGID_BODY_MAP,INDEXING':
            layout.enabled = False
        if socket.is_linked==True:
            layout.alignment = "LEFT"

        return 'CONTINUE'

    def custom_draw_input_sockets_rigid_body_source_objects(self, socket, context, layout):
        if self.source_object_pointer_data_from1=='RIGID_BODY_DATA_FROM,SETTINGS':
            layout.enabled = False
        if socket.is_linked==True:
            layout.alignment = "LEFT"

        return 'CONTINUE'

    def custom_draw_input_sockets_rigid_body_params(self, socket, context, layout):
        if self.source_object_pointer_data_from1=='RIGID_BODY_DATA_FROM,OBJECTS':
            layout.enabled = False
        if socket.is_linked==True:
            layout.alignment = "LEFT"
            pass

        return 'CONTINUE'

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket' , 'objects'                                ).prop_name = 'object_in_pointer'
        self.inputs.new('SvStringsSocket', 'objects_map'                            ).prop_name = 'objects_map1'
        self.inputs.new('SvObjectSocket' , 'rigid_body_settings'                    ).prop_name = 'rigid_body_settings1'
        self.inputs.new('SvStringsSocket', 'rigid_body_type'                        ).prop_name = 'rigid_body_type1'
        self.inputs.new('SvStringsSocket', 'rigid_body_mass'                        ).prop_name = 'rigid_body_mass1'
        self.inputs.new('SvStringsSocket', 'rigid_body_enabled'                     ).prop_name = 'rigid_body_enabled1'
        self.inputs.new('SvStringsSocket', 'rigid_body_kinematic'                   ).prop_name = 'rigid_body_kinematic1'
        self.inputs.new('SvStringsSocket', 'rigid_body_collision_shape'             ).prop_name = 'rigid_body_collision_shape1'
        self.inputs.new('SvStringsSocket', 'rigid_body_mesh_source'                 ).prop_name = 'rigid_body_mesh_source1'
        self.inputs.new('SvStringsSocket', 'rigid_body_use_deform'                  ).prop_name = 'rigid_body_use_deform1'
        self.inputs.new('SvStringsSocket', 'rigid_body_friction'                    ).prop_name = 'rigid_body_friction1'
        self.inputs.new('SvStringsSocket', 'rigid_body_restitution'                 ).prop_name = 'rigid_body_restitution1'
        self.inputs.new('SvStringsSocket', 'rigid_body_use_margin'                  ).prop_name = 'rigid_body_use_margin1'
        self.inputs.new('SvStringsSocket', 'rigid_body_collision_margin'            ).prop_name = 'rigid_body_collision_margin1'
        self.inputs.new('SvStringsSocket', 'rigid_body_collision_collections'       ) #.prop_name = 'rigid_body_collision_collections1' # assigned prop_name conflict with custom_draw 
        self.inputs.new('SvStringsSocket', 'rigid_body_linear_damping'              ).prop_name = 'rigid_body_linear_damping1'
        self.inputs.new('SvStringsSocket', 'rigid_body_angular_damping'             ).prop_name = 'rigid_body_angular_damping1'
        self.inputs.new('SvStringsSocket', 'rigid_body_use_deactivation'            ).prop_name = 'rigid_body_use_deactivation1'
        self.inputs.new('SvStringsSocket', 'rigid_body_use_start_deactivated'       ).prop_name = 'rigid_body_use_start_deactivated1'
        self.inputs.new('SvStringsSocket', 'rigid_body_deactivate_linear_velocity'  ).prop_name = 'rigid_body_deactivate_linear_velocity1'
        self.inputs.new('SvStringsSocket', 'rigid_body_deactivate_angular_velocity' ).prop_name = 'rigid_body_deactivate_angular_velocity1'

        #self.inputs['objects'                           ].label       = 'Objects'
        #self.inputs['objects'                           ].description = 'Objects description'

        for (_sn, value) in {
                'objects':'object_in_pointer',
                'objects_map':'objects_map1',
                'rigid_body_settings':'rigid_body_settings1'}.items():
            name = None
            type = None
            description=None
            if hasattr(self.__class__, 'bl_rna')==True and value in self.__class__.bl_rna.properties:
                prop = self.__class__.bl_rna.properties[value]
                name = prop.name
                type = prop.type
                description = prop.description
            if description:
                self.inputs[_sn].description = description
                pass

            pass
        self.inputs['objects_map'           ].custom_draw = 'custom_draw_input_sockets_objects_map'
        self.inputs['rigid_body_settings'   ].custom_draw = 'custom_draw_input_sockets_rigid_body_source_objects'

        #for sn in sockets_input_names_for_params:
        for sn in rigid_body_params:
            _sn = 'rigid_body_'+sn
            name = None
            type = None
            description=None
            if hasattr(self.__class__, 'bl_rna')==True and _sn in self.__class__.bl_rna.properties:
                prop = self.__class__.bl_rna.properties[_sn]
                name = prop.name
                type = prop.type
                description = prop.description
            if description:
                self.inputs[_sn].description = f'{description}'
            self.inputs[_sn].custom_draw = 'custom_draw_input_sockets_rigid_body_params'

        self.inputs['rigid_body_collision_collections'  ].custom_draw = 'custom_draw_collision_collections'
        self.inputs['rigid_body_collision_collections'  ].label       = 'Collision Collection'
        
        self.outputs.new('SvObjectSocket', 'objects')
        self.outputs['objects'].label       = 'Objects'
        pass

    def process(self):
        if not any(socket.is_linked for socket in self.inputs):
            return

        # active_obj = bpy.context.view_layer.objects.active
        # selected = bpy.context.selected_objects.copy() if hasattr(bpy.context, 'selected_objects') else None

        attrs = [
            #"type",
            "mass",
            "enabled",
            "kinematic",
            #"collision_shape",
            #"mesh_source",
            "use_deform",
            "friction",
            "restitution",
            "use_margin",
            "collision_margin",
            #"collision_collections",
            "linear_damping",
            "angular_damping",
            "use_deactivation",
            "use_start_deactivated",
            "deactivate_linear_velocity",
            "deactivate_angular_velocity",
        ]
        attrs1 = [
            #"type",
            "collision_shape",
            "mesh_source",
        ]

        objects             = self.inputs['objects'             ].sv_get(deepcopy=False, default=[self.object_in_pointer])
        objects_map         = self.inputs['objects_map'         ].sv_get(deepcopy=False, default=[self.objects_map1])
        rigid_body_settings = self.inputs['rigid_body_settings' ].sv_get(deepcopy=False, default=[self.rigid_body_settings1])

        if self.node_in_use==True:
            if self.inputs['objects_map'].is_linked==False:
                objects_map = [self.objects_map1] * len(objects)
                pass

            if self.objects_map_mode1=='RIGID_BODY_MAP,INDEXING':
                objects_map = [I for I in range(len(objects))]
                pass
            set_objects_map = set(objects_map)
            len_objects_map = len(objects_map)
            if len_objects_map==0:
                raise Exception(f'Objects map has no elements: 0')
            
            index_min_settings = min(set_objects_map)
            index_max_settings = max(set_objects_map)
            len_rigid_body_settings = len(rigid_body_settings)
            # indexes can be negative. )))
            if self.objects_map_mode1=='RIGID_BODY_MAP,MAPPING' and (index_min_settings<-(len_rigid_body_settings-1) or (len_rigid_body_settings-1)<index_max_settings):
                raise Exception(f'Indexes in Objects map is out of range: [{index_min_settings}:{index_max_settings}] out of Rigid Body settings [{-len_rigid_body_settings}:{len_rigid_body_settings}]')

            input_sockets_settings = dict()
            # read data in general input sockets
            for (name, params) in rigid_body_params.items():
                node_property_name = params['node_property_name']
                socket_name = params['socket_name']
                if socket_name not in self.inputs:
                    raise Exception(f'No input socket with name {socket_name}.')

                prop_type = None
                if hasattr(self.__class__, 'bl_rna')==True and node_property_name in self.__class__.bl_rna.properties:
                    prop = self.__class__.bl_rna.properties[node_property_name]
                    prop_type = prop.type
                else:
                    # development error.
                    raise Exception(f'Unknown property {node_property_name}. Check settings params')
                
                default_prop_value = getattr(self, node_property_name)
                if prop_type=='ENUM':
                    # enum properties of default value has prefix to remove
                    default_prop_value = default_prop_value.split(',')[-1]
                    pass
                socket = self.inputs[socket_name]
                if socket.is_linked==True:
                    socket_value =self.inputs[socket_name].sv_get(deepcopy=False)
                    len_socket_value = len(socket_value)
                    # align objects and input setting socket
                    if len_socket_value>len_objects_map:
                        socket_value = socket_value[:len_objects_map]
                    elif len_socket_value<len_objects_map-1:
                        socket_value += [socket_value[-1]]*(len_objects_map-len(socket_value))
                    pass

                else:
                    socket_value = [default_prop_value]*len_objects_map
                input_sockets_settings[name] = socket_value
                pass

            if len(objects)<len(objects_map):
                raise Exception(f"Number of Objects are less Number of Objects Map")
            else:
                if bpy.context.mode == 'OBJECT':
                    
                    inputs_settings = []
                    # read settings

                    rigid_body_objects_for_animation = []
                    for I, ID in enumerate(objects_map):
                        rigid_body_settings_ID = dict()
                        if self.source_object_pointer_data_from1=='RIGID_BODY_DATA_FROM,OBJECTS':
                            if ID<-len_rigid_body_settings or len_rigid_body_settings-1<ID:
                                raise Exception(f"No Rigid Body settings[{ID}] in the Objects Map[{I}]. Allowed range in Rigid Body settings is [{-(len_rigid_body_settings-1)}:{len_rigid_body_settings-1}]")
                            rigid_body_objects_for_animation.append(rigid_body_settings[ID])
                            rigid_body = rigid_body_settings[ID].rigid_body
                            for (name, param) in rigid_body_params.items():
                                rigid_body_settings_ID[name] = getattr(rigid_body, name)
                            pass
                        elif self.source_object_pointer_data_from1=='RIGID_BODY_DATA_FROM,SETTINGS':
                            for (name, param) in rigid_body_params.items():
                                value = input_sockets_settings[name][ID]
                                rigid_body_settings_ID[name] = value
                            pass
                        else:
                            # development exception. Check enum values
                            raise Exception(f'Unknown type of self.source_object_pointer_data_from1={self.source_object_pointer_data_from1}')
                        inputs_settings.append(rigid_body_settings_ID)
                        pass
                    pass

                    if not bpy.context.scene.rigidbody_world:
                        bpy.ops.rigidbody.world_add()

                    for I, obj in enumerate(objects):
                        if obj:
                            # Add active object as Rigid Body
                            if hasattr(obj, 'rigid_body')==False or obj.rigid_body==None:
                                # bpy.context.view_layer.objects.active = obj
                                # obj.select_set(True)
                                # bpy.ops.rigidbody.object_add()

                                with bpy.context.temp_override(
                                    object                      =  obj,
                                    active_object               =  obj,
                                    selected_objects            = [obj],
                                    selected_editable_objects   = [obj],
                                    view_layer=bpy.context.view_layer, ):
                                        bpy.ops.rigidbody.object_add()
                                        pass
                            pass

                            # if self.copy_objects_animation:
                            #     try:
                            #         copy_rigid_body_animation(rigid_body_settings[I], [obj])
                            #     except Exception as ex:
                            #         print(f"Произошла ошибка при копировании анимации {ex}")
                            #         pass
                            #     pass
                            # if self.clear_objects_animation:
                            #     try:
                            #         copy_rigid_body_animation(rigid_body_settings[I], [obj], only_clear=True)
                            #     except Exception as ex:
                            #         print(f"Произошла ошибка при очистке анимации {ex}")
                            #         pass
                            #     self.clear_objects_animation = False
                            #     pass
                            
                            inputs_settings_I = inputs_settings[I]
                            for (name, value) in inputs_settings_I.items():
                                setattr( obj.rigid_body, name, value )
                                pass
                            pass
                        else:
                            #raise Exception(f"Object[{I}] is None")
                            pass
                        pass
                    # if self.copy_objects_animation or self.clear_objects_animation:
                    #     self.copy_objects_animation = False
                    #     self.clear_objects_animation = False

                    # if selected:
                    #     # # восстановить выделение
                    #     # # TODO: Кажется срабатывает событие изменения сцены при этом. Нужно как-то отключить обработку этого события при восстановлении select
                    #     # bpy.ops.object.select_all(action='DESELECT')
                    #     # for obj in selected:
                    #     #     obj.select_set(True)
                    #     pass

                    # восстановить активный
                    # bpy.context.view_layer.objects.active = active_obj
                    pass
                pass
            pass
        else:
            for I, obj in enumerate(objects):
                if obj:
                    # Remove Rigid Body settings from Object
                    if hasattr(obj, 'rigid_body')==True and obj.rigid_body is not None:
                        # bpy.context.view_layer.objects.active = obj
                        # obj.select_set(True)
                        # bpy.ops.rigidbody.object_remove()
                        with bpy.context.temp_override(
                            object                      =  obj,
                            active_object               =  obj,
                            selected_objects            = [obj],
                            selected_editable_objects   = [obj],
                            view_layer=bpy.context.view_layer, ):
                                bpy.ops.rigidbody.object_remove()
                                pass
                    pass
                pass
            pass
        self.outputs['objects'].sv_set(objects)
        pass

classes = [SvRigidBodyNode]
register, unregister = bpy.utils.register_classes_factory(classes)
