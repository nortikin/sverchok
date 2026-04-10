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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode

from sverchok.data_structure import (updateNode, match_long_repeat, fullList, get_data_nesting_level,
                                     describe_data_shape)

class SvRigidBodyNode(SverchCustomTreeNode, bpy.types.Node):
    '''Set Set rigid Body params per object'''

    bl_idname = 'SvRigidBodyNode'
    bl_label = "Rigid Body (Objects)"
    bl_icon = 'RIGID_BODY'
    is_scene_dependent = True
    is_animation_dependent = True
    
    node_apply : BoolProperty(
        name = "Enable",
        default = True,
        description="On - Enable, Off - remove Rigid Body simulation params from all objects.",
        update = updateNode)

    rigid_body_types = [
            ('RIGID_BODY_TYPE,ACTIVE' , "Active" , "[0] Object is directly controller by simulation results", 0),
            ('RIGID_BODY_TYPE,PASSIVE', "Passive", "[1] Object is directly controller by animation system"  , 1),
        ]

    rigid_body_type : EnumProperty(
        name = "Type",
        items = rigid_body_types,
        default = 'RIGID_BODY_TYPE,ACTIVE',
        update = updateNode)
    
    rigid_body_enabled : BoolProperty(
        name = "Dynamic",
        default = True,
        description="On - Enable, Off - disable Rigid Body. Disable before remove. Rigid Body actively participates to the simulation",
        update = updateNode)

    rigid_body_kinematic : BoolProperty(
        name = "Animated",
        default = False,
        description="Allow rigid Body to be controlled by the anumation system",
        update = updateNode)
    
    rigid_body_mass: FloatProperty(
        name = "Spacing",
        default = 0.0001,
        #min = 0.0,
        description="Percent of space to leave between generated fragment meshes",
        update=updateNode)

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

    rigid_body_collision_shape : EnumProperty(
        name = "Type",
        items = rigid_body_collision_shape_modes,
        default = 'RIGID_BODY_SHAPE_MODE,CONVEX_HULL',
        update = updateNode)

    rigid_body_mesh_source_modes = [
            ('RIGID_BODY_MESH_SOURCE,BASE'   , "Base"   , "Base mesh"                                  , 0),
            ('RIGID_BODY_MESH_SOURCE,DEFORM' , "Deform" , "Deformations (shape keys, deform modifiers)", 1),
            ('RIGID_BODY_MESH_SOURCE,FINAL'  , "Final"  , "All modifiers"                              , 2),
        ]

    rigid_body_mesh_source : EnumProperty(
        name        = "Mesh Source",
        items       = rigid_body_mesh_source_modes,
        default     = 'RIGID_BODY_MESH_SOURCE,DEFORM',
        description  = "Source of the mesh used to create collision shape",
        update      = updateNode)

    rigid_body_friction: FloatProperty(
        name        = "Friction",
        default     = 0.000,
        min         = 0.0,
        max         = 1.0,
        description = "Resistance of object to movement",
        update=updateNode)

    rigid_body_restitution: FloatProperty(
        name        = "Bounciness",
        default     = 0.000,
        min         = 0.0,
        max         = 1.0,
        description = "Tendency of object to bounce after colliding with another (0 = stays still, 1 = perfectly elastic)",
        update=updateNode)
    
    rigid_body_use_margin : BoolProperty(
        name        = "Collision Margin",
        default     = False,
        description = "Use custom collision margin (some shapes will have a visible gap around them)",
        update      = updateNode)

    rigid_body_collision_margin: FloatProperty(
        name        = "Margin",
        default     = 0.000,
        min         = 0.0,
        max         = 1.0,
        description = "Threshold of distance near surface where collisions are still considered (best results when non-zero)",
        update=updateNode)

    rigid_body_linear_damping: FloatProperty(
        name        = "Linear Damping",
        default     = 0.000,
        min         = 0.04,
        max         = 1.0,
        description = "Amount of linear velocity that is lost over time",
        update=updateNode)

    rigid_body_angular_damping: FloatProperty(
        name        = "Angular Damping",
        default     = 0.000,
        min         = 0.0,
        max         = 1.0,
        description = "Amount of angular velocity that is lost over time",
        update=updateNode)
    
    rigid_body_use_deactivation : BoolProperty(
        name        = "Enable Deactivation",
        default     = False,
        description = "Enable deactivation of resting rigid bodies (increases performance and stability but can cause glitches)",
        update  = updateNode)
    
    rigid_body_use_start_deactivated : BoolProperty(
        name        = "Start Deactivated",
        default     = False,
        description = "Deactivate rigid body at the start of the simulation",
        update = updateNode)

    rigid_body_deactivate_linear_velocity: FloatProperty(
        name        = "Linear Velocity Deactivation Threshold",
        default     = 0.4,
        min         = 0.0,
        #max        = 1.0,
        description = "Linear Velocity below which simulation stops simulating object",
        update=updateNode)

    rigid_body_deactivate_angular_velocity: FloatProperty(
        name        = "Angular Velocity Deactivation Threshold",
        default     = 0.000,
        min         = 0.5,
        #max        = 1.0,
        description = "Angular Velocity below which simulation stops simulating object",
        update=updateNode)

    def sv_draw_buttons(self, context, layout):
        box = layout #.box()
        box.column(align=True).prop(self, 'node_apply', text=('Enabled' if self.node_apply==True else 'Disabled'), icon=('GHOST_ENABLED' if self.node_apply==True else 'GHOST_DISABLED') )
        pass

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'objects')
        self.inputs.new('SvStringsSocket', 'rigid_body_type'                        ).prop_name = 'rigid_body_type'
        self.inputs.new('SvStringsSocket', 'rigid_body_enabled'                     ).prop_name = 'rigid_body_enabled'
        self.inputs.new('SvStringsSocket', 'rigid_body_kinematic'                   ).prop_name = 'rigid_body_kinematic'
        self.inputs.new('SvStringsSocket', 'rigid_body_collision_shape'             ).prop_name = 'rigid_body_collision_shape'
        self.inputs.new('SvStringsSocket', 'rigid_body_mesh_source'                 ).prop_name = 'rigid_body_mesh_source'
        self.inputs.new('SvStringsSocket', 'rigid_body_friction'                    ).prop_name = 'rigid_body_friction'
        self.inputs.new('SvStringsSocket', 'rigid_body_restitution'                 ).prop_name = 'rigid_body_restitution'
        self.inputs.new('SvStringsSocket', 'rigid_body_use_margin'                  ).prop_name = 'rigid_body_use_margin'
        self.inputs.new('SvStringsSocket', 'rigid_body_collision_margin'            ).prop_name = 'rigid_body_collision_margin'
        self.inputs.new('SvStringsSocket', 'rigid_body_linear_damping'              ).prop_name = 'rigid_body_linear_damping'
        self.inputs.new('SvStringsSocket', 'rigid_body_angular_damping'             ).prop_name = 'rigid_body_angular_damping'
        self.inputs.new('SvStringsSocket', 'rigid_body_use_deactivation'            ).prop_name = 'rigid_body_use_deactivation'
        self.inputs.new('SvStringsSocket', 'rigid_body_use_start_deactivated'       ).prop_name = 'rigid_body_use_start_deactivated'
        self.inputs.new('SvStringsSocket', 'rigid_body_deactivate_linear_velocity'  ).prop_name = 'rigid_body_deactivate_linear_velocity'
        self.inputs.new('SvStringsSocket', 'rigid_body_deactivate_angular_velocity' ).prop_name = 'rigid_body_deactivate_angular_velocity'

        self.outputs.new('SvObjectSocket', 'objects')
        self.update_all_faces(context)
        pass

    def process(self):
        if not any(socket.is_linked for socket in self.inputs):
            return

        active_obj = bpy.context.view_layer.objects.active
        selected = bpy.context.selected_objects.copy()

        attrs = [
            #"type",
            "enabled",
            "kinematic",
            #"collision_shape",
            #"mesh_source",
            "friction",
            "restitution",
            "use_margin",
            "collision_margin",
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

        objects = self.inputs['objects'].sv_get()

        if bpy.context.mode == 'OBJECT':
            if not bpy.context.scene.rigidbody_world:
                bpy.ops.rigidbody.world_add()

            for I, obj in enumerate(objects):
                if self.node_apply==True:
                    if hasattr(obj, 'rigid_body')==False or obj.rigid_body==None:
                        bpy.context.view_layer.objects.active = obj
                        obj.select_set(True)
                        bpy.ops.rigidbody.object_add()
                    pass
                    obj.rigid_body.type = 'ACTIVE' if self.rigid_body_type=='RIGID_BODY_TYPE,ACTIVE' else 'PASSIVE'
                    for attr in attrs:
                        attr_val = getattr(self, 'rigid_body_'+attr)
                        setattr( obj.rigid_body, attr, attr_val )

                    for attr in attrs1:
                        attr_val = getattr(self, 'rigid_body_'+attr)
                        attr_val = attr_val.split(',')[-1]
                        setattr( obj.rigid_body, attr, attr_val )
                    pass
                else:
                    if hasattr(obj, 'rigid_body')==True and obj.rigid_body is not None:
                        bpy.context.view_layer.objects.active = obj
                        obj.select_set(True)
                        bpy.ops.rigidbody.object_remove()
                    pass
                pass

            # восстановить выделение
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected:
                obj.select_set(True)

            # восстановить активный
            bpy.context.view_layer.objects.active = active_obj
        else:
            pass
        
        self.outputs['objects'].sv_set(objects)
        pass

classes = [SvRigidBodyNode]
register, unregister = bpy.utils.register_classes_factory(classes)
