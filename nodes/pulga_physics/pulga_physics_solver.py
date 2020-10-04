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
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.pulga_physics_core_2 import pulga_system_init


class SvPulgaPhysicsSolverNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    '''
    Triggers: Simulate Particles
    Tooltip: Modular Physics Engine
    '''
    bl_idname = 'SvPulgaPhysicsSolverNode'
    bl_label = 'Pulga Physics Solver'
    bl_icon = 'MOD_PHYSICS'

    iterations: IntProperty(
        name='Iterations', description='Number of Iterations',
        default=1, min=1, update=updateNode)

    rads_in: FloatProperty(
        name='Radius', description='Used to calculate mass, surface and collisions',
        default=1.0, update=updateNode)

    initial_vel: FloatVectorProperty(
        name='Initial Velocity', description='Initial Velocity',
        size=3, default=(0., 0., 0.),
        precision=3, update=updateNode)

    max_vel: FloatProperty(
        name='Max Velocity', description='Limit maximun speed. 0 = no limit',
        default=0.01, precision=3, update=updateNode)


    density: FloatProperty(
        name='Density', description='Density',
        default=1, update=updateNode)


    def handle_accumulative(self, context):
        '''start cache'''
        if not self.node_id in self.node_cache:
            self.node_cache[self.node_id] = {}
        data = self.node_cache[self.node_id]
        if not self.accumulative:
            for i in range(len(data)):
                self.accumulativity_set_data([], i)
            self.accumulative_parse = False
            self.is_animatable =False
        else:
            self.is_animatable =True

        updateNode(self, context)

    def write_memory_prop(self, data):
        '''write values to string property'''
        self.memory = ''.join(str(data))

    def check_memory_prop(self):
        tx = self.memory
        if len(tx) > 1:
            return ast.literal_eval(tx)
        return []

    def memory_to_property(self, context):
        '''bump memory to text-block'''
        if self.accumulative_parse:

            data = self.node_cache[self.node_id]
            out = []
            for i in range(len(data)):
                out.append([data[i][0].tolist(), data[i][1].tolist(), data[i][2].tolist(), data[i][3].tolist()])

            self.write_memory_prop(out)

    def memory_to_lists(self):
        '''bump memory to output'''
        verts = []
        rads = []
        vel = []
        react = []
        np = self.output_numpy
        data = self.node_cache[self.node_id]
        if type(data) == dict:
            for i in range(len(data)):
                verts.append(data[i][0] if np else data[i][0].tolist())
                rads.append(data[i][1] if np else data[i][1].tolist())
                vel.append(data[i][2] if np else data[i][2].tolist())
                react.append(data[i][3] if np else data[i][3].tolist())
        else:
            data = self.check_memory_prop()
            for i in range(len(data)):
                verts.append(array(data[i][0]) if np else data[i][0])
                rads.append(array(data[i][1]) if np else data[i][1])
                vel.append(array(data[i][2]) if np else data[i][2])
                react.append(array(data[i][3]) if np else data[i][3])

        return verts, rads, vel, react

    def reset_memory(self, context):
        if self.accumulative_reset:
            if not self.accumulative_parse:
                self.node_cache[self.node_id] = {}
            self.accumulative_reset = False
            updateNode(self, context)

    def update_memory(self, context):
        if self.accumulative_update:
            self.accumulative_update = False
            if not self.accumulative_parse:
                updateNode(self, context)

    node_cache = {}
    memory: StringProperty(default="")

    accumulative: BoolProperty(
        name="Accumulative",
        description="Accumulate changes every NodeTree update",
        default=False,
        update=handle_accumulative)

    accumulative_reset: BoolProperty(
        name="Reset",
        description="Restart accumulative memory",
        default=False,
        update=reset_memory)

    accumulative_update: BoolProperty(
        name="Update",
        description="Iterate again",
        default=False,
        update=update_memory)

    accumulative_parse: BoolProperty(
        name="Pause",
        description="Pause processing",
        default=False,
        update=memory_to_property
        )

    def accumulativity_get_data(self):
        '''get data form previous update'''
        data = self.node_cache[self.node_id]
        return data

    def accumulativity_set_data(self, cache, cache_id):
        '''store data form this update'''
        data = self.node_cache[self.node_id]
        data[cache_id] = cache

        return data


    prop_dict = {
        "Initial_Pos"     : (0, ''          , 'v', 0),
        "Iterations"      : (1, 'iterations', 's', 0),
        "rads_in"         : (8, 'rads_in'          , 's', 0),
        "Initial Velocity": (17, 'initial_vel'     , 'v', 0),
        "max_vel"         : (18, 'max_vel'         , 's', 0),
        "Density"         : (27, 'density'         , 's', 0),


    }
    sorted_props = sorted(prop_dict.items(), key=lambda kv: kv[1])

    output_numpy : BoolProperty(name="as NumPy",
        description="Output NumPy arrays ",
        default=False,
        update=updateNode)

    def sv_init(self, context):

        '''create sockets'''
        self.width = 200
        new_input = self.inputs.new
        new_output = self.outputs.new
        vs, ss = 'SvVerticesSocket', 'SvStringsSocket'
        input_type_dict = {
        "v": 'SvVerticesSocket',
        "s": 'SvStringsSocket',

        }
        for input_prop in self.sorted_props:
            input_type = input_type_dict[input_prop[1][2]]
            new_input(input_type, input_prop[0]).prop_name = input_prop[1][1]

        new_input('SvPulgaForceSocket', "Forces")
        new_output('SvVerticesSocket', "Vertices")
        new_output('SvStringsSocket', "Rads")
        new_output('SvVerticesSocket', 'Velocity')
        new_output('SvVerticesSocket', 'Pins Reactions')

        self.is_animatable = False

    def draw_buttons(self, context, layout):
        '''draw buttons on the node'''

        r4 = layout.column(align=True)
        r4.prop(self, "accumulative", toggle=True)

        if self.accumulative:
            cr = r4.row(align=True)
            cr.prop(self, "accumulative_reset", toggle=True)
            cr.prop(self, "accumulative_update",  toggle=True)
            cr.prop(self, "accumulative_parse", toggle=True)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        self.draw_buttons(context, layout)
        layout.prop(self, "output_numpy", toggle=False)


    def get_data(self):
        '''get all data from sockets'''
        parameters = []
        for socket in self.inputs:
            if len(socket.prop_name)>0:

                parameters.append(socket.sv_get())
            else:
                parameters.append(socket.sv_get(default=[[]]))


        return match_long_repeat(parameters)

    def fill_gates_dict(self):
        '''redistribute booleans'''
        gates_dict = {}
        gates_dict["accumulate"] = self.accumulative
        gates_dict["output"] = self.output_numpy


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
            if self.node_id in self.node_cache:
                data = self.node_cache[self.node_id]
                if type(data) != dict:
                    from_file = True
                    self.node_cache[self.node_id] = {}
                    past = self.check_memory_prop()
            else:
                from_file = True
                self.node_cache[self.node_id] = {}
                past = self.check_memory_prop()

        return data, past, from_file

    def process(self):
        '''main node function called every update'''

        si = self.inputs
        so = self.outputs
        if not any(socket.is_linked for socket in so):
            return

        if not si['Initial_Pos'].is_linked or not si['Forces'].is_linked:
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
                cache_new = pulga_system_init(par, gates_dict, out_lists, cache)

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
    bpy.utils.register_class(SvPulgaPhysicsSolverNode)

def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvPulgaPhysicsSolverNode)
