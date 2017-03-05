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
from math import *

import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty, FloatVectorProperty, IntProperty
from mathutils import Vector
import json
import io

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import fullList, updateNode, dataCorrect, match_long_repeat

"""
JSON format:
    {
        "vertices": [[1, 2, 3], [2, 3, 4], [4,5,6]],
        "edges": [[0,1]],
        "faces": [[0,1,2]]
    }
    In vertices list, any of numbers can be replaced by string (variable name).
"""

def evaluate(json, variables):
    result = {}
    result['edges'] = json['edges']
    result['faces'] = json['faces']
    result['vertices'] = []
    
    for vertex in json['vertices']:
        v = []
        for c in vertex:
            if c in variables:
                v.append(variables[c])
            elif isinstance(c, str):
                v.append(0.0)
            else:
                v.append(c)
        result['vertices'].append(v)
    return result

class SvJsonFromMesh(bpy.types.Operator):
    "JSON from selected mesh"
    bl_idname = "node.sverchok_json_from_mesh"
    bl_label = "JSON from mesh"
    bl_options = {'REGISTER'}

    nodename = StringProperty(name='nodename')
    treename = StringProperty(name='treename')

    def execute(self, context):
        if not bpy.context.selected_objects[0].type == 'MESH':
            print("JSON from mesh: selected object is not mesh")
            self.report({'INFO'}, 'It is not a mesh selected')
            return

        object = bpy.context.selected_objects[0].data
        result = {}
        result['vertices'] = list([v.co[:] for v in object.vertices])
        result['edges'] = object.edge_keys
        result['faces'] = [list(p.vertices) for p in object.polygons]

        self.write_values(self.nodename, json.dumps(result, indent=2))
        bpy.data.node_groups[self.treename].nodes[self.nodename].filename = self.nodename
        return{'FINISHED'}

    def write_values(self,text,values):
        texts = bpy.data.texts.items()
        exists = False
        for t in texts:
            if bpy.data.texts[t[0]].name == text:
                exists = True
                break

        if not exists:
            bpy.data.texts.new(text)
        bpy.data.texts[text].clear()
        bpy.data.texts[text].write(values)

class SvMeshEvalNode(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvMeshEvalNode'
    bl_label = 'MeshEvalNode'
    bl_icon = 'OUTLINER_OB_EMPTY'

    filename = StringProperty(default="", update=updateNode)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop_search(self, 'filename', bpy.data, 'texts', text='', icon='TEXT')
        row = layout.row()

        do_text = row.operator('node.sverchok_json_from_mesh', text='from selection')
        do_text.nodename = self.name
        do_text.treename = self.id_data.name

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "a")

        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Faces")

    def load_json(self):
        internal_file = bpy.data.texts[self.filename]
        f = io.StringIO(internal_file.as_string())
        json_data = json.load(f)
        self.validate_json(json_data)
        return json_data
    
    def validate_json(self, json):
        if not "vertices" in json:
            raise Exception("JSON does not have `vertices' key")
        if not "edges" in json:
            raise Exception("JSON does not have `edges' key")
        if not "faces" in json:
            raise Exception("JSON does not have `faces' key")

    def get_variables(self):
        variables = set()
        json = self.load_json()
        if not json:
            return variables

        for vertex in json["vertices"]:
            for c in vertex:
                if isinstance(c, str):
                    variables.add(c)

        return variables

    def adjust_inputs(self):
        variables = self.get_variables()
        print("adjust_input:" + str(variables))
        print("inputs:" + str(self.inputs.keys()))
        for key in self.inputs.keys():
            if key not in variables:
                print("Input {} not in variables {}, remove it".format(key, str(variables)))
                self.inputs.remove(self.inputs[key])
        for v in variables:
            if v not in self.inputs:
                print("Variable {} not in inputs {}, add it".format(v, str(self.inputs.keys())))
                self.inputs.new('StringsSocket', v)

    def update(self):
        '''
        update analyzes the state of the node and returns if the criteria to start processing
        are not met.
        '''

        print("update")
        # keeping the file internal for now.
        if not (self.filename in bpy.data.texts):
            return

        if not ('Edges' in self.outputs):
            return

        self.adjust_inputs()

    def get_input(self):
        variables = self.get_variables()
        result = {}
        for var in variables:
            print(var)
            if self.inputs[var].is_linked:
                result[var] = self.inputs[var].sv_get()[0]
            else:
                result[var] = [0.0]
        return result

    def process(self):

        if not self.outputs[0].is_linked:
            return

        var_names = self.get_variables()
        inputs = self.get_input()
        if not inputs:
            if not var_names:
                inputs = {'a': [0.0]}

        print(inputs)

        result_vertices = []
        result_edges = []
        result_faces = []

        template = self.load_json()

        parameters = match_long_repeat(inputs.values())
        for values in zip(*parameters):
            variables = dict(zip(var_names, values))

            json = evaluate(template, variables)
            print(json['vertices'])
            result_vertices.append(json['vertices'])
            result_edges.append(json['edges'])
            result_faces.append(json['faces'])

        if self.outputs['Vertices'].is_linked:
            self.outputs['Vertices'].sv_set(result_vertices)

        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set(result_edges)

        if self.outputs['Faces'].is_linked:
            self.outputs['Faces'].sv_set(result_faces)


def register():
    bpy.utils.register_class(SvJsonFromMesh)
    bpy.utils.register_class(SvMeshEvalNode)


def unregister():
    bpy.utils.unregister_class(SvJsonFromMesh)
    bpy.utils.unregister_class(SvMeshEvalNode)

