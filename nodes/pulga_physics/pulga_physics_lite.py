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

import ast
from numpy import array
import bpy
from bpy.props import IntProperty, StringProperty, BoolProperty, FloatProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import updateNode, node_id, match_long_repeat
from sverchok.utils.pulga_physics_core import pulga_system_init

FILE_NAME = 'pulga_Memory '


def check_past_file(location):
    '''read text-block and parse values'''
    name = FILE_NAME + location + ".txt"
    text = bpy.data.texts.get(name) or bpy.data.texts.new(name)
    tx = text.as_string()
    if len(tx) > 1:
        return ast.literal_eval(text.as_string())
    else:
        return []


def fill_past_file(p, location):
    '''write values to text-block'''
    name = FILE_NAME + location + ".txt"
    text = bpy.data.texts.get(name) or bpy.data.texts.new(name)
    text.clear()
    text.write(''.join(str(p)))

class SvPulgaPhysicsNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    '''
    Triggers: Springs, Cloth
    Tooltip: Physics Engine
    '''
    bl_idname = 'SvPulgaPhysicsNode'
    bl_label = 'Pulga Physics Lite'
    bl_icon = 'MOD_PHYSICS'

    n_id : StringProperty()

    iterations : IntProperty(
        name='Iterations', description='Number of Iterations',
        default=1, min=1, update=updateNode)

    fixed_len : FloatProperty(
        name='Springs Length', description='Specify spring rest length, 0 to calculate it from initial position',
        default=0.0, update=updateNode)
    spring_k : FloatProperty(
        name='Springs Stiffness', description='Springs stiffness constant',
        default=0.0, precision=4,
        update=updateNode)

    rads_in : FloatProperty(
        name='Radius', description='Used to calculate mass, surface and collisions',
        default=1.0, update=updateNode)

    self_collision : FloatProperty(
        name='Self Collision', description='Collision forces between vertices',
        default=0.0, precision=4, step=1e-2, update=updateNode)
    self_attract : FloatProperty(
        name='Self Attract', description='Attraction between vertices',
        default=0.0, precision=4, step=1e-2, update=updateNode)
    attract_decay : FloatProperty(
        name='Self Attract Decay', description='0 = no decay, 1 = linear, 2 = quadratic...',
        default=0.0, precision=3, update=updateNode)
    grow : FloatProperty(
        name='Grow', description='Shrink if collide with others / Grow if does not ',
        default=0.0, update=updateNode)
    min_rad : FloatProperty(
        name='Min Radius', description='Do not shrink under this value',
        default=0.1, precision=3, update=updateNode)
    max_rad : FloatProperty(
        name='Max Radius', description='Do not grow over this value',
        default=1.0, precision=3, update=updateNode)

    inflate : FloatProperty(
        name='Inflate', description='push geometry along the normals proportional to polygon area',
        default=1.0, precision=3, update=updateNode)

    initial_vel : FloatVectorProperty(
        name='Initial Velocity', description='Initial Velocity',
        size=3, default=(0., 0., 0.),
        precision=3, update=updateNode)

    max_vel : FloatProperty(
        name='Max Velocity', description='Limit maximun speed. 0 = no limit',
        default=0.01, precision=3, update=updateNode)
    drag_force : FloatProperty(
        name='Drag Force', description='Movement resistance from environment',
        default=0.0, precision=3, update=updateNode)
    att_force : FloatProperty(
        name='Attractors Force', description='Attractors Force magnitude',
        default=0.0, precision=3, update=updateNode)
    att_clamp : FloatProperty(
        name='Attractors Clamp', description='Attractors maximum influence distance',
        default=0.0, precision=3, update=updateNode)
    att_decay_power : FloatProperty(
        name='Attractors Decay', description='Decay with distance 0 = no decay, 1 = linear, 2 = quadratic...',
        default=0.0, precision=3, update=updateNode)

    random_seed : IntProperty(
        name='Random Seed', description='Random seed number',
        default=0, min=0, update=updateNode)
    random_force : FloatProperty(
        name='Random Force', description='Random force magnitude',
        default=0.0, update=updateNode)
    random_variation : FloatProperty(
        name='Random Variation', description='Random force variation',
        default=0.0, min=0, max=1, update=updateNode)

    density : FloatProperty(
        name='Density', description='Density',
        default=0.1, update=updateNode)

    gravity : FloatVectorProperty(
        name='Gravity', description='gravity or other constant forces that are mass independent',
        size=3, default=(0., 0., 0.),
        precision=4, update=updateNode)
    wind : FloatVectorProperty(
        name='Wind', description='wind or other constant forces that are mass dependent',
        size=3, default=(0., 0., 0.),
        precision=4, update=updateNode)

    obstacles_bounce : FloatProperty(
        name='Obstacles Bounce', description='Obstacles Bounce',
        default=0.1, update=updateNode)

    def handle_accumulative(self, context):
        '''start cache'''

        data = self.node_cache.get(0)
        if not self.accumulative:
            for i in range(len(data)):
                self.accumulativity_set_data([], i)
            self.accumulative_parse = False
            self.is_animatable =False
        else:
            self.is_animatable =True

        if not data:
            self.node_cache[0] = {}
        updateNode(self, context)

    def memory_to_file(self, context):
        '''bump memory to text-block'''
        if self.accumulative_parse:
            location = self.name + "_"+ node_id(self)
            data = self.node_cache.get(0)
            out = []
            for i in range(len(data)):
                out.append([data[i][0].tolist(), data[i][1].tolist(), data[i][2].tolist(), data[i][3].tolist()])
            fill_past_file(out, location)

    def memory_to_lists(self):
        '''bump memory to output'''
        verts = []
        rads = []
        vel = []
        react = []
        np = self.output_numpy
        data = self.node_cache.get(0)
        if type(data) == dict:
            for i in range(len(data)):
                verts.append(data[i][0] if np else data[i][0].tolist())
                rads.append(data[i][1] if np else data[i][1].tolist())
                vel.append(data[i][2] if np else data[i][2].tolist())
                react.append(data[i][3] if np else data[i][3].tolist())
        else:
            location = self.name + "_"+ node_id(self)
            data = check_past_file(location)
            for i in range(len(data)):
                verts.append(array(data[i][0]) if np else data[i][0])
                rads.append(array(data[i][1]) if np else data[i][1])
                vel.append(array(data[i][2]) if np else data[i][2])
                react.append(array(data[i][3]) if np else data[i][3])

        return verts, rads, vel, react

    def reset_memory(self, context):
        if self.accumulative_reset:
            if not self.accumulative_parse:
                self.node_cache[0] = {}
            self.accumulative_reset = False
            updateNode(self, context)

    def update_memory(self, context):
        if self.accumulative_update:
            self.accumulative_update = False
            if not self.accumulative_parse:
                updateNode(self, context)

    node_cache = {}

    accumulative : BoolProperty(
        name="Accumulative",
        description="Accumulate changes every NodeTree update",
        default=False,
        update=handle_accumulative)

    accumulative_reset : BoolProperty(
        name="Reset",
        description="Restart accumulative memory",
        default=False,
        update=reset_memory)

    accumulative_update : BoolProperty(
        name="Update",
        description="Iterate again",
        default=False,
        update=update_memory)

    accumulative_parse : BoolProperty(
        name="Pause",
        description="Pause processing",
        default=False,
        update=memory_to_file
        )

    def accumulativity_get_data(self):
        '''get data form previous update'''
        data = self.node_cache.get(0)
        return data

    def accumulativity_set_data(self, cache, cache_id):
        '''store data form this update'''
        data = self.node_cache.get(0)
        data[cache_id] = cache

        return data


    prop_dict = {
        "Initial_Pos"     : (0, ''          , 'v', 0),
        "Iterations"      : (1, 'iterations', 's', 0),
        "Springs"         : (2, ''          , 's', 4),
        "fixed_len"       : (4, 'fixed_len' , 's', 4),
        "spring_k"        : (5, 'spring_k'  , 's', 4),
        "Pins"            : (6, ''          , 's', 5),
        "Pins Goal Position"   : (7, ''          , 'v', 5),
        "rads_in"         : (8, 'rads_in'          , 's', 0),
        "self_collision"  : (9, 'self_collision'   , 's', 1),
        "self_attract"    : (10, 'self_attract'    , 's', 2),
        "attract_decay"   : (11, 'attract_decay'   , 's', 2),
        "grow"            : (12, 'grow'            , 's', 3),
        "min_rad"         : (13, 'min_rad'         , 's', 3),
        "max_rad"         : (14, 'max_rad'         , 's', 3),
        "Pols"            : (15, ''                , 's', 7),
        "inflate"         : (16, 'inflate'         , 's', 7),
        "Initial Velocity": (17, 'initial_vel'     , 'v', 0),
        "max_vel"         : (18, 'max_vel'         , 's', 0),
        "drag_force"      : (19, 'drag_force'      , 's', 6),
        "Attractors"      : (20, ''                , 'v', 8),
        "att_force"           : (21, 'att_force'           , 's', 8),
        "att_clamp"       : (22, 'att_clamp'       , 's', 8),
        "att_decay_power" : (23, 'att_decay_power' , 's', 8),
        "random_seed"     : (24, 'random_seed'     , 's', 9),
        "random_force"    : (25, 'random_force'    , 's', 9),
        "random_variation": (26, 'random_variation', 's', 9),
        "Density"         : (27, 'density'         , 's', 0),
        "Gravity"         : (28, 'gravity'         , 'v', 11),
        "Wind"            : (29, 'wind'            , 'v', 11),
        "Bounding Box"    : (30, ''                , 'v', 12),
        "Obstacles"       : (31, ''                , 'v', 10),
        "Obstacles_pols"  : (32, ''                , 's', 10),
        "obstacles_bounce": (33, 'obstacles_bounce', 's', 10),

    }
    sorted_props = sorted(prop_dict.items(), key=lambda kv: kv[1])

    prop_ui_groups = [[] for i in range(13)]
    for input_prop in sorted_props:
        prop_ui_groups[input_prop[1][3]].append(input_prop[0])

    def update_sockets(self, context):
        ''' show and hide gated inputs'''
        prop_triggers = [
            self.self_react_M,
            self.self_attract_M,
            self.fit_M,
            self.springs_M,
            self.pins_M,
            self.drag_M,
            self.inflate_M,
            self.attract_M,
            self.random_M,
            self.obstacles_M,
            self.world_F_M,
            self.bounding_box_M,
        ]
        si = self.inputs
        so = self.outputs

        for i in range(len(prop_triggers)):
            if prop_triggers[i]:
                if si[self.prop_ui_groups[i+1][0]].hide_safe:
                    for p in self.prop_ui_groups[i+1]:
                        si[p].hide_safe = False
            else:
                for p in self.prop_ui_groups[i+1]:
                    si[p].hide_safe = True
        if self.fit_M:
            if so["Rads"].hide_safe:
                so["Rads"].hide_safe = False
        else:
            so["Rads"].hide_safe = True
        if self.pins_M:
            if so["Pins Reactions"].hide_safe:
                so["Pins Reactions"].hide_safe = False
        else:
            so["Pins Reactions"].hide_safe = True

        updateNode(self, context)

    self_react_M : BoolProperty(name="Collision",
        description="Self Collision: collision between input vertices as spheres",
        default=False,
        update=update_sockets)
    self_attract_M : BoolProperty(name="Attraction",
        description="Self Attraction: attract between input vertices as spheres",
        default=False,
        update=update_sockets)
    fit_M : BoolProperty(name="Fit",
        description="Fit: shrink if collide with others, grow if not",
        default=False,
        update=update_sockets)
    springs_M : BoolProperty(name="Springs",
        description="Use springs forces",
        default=False,
        update=update_sockets)
    pins_M : BoolProperty(name="Pin",
        description="Pin (turn to static) mask",
        default=False,
        update=update_sockets)
    inflate_M : BoolProperty(name="Inflate",
        description="Inflate (push geometry along the polygons normals proportional to polygon area",
        default=False,
        update=update_sockets)
    drag_M : BoolProperty(name="Drag",
        description="Drag force",
        default=False,
        update=update_sockets)
    attract_M : BoolProperty(name="Attractors",
        description="Use external attractors",
        default=False,
        update=update_sockets)
    random_M : BoolProperty(name="Random",
        description="Random force",
        default=False,
        update=update_sockets)
    bounding_box_M : BoolProperty(name="Boundaries",
        description="System bounding box",
        default=False,
        update=update_sockets)
    world_F_M : BoolProperty(name="World",
        description="Constant Forces",
        default=False,
        update=update_sockets)
    obstacles_M : BoolProperty(name="Obstacles",
        description="Collision obstacles",
        default=False,
        update=update_sockets)

    output_numpy : BoolProperty(name="as NumPy",
        description="Output NumPy arrays ",
        default=False,
        update=updateNode)

    def sv_init(self, context):

        '''create sockets'''
        self.width = 200
        si = self.inputs.new
        so = self.outputs.new
        vs, ss = 'SvVerticesSocket', 'SvStringsSocket'

        for input_prop in self.sorted_props:
            input_type = vs if input_prop[1][2] == 'v' else ss
            si(input_type, input_prop[0]).prop_name = input_prop[1][1]


        so(vs, "Vertices")
        so(ss, "Rads")
        so(vs, 'Velocity')
        so(vs, 'Pins Reactions')

        self.update_sockets(context)
        self.is_animatable = False

    def draw_buttons(self, context, layout):
        '''draw buttons on the node'''
        c1 = layout.column(align=True)
        r0 = c1.row(align=True)
        r0.prop(self, "self_react_M", toggle=True)
        r0.prop(self, "self_attract_M", toggle=True)
        r0.prop(self, "fit_M", toggle=True)

        r = c1.row(align=True)
        r.prop(self, "springs_M", toggle=True)
        r.prop(self, "pins_M", toggle=True)
        r.prop(self, "inflate_M", toggle=True)


        r2 = c1.row(align=True)
        r2.prop(self, "drag_M", toggle=True)
        r2.prop(self, "attract_M", toggle=True)
        r2.prop(self, "random_M", toggle=True)

        r3 = c1.row(align=True)
        r3.prop(self, "world_F_M", toggle=True)
        r3.prop(self, "obstacles_M", toggle=True)
        r3.prop(self, "bounding_box_M", toggle=True)

        r4 = layout.column(align=True)
        r4.prop(self, "accumulative", toggle=True)

        if self.accumulative:
            cr = r4.row(align=True)
            cr.prop(self, "accumulative_reset", toggle=True)
            cr.prop(self,"accumulative_update",  toggle=True)
            cr.prop(self, "accumulative_parse", toggle=True)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        self.draw_buttons(context, layout)
        layout.prop(self, "output_numpy", toggle=False)


    def get_data(self):
        '''get all data from sockets'''
        si = self.inputs
        parameters = []
        for socket in si:
            if len(socket.prop_name)>0:

                parameters.append(socket.sv_get())
            else:
                parameters.append(socket.sv_get(default=[[]]))


        return match_long_repeat(parameters)

    def fill_gates_dict(self):
        '''redistribute booleans'''
        si = self.inputs
        gates_dict = {}
        gates_dict["accumulate"] = self.accumulative
        gates_dict["self_react"] = [self.self_react_M, self.self_attract_M, self.fit_M]
        gates_dict["Springs"] = [si["Springs"].is_linked, si["fixed_len"].is_linked]
        gates_dict["Pins"] = [si["Pins"].is_linked, si["Pins Goal Position"].is_linked]
        gates_dict["drag"] = [self.drag_M, self.fit_M]
        gates_dict["inflate"] = si["Pols"].is_linked
        gates_dict["random"] = self.random_M
        gates_dict["attractors"] = si["Attractors"].is_linked
        gates_dict["world_f"] = [self.world_F_M, self.fit_M]
        gates_dict["Obstacles"] = si["Obstacles"].is_linked and si["Obstacles_pols"].is_linked
        gates_dict["b_box"] = si["Bounding Box"].is_linked
        gates_dict["output"] = self.output_numpy
        gates_dict["apply_f"] = True

        return gates_dict

    def get_local_cache(self, past, data, from_file, temp_id):
        '''parse individual cached geometry if there is any'''
        cache = []
        if self.accumulative:
            if from_file and len(past) > 0:
                cache = past[temp_id]
            if not from_file and len(data) > 0:
                cache = data.get(temp_id, [])

        return cache

    def get_global_cache(self):
        '''read cached geometry if there is any'''
        from_file = False
        past = []
        data = []
        if self.accumulative:
            data = self.node_cache.get(0)
            if type(data) != dict:
                from_file = True
                self.node_cache[0] = {}
                location = self.name + "_"+ node_id(self)
                past = check_past_file(location)

        return data, past, from_file

    def process(self):
        '''main node function called every update'''

        si = self.inputs
        so = self.outputs
        if not any(socket.is_linked for socket in so):
            return

        if not si['Initial_Pos'].is_linked:
            return
        verts_out = []
        rads_out = []
        velocity_out = []
        reactions_out = []

        if self.accumulative and self.accumulative_parse:
            verts_out, rads_out, velocity_out, reactions_out = self.memory_to_lists()
        else:
            out_lists = [verts_out, rads_out, velocity_out, reactions_out]
            params = self.get_data()
            gates_dict = self.fill_gates_dict()
            data, past, from_file = self.get_global_cache()
            temp_id = 0
            for par in zip(*params):
                cache = self.get_local_cache(past, data, from_file, temp_id)
                par_dict = {}
                for idx, p in enumerate(self.sorted_props):
                    par_dict[p[0]] = par[idx]
                cache_new = pulga_system_init(par_dict, par, gates_dict, out_lists, cache)

                if self.accumulative:
                    self.accumulativity_set_data(cache_new, temp_id)

                temp_id += 1

        if so['Vertices'].is_linked:
            so['Vertices'].sv_set(verts_out)
        if so['Rads'].is_linked:
            so['Rads'].sv_set(rads_out)
        if so['Velocity'].is_linked:
            so['Velocity'].sv_set(velocity_out)
        if so['Pins Reactions'].is_linked:
            so['Pins Reactions'].sv_set(reactions_out)




def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvPulgaPhysicsNode)

def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvPulgaPhysicsNode)
