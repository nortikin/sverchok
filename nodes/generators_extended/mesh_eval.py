# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# upgraded to pointerproperty

import ast
from math import *
from collections import defaultdict
import numpy as np

import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty, FloatVectorProperty, IntProperty, PointerProperty
from mathutils import Vector
import json
import io

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import fullList, updateNode, dataCorrect, match_long_repeat
from sverchok.utils.script_importhelper import safe_names
from sverchok.utils.logging import exception, info

"""
JSON format:
    {
        "defaults": {"a": 1, "b": 2},                    # optional
        "vertices": [[1, 2, 3], [2, 3, 4], [4,5,6]],
        "vertexdata": [1, 1, 2]                          # optional, one item per vertex
        "edges": [[0,1]],
        "faces": [[0,1,2]],
        "facedata": [0]                                  # optional, one item per face
    }
    In vertices list, any of numbers can be replaced by string (variable name).
"""

def get_variables(string):
    root = ast.parse(string, mode='eval')
    result = {node.id for node in ast.walk(root) if isinstance(node, ast.Name)}
    return result.difference(safe_names.keys())

# It could be safer...
def safe_eval(string, variables):
    env = dict()
    env.update(safe_names)
    env.update(variables)
    env["__builtins__"] = {}
    root = ast.parse(string, mode='eval')
    return eval(compile(root, "<expression>", 'eval'), env)

def evaluate(json, variables):
    result = {}
    result['edges'] = json['edges']
    result['faces'] = json['faces']
    result['vertices'] = []
    result['vertexdata'] = []
    result['facedata'] = []

    groups = {}

    def eval_list(coords):
        if isinstance(coords, str):
            coords = [coords]
        if isinstance(coords, dict):
            result = dict()
            for key in coords:
                result[key] = eval_list(coords[key])
            return result

        v = []
        for c in coords:
            if isinstance(c, str):
                try:
                    val = safe_eval(c, variables)
                    #self.debug("EVAL: {} with {} => {}".format(c, variables, val))
                except NameError as e:
                    exception(e)
                    val = 0.0
            else:
                val = c
            v.append(val)
        return v

    for idx, vertex in enumerate(json['vertices']):
        if isinstance(vertex, (list, tuple)) and len(vertex) == 3:
            coords = vertex
        elif isinstance(vertex, (list, tuple)) and len(vertex) == 4 and isinstance(vertex[-1], (str, list, tuple)):
            coords = vertex[:-1]
            g = vertex[-1]
            if isinstance(g, str):
                groupnames = [g]
            else:
                groupnames = g
            for groupname in groupnames:
                if groupname in groups:
                    groups[groupname].append(idx)
                else:
                    groups[groupname] = [idx]

        v = eval_list(coords)
        result['vertices'].append(v)

    for idx, item in enumerate(json.get('vertexdata', [])):
        if isinstance(item, (str, list, tuple, dict)):
            coords = item
        else:
            result['vertexdata'].append(item)
            continue
        
        v = eval_list(coords)
        result['vertexdata'].append(v)

    for idx, item in enumerate(json.get('facedata', [])):
        if isinstance(item, (str, list, tuple, dict)):
            coords = item
        else:
            result['facedata'].append(item)
            continue
        
        v = eval_list(coords)
        result['facedata'].append(v)

    return result, groups

def selected_masks_adding(node):
    """ adding new list masks nodes if none """
    if node.outputs[0].is_linked: return
    loc = node.location

    tree = bpy.context.space_data.edit_tree
    links = tree.links

    mo = tree.nodes.new('MaskListNode')
    mv = tree.nodes.new('SvMoveNodeMK2')
    rf = tree.nodes.new('SvGenNumberRange')
    vi = tree.nodes.new('GenVectorsNode')
    mi = tree.nodes.new('SvMaskJoinNode')
    vd = tree.nodes.new('ViewerNode2')
    mo.location = loc+Vector((300,0))
    mv.location = loc+Vector((550,0))
    vi.location = loc+Vector((350,-225))
    rf.location = loc+Vector((0,-225))
    mi.location = loc+Vector((800,0))
    vd.location = loc+Vector((1000,0))

    links.new(node.outputs[0], mo.inputs[0])   #verts
    links.new(node.outputs[3], mo.inputs[1])   #mask
    links.new(mo.outputs[0], mi.inputs[0])   #mask
    links.new(mo.outputs[3], mv.inputs[0])   #True out
    links.new(vi.outputs[0], mv.inputs[1])   #vector
    links.new(rf.outputs[0], vi.inputs[2])   #range
    links.new(mv.outputs[0], mi.inputs[1])   #True in
    links.new(mo.outputs[4], mi.inputs[2])   #False
    links.new(mi.outputs[0], vd.inputs[0])   #Verts
    links.new(node.outputs[2], vd.inputs[1])   #Faces
    mi.Level = 2
    mo.level = 2
    rf.mode='FRANGE_COUNT'
    rf.stop_=4
    rf.count_=4

class SvJsonFromMesh(bpy.types.Operator):
    "JSON from selected mesh"
    bl_idname = "node.sverchok_json_from_mesh"
    bl_label = "JSON from mesh"
    bl_options = {'REGISTER'}

    nodename: StringProperty(name='nodename')
    treename: StringProperty(name='treename')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        if not bpy.context.selected_objects[0].type == 'MESH':
            node.info("JSON from mesh: selected object is not mesh")
            self.report({'INFO'}, 'It is not a mesh selected')
            return

        object = bpy.context.selected_objects[0]
        mesh = object.data
        result = {}
        verts = []
        isselected = False
        for v in mesh.vertices:
            names = set()
            for grp in v.groups:
                name = object.vertex_groups[grp.group].name
                names.add(name)
            if v.select:
                names.add('Selected')
                isselected = True
            if names:
                vertex = self.round(v) + [list(sorted(names))]
            else:
                vertex = self.round(v)
            verts.append(vertex)

        if isselected:
            if not 'Selected' in node.inputs.keys() and not node.outputs[0].is_linked:
                node.outputs.new('SvStringsSocket', 'Selected')
                if node.sample_tree:
                    selected_masks_adding(node)

        # RGBA
        num_components = 4
        v_count = len(mesh.vertices)
        loop_count = len(mesh.loops)
        #node.debug("Loops: %s, verts: %s", len(mesh.loops), len(mesh.vertices))
        if mesh.vertex_colors:
            vertex_colors = defaultdict(dict)
            layer_names = mesh.vertex_colors.keys()
            for color_layer in mesh.vertex_colors:
                color_data = np.empty(loop_count * num_components, dtype=np.float32)
                vertex_index = np.zeros(loop_count, dtype=int)
                mesh.loops.foreach_get("vertex_index", vertex_index)
                color_layer.data.foreach_get("color", color_data)
                color_data.shape = (loop_count, num_components)
                for idx, v_color in zip(vertex_index, color_data):
                    vertex_colors[idx][color_layer.name] = tuple([float(c) for c in v_color])
            if len(layer_names) == 1:
                layer_name = layer_names[0]
                vertex_colors = [vertex_colors[i].get(layer_name, (0,0,0,1)) for i in range(v_count)]
            else:
                vertex_colors = [vertex_colors[i] for i in range(v_count)]
        else:
            vertex_colors = []

        materials = [p.material_index for p in mesh.polygons]

        result['vertices'] = verts
        result['edges'] = mesh.edge_keys
        result['faces'] = [list(p.vertices) for p in mesh.polygons]
        result['vertexdata'] = vertex_colors
        result['facedata'] = materials

        self.write_values(self.nodename, json.dumps(result, indent=2))
        bpy.data.node_groups[self.treename].nodes[self.nodename].filename = self.nodename
        return{'FINISHED'}

    def round(self, vector):
        precision = bpy.data.node_groups[self.treename].nodes[self.nodename].precision
        vector = [round(x, precision) for x in vector.co[:]]
        return vector

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

class SvMeshEvalNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    """
    Triggers: mesh JSON eval expression
    Tooltip: Generate mesh from parametric JSON expression
    """
    bl_idname = 'SvMeshEvalNode'
    bl_label = 'Mesh Expression'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MESH_EXPRESSION'

    def captured_updateNode(self, context):
        if not self.updating_name_from_pointer:
            text_datablock = self.get_bpy_data_from_name(self.filename, bpy.data.texts)
            if text_datablock:
                self.font_pointer = text_datablock
                self.adjust_sockets()
                updateNode(self, context)

    def pointer_update(self, context):
        self.updating_name_from_pointer = True

        try:
            self.filename = self.file_pointer.name if self.file_pointer else ""
        except Exception as err:
            self.info(err)

        self.updating_name_from_pointer = False
        self.adjust_sockets()
        updateNode(self, context)

    properties_to_skip_iojson = ['file_pointer', 'updating_name_from_pointer']
    updating_name_from_pointer: BoolProperty(name="updating name")
    filename: StringProperty(default="")
    file_pointer: PointerProperty(type=bpy.types.Text, poll=lambda s, o: True, update=pointer_update)

    precision: IntProperty(name = "Precision",
                    description = "Number of decimal places used for coordinates when generating JSON from selection",
                    min=0, max=10, default=8,
                    update=updateNode)

    sample_tree: BoolProperty(name = "Example tree",
                    description = "Create example nodes when generating JSON from selection",
                    default = False,
                    update=updateNode)

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout, icon_only=True)
        row = layout.row()
        row.prop_search(self, 'filename', bpy.data, 'texts', text='', icon='TEXT')
        row = layout.row()

        do_text = row.operator('node.sverchok_json_from_mesh', text='from selection')
        do_text.nodename = self.name
        do_text.treename = self.id_data.name

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "precision")
        layout.prop(self, "sample_tree")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "a")

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvStringsSocket', "VertexData")
        self.outputs.new('SvStringsSocket', "FaceData")

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
            if isinstance(vertex, (list, tuple)) and len(vertex) == 3:
                coords = vertex
            elif isinstance(vertex, (list, tuple)) and len(vertex) == 4 and isinstance(vertex[-1], (str, list, tuple)):
                coords = vertex[:-1]

            for c in coords:
                if isinstance(c, str):
                    vs = get_variables(c)
                    variables.update(vs)

        def get_(c):
            if isinstance(c, str):
                return get_variables(c)
            elif isinstance(c, dict):
                r = set()
                for key in c:
                    r.update(get_(c[key]))
                return r

        for item in json.get("vertexdata", []):
            if isinstance(item, str):
                coords = [item]
            elif isinstance(item, (list, tuple)):
                coords = item

            for c in coords:
                if isinstance(c, str):
                    vs = get_(c)
                    variables.update(vs)

        for item in json.get("facedata", []):
            if isinstance(item, str):
                coords = [item]
            elif isinstance(item, (list, tuple)):
                coords = item

            for c in coords:
                if isinstance(c, str):
                    vs = get_(c)
                    variables.update(vs)

        return list(sorted(list(variables)))

    def get_group_names(self):
        groups = set()
        json = self.load_json()
        if not json:
            return groups

        for vertex in json["vertices"]:
            if isinstance(vertex, (list, tuple)) and len(vertex) == 4 and isinstance(vertex[-1], (str, list, tuple)):
                g = vertex[-1]
                if isinstance(g, str):
                    names = [g]
                else:
                    names = g
                for name in names:
                    if name in ['Vertices', 'Edges', 'Faces']:
                        raise Exception("Invalid name for vertex group. It should not be Vertices, Edges or Faces.")
                    groups.add(name)

        return list(sorted(list(groups)))

    def get_defaults(self):
        result = {}
        json = self.load_json()
        if not json or 'defaults' not in json:
            return result
        if not isinstance(json['defaults'], dict):
            return result
        return json['defaults']

    def adjust_sockets(self):
        variables = self.get_variables()
        #self.debug("adjust_sockets:" + str(variables))
        #self.debug("inputs:" + str(self.inputs.keys()))
        for key in self.inputs.keys():
            if key not in variables:
                self.debug("Input {} not in variables {}, remove it".format(key, str(variables)))
                self.inputs.remove(self.inputs[key])
        for v in variables:
            if v not in self.inputs:
                self.debug("Variable {} not in inputs {}, add it".format(v, str(self.inputs.keys())))
                self.inputs.new('SvStringsSocket', v)

        groups = self.get_group_names()
        for key in self.outputs.keys():
            if key in ['Vertices', 'Edges', 'Faces', 'VertexData', 'FaceData']:
                continue
            if key not in groups:
                self.debug("Output {} not in groups {}, remove it".format(key, str(groups)))
                self.outputs.remove(self.outputs[key])
        for name in sorted(groups):
            if name not in self.outputs:
                self.debug("Group {} not in outputs {}, add it".format(name, str(self.outputs.keys())))
                self.outputs.new('SvStringsSocket', name)


    def sv_update(self):
        '''
        update analyzes the state of the node and returns if the criteria to start processing
        are not met.
        '''

        # keeping the file internal for now.
        if not (self.filename in bpy.data.texts):
            return

        self.adjust_sockets()

    def get_input(self):
        variables = self.get_variables()
        defaults = self.get_defaults()
        result = {}
        default_results = {}

        for var in defaults.keys():
            d = defaults[var]
            if isinstance(d, (int, float)):
                default_results[var] = d

        for var in variables:
            if var in self.inputs and self.inputs[var].is_linked:
                result[var] = self.inputs[var].sv_get()[0]
                default_results[var] = result[var][0]
            else:
                value = defaults.get(var, 1.0)
                if isinstance(value, str):
                    #self.debug("Eval: {} = {}, {}".format(var, value, default_results))
                    value = safe_eval(value, default_results)
                    default_results[var] = value
                result[var] = [value]
            #self.debug("get_input: {} => {}".format(var, result[var]))
        return result

    def groups_to_masks(self, groups, size):
        result = {}
        for name in groups:
            result[name] = [idx in groups[name] for idx in range(size)]
        return result

    def process(self):

        if not self.outputs[0].is_linked:
            return

        var_names = self.get_variables()
        inputs = self.get_input()

        result_vertices = []
        result_edges = []
        result_faces = []
        result_vertex_data = []
        result_face_data = []
        result_masks_dict = {}

        template = self.load_json()

        if var_names:
            input_values = [inputs[name] for name in var_names]
            parameters = match_long_repeat(input_values)
        else:
            parameters = [[[]]]
        for values in zip(*parameters):
            variables = dict(zip(var_names, values))

            json, groups = evaluate(template, variables)
            verts = json['vertices']
            result_vertices.append(verts)
            result_edges.append(json['edges'])
            result_faces.append(json['faces'])
            result_vertex_data.append(json.get('vertexdata', []))
            result_face_data.append(json.get('facedata', []))

            masks = self.groups_to_masks(groups, len(verts))
            for name in masks.keys():
                if name in result_masks_dict:
                    result_masks_dict[name].append(masks[name])
                else:
                    result_masks_dict[name] = [masks[name]]

        self.outputs['Vertices'].sv_set(result_vertices)
        self.outputs['Edges'].sv_set(result_edges)
        self.outputs['Faces'].sv_set(result_faces)
        if 'VertexData' in self.outputs:
            self.outputs['VertexData'].sv_set(result_vertex_data)
        if 'FaceData' in self.outputs:
            self.outputs['FaceData'].sv_set(result_face_data)

        for name in result_masks_dict.keys():
            self.outputs[name].sv_set(result_masks_dict[name])

    def storage_set_data(self, storage):
        geom = storage['geom']
        filename = storage['params']['filename']

        bpy.data.texts.new(filename)
        bpy.data.texts[filename].clear()
        bpy.data.texts[filename].write(geom)

    def storage_get_data(self, storage):
        if self.filename and self.filename in bpy.data.texts:
            text = bpy.data.texts[self.filename].as_string()
            storage['geom'] = text
        else:
            self.warning("Unknown filename: {}".format(self.filename))

def register():
    bpy.utils.register_class(SvJsonFromMesh)
    bpy.utils.register_class(SvMeshEvalNode)


def unregister():
    bpy.utils.unregister_class(SvJsonFromMesh)
    bpy.utils.unregister_class(SvMeshEvalNode)
