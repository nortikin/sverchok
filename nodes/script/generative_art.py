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

''' by Eleanor Howick | 2015 https://github.com/elfnor
    LSystem code from Philip Rideout  https://github.com/prideout/lsystem '''

import os
import sys

import math
import string
import random
from xml.etree.cElementTree import fromstring
from dataclasses import dataclass

import bpy
from bpy.props import IntProperty, StringProperty, BoolProperty
import mathutils as mu
import sverchok
from sverchok.utils.sv_update_utils import sv_get_local_path
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, Vector_generate

FAIL_COLOR = (0.8, 0.1, 0.1)
READY_COLOR = (0, 0.6, 0.8)

sv_path = os.path.dirname(sv_get_local_path()[0])
generative_art_template_path = os.path.join(sv_path, 'node_scripts', 'GenerativeArt_templates')
template_categories = ['examples']

class GENERATIVEART_EXCEPTION(Exception): pass

menu_file_part = 0
menu_file_index = 0
dict_file_name_to_index = dict()

def display_file_name(file_path):
    global menu_file_part
    global menu_file_index
    menu_file_index+=1
    dict_file_name_to_index[file_path] = f'{menu_file_part}.{menu_file_index}.'
    dfn = bpy.path.display_name(file_path)
    dfn = f'{menu_file_part}.{menu_file_index}. {dfn}'
    return dfn

class SV_MT_GenerativeArtMenu(bpy.types.Menu):
    '''Selection menu to load generative art templates'''
    bl_label = "Generative Art templates"
    bl_idname = "SV_MT_GenerativeArtMenu"

    def draw(self, context):
        global menu_file_part
        global menu_file_index
        global dict_file_name_to_index
        
        node = None
        if hasattr(context, "node"):
            node = context.node
        if not node and context.active_node:
            node = context.active_node

        if node:
            args = dict(operator=SvGenerativeArtTextImport.bl_idname, display_name=display_file_name,)

            menu_file_part=0
            dict_file_name_to_index = dict()
            for I, folder in enumerate(template_categories):
                menu_file_part+=1
                menu_file_index = 0
                final_path = os.path.join(generative_art_template_path, folder)
                self.layout.label(text=f"{menu_file_part}. {folder}")
                self.path_menu(searchpaths=[final_path], **args)
                self.layout.row().separator()

        pass

class SvGenerativeArtCallBack(bpy.types.Operator):
    '''Reload xml file and update node'''
    bl_idname = "node.generative_art_callback"
    bl_label = "Generative Art callback"
    bl_options = {'INTERNAL'}
    fn_name: StringProperty(default='')

    def execute(self, context):
        getattr(context.node, self.fn_name)()
        context.node.rseed = context.node.rseed
        return {'FINISHED'}


class SvGenerativeArtCustomCallBack(bpy.types.Operator):

    bl_idname = "node.generative_art_custom_callback"
    bl_label = "custom Generative Art callback"
    bl_options = {'INTERNAL'}
    cb_name: StringProperty(default='')

    def execute(self, context):
        context.node.custom_callback(context, self)
        return {'FINISHED'}

class SvGenerativeArtTextImport(bpy.types.Operator):

    bl_idname = "node.generative_art_import"
    bl_label = "Generative Art load"
    filepath: StringProperty()

    def execute(self, context):
        global dict_file_name_to_index
        message = "Error set node script. Try select node 'Script Light'. If this is helpless then write issue."
        def draw(self, context):
            self.layout.label(text=message)

        txt = bpy.data.texts.load(self.filepath)
        # get active node.
        node = None
        if hasattr(context, "node")==True and context.node is not None:
            # blender 3.6.x
            node = context.node
        elif hasattr(context, "active_node")==True and context.active_node is not None:
            # Blender 4.x
            node = context.active_node

        if node is not None:
            if txt.filepath in dict_file_name_to_index:
                node.menu_index = dict_file_name_to_index[txt.filepath]+' '
            else:
                node.menu_index = ''
            node.file_name = os.path.basename(txt.name)
            node.process()
        else:
            bpy.context.window_manager.popup_menu(draw, title="Error", icon="INFO")
            pass
        return {'FINISHED'}

loop = dict()
script_lookup = dict()

def gather_items(context):

    sv_dir = os.path.dirname(sverchok.__file__) 
    script_dir = os.path.join(sv_dir, "node_scripts","SNLite_templates")
    
    values = []
    idx = 0
    for category in os.scandir(script_dir):
        if category.is_dir():
            for script in os.scandir(category.path):
                if script.is_file():
                    script_lookup[str(idx)] = script.path
                    values.append((str(idx), f"{script.name} | {category.name}", ''))
                    idx += 1
    return values

def item_cb(self, context):
    return loop.get('results') or [("A","A", '', 0),]

class SvGenerativeArtSearch(bpy.types.Operator, SvGenericNodeLocator):
    """ SNLite Search Script Library """
    bl_idname = "node.sv_generative_art_search"
    bl_label = "Generative Art Search"
    bl_property = "my_enum"

    my_enum: bpy.props.EnumProperty(items=item_cb)

    @classmethod
    def poll(cls, context):
        tree_type = getattr(context.space_data, 'tree_type', None)
        if tree_type in {'SverchCustomTreeType', }:
            return True

    def sv_execute(self, context, node):
        if self.my_enum.isnumeric():
            print(script_lookup[self.my_enum])
            file_name = os.path.basename(script_lookup[self.my_enum])
            text_block = bpy.data.texts.new(file_name)
            with open(script_lookup[self.my_enum]) as f:
                text_block.from_string(f.read())
            node.file_name = text_block.name
            node.process()

        return {'FINISHED'}

    def invoke(self, context, event):
        # context.space_data.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        
        if not loop.get('results'):
            loop['results'] = gather_items(context)
        
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


@dataclass
class LSystemLevel:
    rule: object
    depth: int
    matrix: mu.Matrix
    matrix_prev: mu.Matrix

"""
---------------------------------------------------
    LSystem
---------------------------------------------------
"""
class LSystem:

    """
    Takes an XML tree.
    """
    def __init__(self, xml_tree, maxObjects):
        self._tree = xml_tree
        self.global_max_depth = int(self._tree.get("max_depth"))
        self._progressCount = 0
        self._maxObjects = maxObjects

    """
    Returns a list of "shapes".
    Each shape is a 2-tuple: (shape name, transform matrix).
    """
    def evaluate(self, seed=0):
        random.seed(seed)
        rule = _pickRule(self._tree, "entry")
        entry = LSystemLevel(rule=rule, depth=0, matrix=mu.Matrix.Identity(4), matrix_prev=mu.Matrix.Identity(4))
        shapes = self._evaluate(entry)
        return shapes

    def _evaluate(self, entry):
        stack = [entry]
        shapes = []
        nobjects = 0
        while len(stack) > 0:
            if nobjects > self._maxObjects:
                print('max objects reached')
                break

            level = stack.pop()
            
            rule_name = level.rule.get('name')
            local_max_depth = self.global_max_depth-len(stack)
            if "max_depth" in level.rule.attrib:
                local_max_depth = int(level.rule.get("max_depth"))
                if local_max_depth<=0:
                    continue
                pass

            if len(stack) > self.global_max_depth:
                shapes.append(None)
                continue

            # if len(shapes) > self.global_max_depth:
            #     shapes.append(None)
            #     continue

            if level.depth > local_max_depth:
                if "successor" in level.rule.attrib:
                    successor = level.rule.get("successor")
                    sub_rule = _pickRule(self._tree, successor)
                    sub_rule_name   = sub_rule.get('name')
                    sub_rule_depth = 0
                    if (sub_rule_name==rule_name):
                        sub_rule_depth = level.depth+1
                    else:
                        if ("max_depth" in sub_rule.attrib):
                            sub_rule_depth = 0
                        else:
                            sub_rule_depth = level.depth+1
                        pass
                    stack.append(LSystemLevel(rule=sub_rule, depth=sub_rule_depth, matrix=level.matrix_prev.copy(), matrix_prev=level.matrix_prev.copy()))
                shapes.append(None)
                continue

            base_matrix = level.matrix.copy()
            for statement in level.rule:
                tstr = statement.get("transforms", "")
                if not(tstr):
                    tstr = ''
                    for t in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz',
                              'sa', 'sx', 'sy', 'sz']:
                        tvalue = statement.get(t)
                        if tvalue:
                            n = eval(tvalue)
                            tstr += "{} {:f} ".format(t, n)
                        pass
                    pass
                xform = _parseXform(tstr)
                count = int(statement.get("count", 1))
                count_xform = mu.Matrix.Identity(4)
                if count >= 1:
                    matrix_prev = base_matrix
                    for n in range(count):
                        count_xform @= xform
                        matrix = base_matrix @ count_xform

                        if statement.tag == "call":
                            sub_rule = _pickRule(self._tree, statement.get("rule"))
                            cloned_matrix = matrix.copy()
                            sub_rule_name   = sub_rule.get('name')
                            sub_rule_depth = 0
                            if (sub_rule_name==rule_name):
                                sub_rule_depth = level.depth+1
                            elif (sub_rule_name!=rule_name):
                                if ("max_depth" in sub_rule.attrib):
                                    sub_rule_depth = 0
                                else:
                                    sub_rule_depth = level.depth+1
                                pass
                            
                            name = statement.get("shape")
                            if name == "None" or name is None:
                                #shapes.append(None)
                                pass
                            else:
                                #shape = (name, matrix @ xform.inverted())
                                shape = (name, cloned_matrix )
                                shapes.append(shape)
                                nobjects += 1

                            entry = LSystemLevel(rule=sub_rule, depth=sub_rule_depth, matrix=cloned_matrix, matrix_prev=matrix_prev.copy())
                            stack.append(entry)

                        elif statement.tag == "instance":
                            name = statement.get("shape")
                            if name == "None" or name is None:
                                shapes.append(None)
                            else:
                                shape = (name, matrix.copy())
                                shapes.append(shape)
                                nobjects += 1

                        else:
                            raise ValueError("bad xml", statement.tag)
                        
                        matrix_prev = base_matrix @ count_xform
                        pass

                    if count > 1:
                        shapes.append(None)
                else:
                    pass

        return shapes
        # end of _evaluate

    def make_tube(self, mats, verts):
        """
        takes a list of vertices and a list of matrices
        the vertices are to be joined in a ring, copied and transformed
        by the 1st matrix and this ring joined to the previous ring.

        The ring doesn't have to be planar.
        outputs lists of vertices, edges and faces
        """

        edges_out = []
        verts_out = []
        faces_out = []
        vID = 0

        if len(mats) > 1:
            nring = len(verts[0])
            # end face
            faces_out.append(list(range(nring)))
            for i, m in enumerate(mats):
                for j, v in enumerate(verts[0]):
                    vout = mu.Matrix(m) @ mu.Vector(v)
                    verts_out.append(vout.to_tuple())
                    vID = j + i*nring
                    # rings
                    if j != 0:
                        edges_out.append([vID, vID - 1])
                    else:
                        edges_out.append([vID, vID + nring-1])
                    # lines
                    if i != 0:
                        edges_out.append([vID, vID - nring])
                        # faces
                        if j != 0:
                            faces_out.append([vID,
                                              vID - nring,
                                              vID - nring - 1,
                                              vID-1])
                        else:
                            faces_out.append([vID,
                                              vID - nring,
                                              vID-1,
                                              vID + nring-1])
            # end face
            # reversing list fixes face normal direction keeps mesh manifold
            f = list(range(vID, vID-nring, -1))
            faces_out.append(f)
        return verts_out, edges_out, faces_out


def _pickRule(tree, name):

    rules = tree.findall("rule")
    elements = []
    for r in rules:
        if r.get("name") == name:
            elements.append(r)

    if len(elements) == 0:
        raise ValueError("bad xml",  "no rules found with name '%s'" % name)

    sum, tuples = 0, []
    for e in elements:
        weight = int(e.get("weight", 1))
        sum = sum + weight
        tuples.append((e, weight))
    n = random.randint(0, sum - 1)
    for (item, weight) in tuples:
        if n < weight:
            break
        n = n - weight
    return item

_xformCache = {}


def _parseXform(xform_string):
    if xform_string in _xformCache:
        return _xformCache[xform_string]

    matrix = mu.Matrix.Identity(4)
    tokens = xform_string.split()
    t = 0
    while t < len(tokens) - 1:
            command, t = tokens[t], t + 1

            # Translation
            if command == 'tx':
                x, t = eval(tokens[t]), t + 1
                matrix @= mu.Matrix.Translation(mu.Vector((x, 0, 0)))
            elif command == 'ty':
                y, t = eval(tokens[t]), t + 1
                matrix @= mu.Matrix.Translation(mu.Vector((0, y, 0)))
            elif command == 'tz':
                z, t = eval(tokens[t]), t + 1
                matrix @= mu.Matrix.Translation(mu.Vector((0, 0, z)))
            elif command == 't':
                x, t = eval(tokens[t]), t + 1
                y, t = eval(tokens[t]), t + 1
                z, t = eval(tokens[t]), t + 1
                matrix @= mu.Matrix.Translation(mu.Vector((x, y, z)))

            # Rotation
            elif command == 'rx':
                theta, t = _radians(eval(tokens[t])), t + 1
                matrix @= mu.Matrix.Rotation(theta, 4, 'X')

            elif command == 'ry':
                theta, t = _radians(eval(tokens[t])), t + 1
                matrix @= mu.Matrix.Rotation(theta, 4, 'Y')
            elif command == 'rz':
                theta, t = _radians(eval(tokens[t])), t + 1
                matrix @= mu.Matrix.Rotation(theta, 4, 'Z')

            # Scale
            elif command == 'sx':
                x, t = eval(tokens[t]), t + 1
                matrix @= mu.Matrix.Scale(x, 4, mu.Vector((1.0, 0.0, 0.0)))
            elif command == 'sy':
                y, t = eval(tokens[t]), t + 1
                matrix @= mu.Matrix.Scale(y, 4, mu.Vector((0.0, 1.0, 0.0)))
            elif command == 'sz':
                z, t = eval(tokens[t]), t + 1
                matrix @= mu.Matrix.Scale(z, 4, mu.Vector((0.0, 0.0, 1.0)))
            elif command == 'sa':
                v, t = eval(tokens[t]), t + 1
                matrix @= mu.Matrix.Scale(v, 4)
            elif command == 's':
                x, t = eval(tokens[t]), t + 1
                y, t = eval(tokens[t]), t + 1
                z, t = eval(tokens[t]), t + 1
                mx = mu.Matrix.Scale(x, 4, mu.Vector((1.0, 0.0, 0.0)))
                my = mu.Matrix.Scale(y, 4, mu.Vector((0.0, 1.0, 0.0)))
                mz = mu.Matrix.Scale(z, 4, mu.Vector((0.0, 0.0, 1.0)))
                mxyz = mx@my@mz
                matrix @= mxyz

            else:
                err_str = "unrecognized transform: '%s' at position %d in '%s'" % (command, t, xform_string)
                raise ValueError("bad xml", err_str)

    _xformCache[xform_string] = matrix
    return matrix


def _radians(d):
    return float(d * 3.141 / 180.0)


loop = dict()
script_lookup = dict()

def gather_items(context):

    sv_dir = os.path.dirname(sverchok.__file__) 
    script_dir = os.path.join(sv_dir, "node_scripts","GenerativeArt_templates")
    
    values = []
    idx = 0
    for category in os.scandir(script_dir):
        if category.is_dir():
            for script in os.scandir(category.path):
                if script.is_file():
                    script_lookup[str(idx)] = script.path
                    values.append((str(idx), f"{script.name} | {category.name}", ''))
                    idx += 1
    return values

def item_cb(self, context):
    return loop.get('results') or [("A","A", '', 0),]

"""
---------------------------------------------------
    SvGenerativeArtNode
---------------------------------------------------
"""
class SvGenerativeArtNode(SverchCustomTreeNode, bpy.types.Node):
    ''' Generative Art or LSystem node'''
    bl_idname = 'SvGenerativeArtNode'
    bl_label = 'Generative Art'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_GENERATIVE_ART'

    
    def init_sockets(self, value):
        if value and (value in bpy.data.texts or self.xml_str):
            try:
                internal_file = bpy.data.texts[value].as_string() if value in bpy.data.texts else self.xml_str
                xml_str = internal_file
                xml_tree = fromstring(xml_str)
                
                d_constants = {}

                for elem in xml_tree.findall("constants"):
                    d_constants.update(elem.attrib)

                field_ids = [v[1] for v in string.Formatter().parse(xml_str)]
                field_ids = set(field_ids) - set([None])
                constant_ids = set(d_constants.keys())
                socket_ids = field_ids - constant_ids

                # add new input sockets to node
                for s_name in sorted(socket_ids):
                    if s_name not in self.inputs:
                        self.inputs.new('SvStringsSocket', s_name)

                # remove any sockets with no field_ids in xml
                old_sockets = [socket
                            for socket in self.inputs[1:]
                            if socket.name not in socket_ids]
                for socket in old_sockets:
                    self.inputs.remove(socket)

                # output sockets to match shape attribute values
                shape_names = set([x.attrib.get('shape') for x in xml_tree.iter('instance')]) | set([elem for elem in set([x.attrib.get('shape') for x in xml_tree.iter('call')]) if elem])
                if None in shape_names:
                    self.is_xml_valid = True
                    self.is_xml_error_text = "Some 'instance' tags in xml file are missing 'shape' attribute. Please fix xml file and try again."
                    raise Exception(self.is_xml_error_text)
                # new output sockets
                for s_name in sorted(shape_names):
                    if s_name not in self.outputs:
                        self.outputs.new('SvMatrixSocket', s_name)

                # remove old output sockets
                old_sockets = [out_socket
                            for out_socket in self.outputs[3:]
                            if out_socket.name not in shape_names]
                for socket in old_sockets:
                    self.outputs.remove(socket)

                self.xml_str = xml_str
                self.is_xml_error_text = ''
            except Exception as _ex:
                self.xml_str = ""
                self.is_xml_valid = False
                self.is_xml_error_text = str(_ex)
                raise Exception(_ex)
                pass
            pass
        else:
            # No value - clear sockets
            old_sockets = [out_socket for out_socket in self.outputs[3:] ]
            for socket in old_sockets:
                self.outputs.remove(socket)
            self.is_xml_error_text = ""
            self.xml_str = ""
            pass
        return
    
    def get_file_name(self):
        return self.filename

    def set_file_name(self, value):
        self.is_xml_valid = True
        self.filename = value
        self.init_sockets(value)
        return

    filename: StringProperty(
        default="",
    )
    file_name: StringProperty(
        name="File Name",
        description="File name of xml file to use for generative art. File must be in bpy.data.texts. You can use search menu to load xml file to bpy.data.texts and set file name at the same time.",
        default="",
        get=get_file_name,
        set=set_file_name,
    ) # update=updateNode_filename)

    menu_index: StringProperty()
    xml_str: StringProperty(default="")

    is_xml_valid: BoolProperty(
        default=False,
        options={'SKIP_SAVE'},
    )

    is_xml_error_text: StringProperty(
        default="",
        options={'SKIP_SAVE'},
    )

    rseed: IntProperty(
        name='Random Seed',
        description='random seed',
        default=21,
        min=0,
        options={'ANIMATABLE'},
        update=updateNode,
    )

    maxmats: IntProperty(
        name='max mats', description='maximum number of matrices',
        default=1000, min=1, options={'ANIMATABLE'},
        update=updateNode)

    def draw_label(self):
        if self.xml_str:
            return f"{SvGenerativeArtNode.bl_label}: {self.menu_index}{self.file_name}"
        else:
            return self.bl_label
        
    def draw_buttons(self, context, layout):
        sn_callback = SvGenerativeArtCallBack.bl_idname
        sn_custom_callback = SvGenerativeArtCustomCallBack.bl_idname

        elem = layout.box()
        row = elem.row()
        if self.xml_str:
            #row.enabled = False
            pass
        row.prop_search(self, 'file_name', bpy.data, 'texts', text='', icon='TEXT')
        if self.is_xml_valid==False:
            col = row.column(align=True)
            col.alert = True
            col.label(text='', icon='ERROR')
        row.operator(sn_callback, text='', icon='PLUGIN').fn_name = 'load'
        self.wrapper_tracked_ui_draw_op(row, SvGenerativeArtSearch.bl_idname, text="", icon="VIEWZOOM")
        menu = elem.menu(SV_MT_GenerativeArtMenu.bl_idname)
        
        col = elem.column()
        col.use_property_decorate = False
        col.use_property_split = True
        col.prop(self, "rseed",)
        col.prop(self, "maxmats",)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvMatrixSocket', "Matrices")
        return

    def nuke_me(self):
        self.xml_str = ''
        self.file_name = ''
        for socket_set in [self.inputs[1:], ]:
            socket_set.clear()
        return

    def load(self):
        if not self.file_name:
            return
        self.file_name = self.file_name
        return

    def xml_text_format(self, xml_str):
        """substitute constants from xml and variables from socket inputs"""
        xml_tree = None
        if xml_str:
            # get constants from xml
            format_dict = {}

            xml_tree = fromstring(xml_str)

            for elem in xml_tree.findall("constants"):
                format_dict.update(elem.attrib)

            # add input socket values to constants dict
            for socket in self.inputs[1:]:
                format_dict[socket.name] = socket.sv_get()[0][0] if socket.is_linked else 0 # here is default value for socket if socket is not connected.

            while '{' in xml_str:
                # using while loop
                # allows constants to be defined using other constants
                xml_str = xml_str.format(**format_dict)
            xml_tree = fromstring(xml_str)
        else:
            pass

        return xml_tree

    def process(self):

        if not any(output.is_linked for output in self.outputs):
            return

        if self.xml_str:
            xml_tree = self.xml_text_format(self.xml_str)
            if xml_tree:

                lsys = LSystem(xml_tree, self.maxmats)
                shapes = lsys.evaluate(seed=self.rseed)
                mat_sublist = []

                edges_out = []
                verts_out = []
                faces_out = []

                # make last entry in shapes None
                # to allow make tube to finish last tube
                if shapes[-1]:
                    shapes.append(None)
                # dictionary for matrix lists
                shape_names = set([x.attrib.get('shape') for x in xml_tree.iter('instance')]) | set([elem for elem in set([x.attrib.get('shape') for x in xml_tree.iter('call')]) if elem])
                mat_dict = {s: [] for s in shape_names}
                if self.inputs['Vertices'].is_linked:
                    verts = Vector_generate(self.inputs['Vertices'].sv_get())
                for i, shape in enumerate(shapes):
                    if shape:
                        mat_sublist.append(shape[1])
                        mat_dict[shape[0]].append(shape[1])
                    else:
                        if len(mat_sublist) > 0:
                            if self.inputs['Vertices'].is_linked:
                                v, e, f = lsys.make_tube(mat_sublist, verts)
                                if v:
                                    verts_out.append(v)
                                    edges_out.append(e)
                                    faces_out.append(f)

                        mat_sublist = []
                    pass

                if self.file_name not in bpy.data.texts:
                    # export to data.tests. This can be happens after import Sverchok Schema from .json-file.
                    text_block = bpy.data.texts.new(self.file_name)
                    text_block.from_string(self.xml_str)

                self.is_xml_valid = True
                self.is_xml_error_text = ''

                self.outputs['Vertices'].sv_set(verts_out)
                self.outputs['Edges'].sv_set(edges_out)
                self.outputs['Faces'].sv_set(faces_out)
                for shape in shape_names:  # isn't it plain wrong? i mean why not just shape_names[-1] if need to get last one?
                    self.outputs[shape].sv_set(mat_dict[shape])
            else:
                pass
        else:
            pass

        return

classes = [
    SV_MT_GenerativeArtMenu,
    SvGenerativeArtTextImport,
    SvGenerativeArtSearch,
    SvGenerativeArtCallBack,
    SvGenerativeArtNode,
]

register, unregister = bpy.utils.register_classes_factory(classes)
