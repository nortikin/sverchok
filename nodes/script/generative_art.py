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
from enum import Enum

import math
import string
import random
from xml.etree.cElementTree import ParseError, fromstring
from dataclasses import dataclass

import bpy
from bpy.props import IntProperty, StringProperty, BoolProperty
import mathutils as mu
import sverchok
from sverchok.utils.sv_update_utils import sv_get_local_path
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, Vector_generate

sv_path = os.path.dirname(sv_get_local_path()[0])
generative_art_template_path = os.path.join(sv_path, 'node_scripts', 'GenerativeArt_templates')
template_categories = ['examples']

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

class SV_MT_GenerativeArtMenuMK2(bpy.types.Menu):
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
            args = dict(operator=SvGenerativeArtTextImportMK2.bl_idname, display_name=display_file_name,)

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

class SvGenerativeArtCallBackMK2(bpy.types.Operator):
    '''Reload xml file and update node'''
    bl_idname = "node.generative_art_callback"
    bl_label = "Generative Art callback"
    bl_options = {'INTERNAL'}
    fn_name: StringProperty(default='')

    def execute(self, context):
        getattr(context.node, self.fn_name)()
        context.node.rseed = context.node.rseed
        return {'FINISHED'}


class SvGenerativeArtCustomCallBackMK2(bpy.types.Operator):

    bl_idname = "node.generative_art_custom_callback"
    bl_label = "custom Generative Art callback"
    bl_options = {'INTERNAL'}
    cb_name: StringProperty(default='')

    def execute(self, context):
        context.node.custom_callback(context, self)
        return {'FINISHED'}

class SvGenerativeArtTextImportMK2(bpy.types.Operator):

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

class SvGenerativeArtSearchMK2(bpy.types.Operator, SvGenericNodeLocator):
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
    rule: object            # rule params
    depth: int              # current_depth
    global_depth: int       # global depth current level is at in the tree structure
    matrix: mu.Matrix
    matrix_prev: mu.Matrix

class LSystemFrameType(Enum):
    CALL = 'call'
    INSTANCE = 'instance'

@dataclass
class LSystemFrame:
    type: LSystemFrameType # 'call' or 'instance'
    obj : object           # params of calls or instances

class LSystemShapeType(Enum):
    START = 'start'
    BODY = 'body'
    TAIL = 'tail'


@dataclass
class LSystemShape:
    type: LSystemShapeType      # 'start', 'body' or 'tail'
    name: string                # shape name
    matrix: mu.Matrix    # transform matrix for shape

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
        self.global_max_depth = int(self._tree.get("max_depth", 1000))
        self._progressCount = 0
        self.global_max_objects = maxObjects

    """
    Returns a list of "shapes".
    Each shape is a 2-tuple: (shape name, transform matrix).
    """
    def evaluate(self, seed=0):
        random.seed(seed)
        rule = _pickRule(self._tree, "entry")
        entry = LSystemLevel(rule=rule, depth=0, global_depth=0, matrix=mu.Matrix.Identity(4), matrix_prev=mu.Matrix.Identity(4))
        shapes = self._evaluate(entry)
        return shapes

    def _evaluate(self, entry):
        stack = [LSystemFrame(type=LSystemFrameType.CALL, obj=entry)]
        shapes = []
        nobjects = 0
        while len(stack) > 0:
            if nobjects >= self.global_max_objects:
                print( f'max objects reached {nobjects}>={self.global_max_objects}')
                break

            stack_frame = stack.pop()

            if stack_frame.type == LSystemFrameType.INSTANCE:
                shape = stack_frame.obj
                # do not add None shapes to list if previous shape is also None, to avoid long lists of Nones.
                if shapes and shapes[-1] is None and shape is None:
                    continue
                shapes.append(shape)
                # In the future it will be more convenient to allow the user to include or exclude TAIL matrices
                # in the resulting matrices if the user wants to perform extrude on these matrices.
                if shape is not None and shape.type!=LSystemShapeType.TAIL:
                    nobjects += 1
                continue
            elif stack_frame.type == LSystemFrameType.CALL:

                level = stack_frame.obj
                
                rule_name = level.rule.get('name')
                # some magic to calculate local max depth based on number of calls in stack.
                # The depth of the stack is not equal to the number of elements in the stack, as there are also
                # levels in the stack that are not taken into account because they do not increase the depth of the recursion.
                set_of_call = set([frame.obj.global_depth for frame in stack if frame.type==LSystemFrameType.CALL])
                # The remaining set can specify depths that have already been reached at the current level of recursion,
                # but they should not be included in calculating the depth for the current level because they do not
                # increase the recursion depth. Therefore, we remove them from the set. Example:
                #     <rule name="spiral" weight="20">
                #        <call transforms="rx 15" rule="spiral"/>  # level 93 /1
                #        <call transforms="rz 180" rule="spiral"/> # level 93 /2 (!!! levels are the same)
                #    </rule>
                # and stack has frames: {34, 71, 73, 45, 23, 93}, then /1 and /2 are at the same level of recursion,
                # so we remove one of them from the set and calculate depth based on the remaining unique levels in the stack.
                set_of_call.discard(level.global_depth)
                stack_depth = len(set_of_call)
                local_max_depth = self.global_max_depth-stack_depth
                if "max_depth" in level.rule.attrib:
                    local_max_depth = int(level.rule.get("max_depth"))
                    if local_max_depth<=0:
                        continue
                    pass

                if stack_depth > self.global_max_depth:
                    shapes.append(None)
                    continue

                # if len(shapes) > self.global_max_depth:
                #     shapes.append(None)
                #     continue

                if level.global_depth > self.global_max_depth:
                    if shapes and shapes[-1] is not None:
                        shapes.append(None)
                    print(f'max recursion depth reached: {self.global_max_depth}')
                    continue

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
                        sub_rule_depth = level.depth+1
                        stack.append( LSystemFrame(type=LSystemFrameType.CALL, obj=LSystemLevel(rule=sub_rule, depth=sub_rule_depth, global_depth=level.global_depth+1, matrix=level.matrix_prev.copy(), matrix_prev=level.matrix_prev.copy())))
                    stack.append(LSystemFrame(type=LSystemFrameType.INSTANCE, obj=None))
                    continue

                base_matrix = level.matrix.copy()
                _local_stack = []
                last_instance_matrix = None
                last_instance_shape_name = None
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

                                # If a branch occurs in the next step, then stop the current branch from developing. The branches themselves must remain stems and not be divided.
                                # Branching is when there are multiple calls to other rules within a rule (>1 call).
                                if len([s for s in sub_rule if s.tag=='call'])>1:
                                    if last_instance_matrix:
                                        # an instance with no name means cancel using the shape for the next call.
                                        # Otherwise there will be an attempt to attach the same shape to the next call.
                                        if last_instance_shape_name and last_instance_shape_name.lower() != "none":
                                            shape = LSystemShape(type=LSystemShapeType.TAIL, name=last_instance_shape_name, matrix=cloned_matrix @ last_instance_matrix)
                                            _local_stack.append(LSystemFrame(type=LSystemFrameType.INSTANCE, obj=shape))
                                        _local_stack.append(LSystemFrame(type=LSystemFrameType.INSTANCE, obj=None))
                                
                                entry = LSystemLevel(rule=sub_rule, depth=sub_rule_depth, global_depth=level.global_depth+1, matrix=cloned_matrix, matrix_prev=matrix_prev.copy())
                                _local_stack.append(LSystemFrame(type=LSystemFrameType.CALL, obj=entry))

                            elif statement.tag == "instance":
                                last_instance_shape_name = statement.get("shape")
                                if last_instance_shape_name is None or last_instance_shape_name.lower()=="none":
                                    last_instance_shape_name = None
                                    _local_stack.append(LSystemFrame(type=LSystemFrameType.INSTANCE, obj=None))
                                else:
                                    #shape = (name, matrix.copy())
                                    shape = LSystemShape(type=LSystemShapeType.BODY, name=last_instance_shape_name, matrix=matrix.copy() )
                                    last_instance_matrix = xform.copy()
                                    _local_stack.append(LSystemFrame(type=LSystemFrameType.INSTANCE, obj=shape))

                            else:
                                raise ValueError("bad xml", statement.tag)
                            
                            matrix_prev = base_matrix @ count_xform
                            pass

                        if count > 1:
                            _local_stack.append(LSystemFrame(type=LSystemFrameType.INSTANCE, obj=None))
                    else:
                        pass
                    pass # for statement in level.rule
                stack.extend(_local_stack[::-1]) # Before saving local elements to the main stack, reverse the local list to preserve the execution order of instructions inside the rule.
            else:
                raise ValueError("bad stack frame type", stack_frame.type)

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

        if len(mats) >= 1:
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

class SvGenerativeArtNodeAlertOperatorMK2(bpy.types.Operator):
    '''Show alert sign'''
    bl_idname = "node.sv_generative_art_node_alert_operator_mk2"
    bl_label = "Generative Art Node Alert"
    description_text: bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, property):
        s = property.description_text
        return s

    def invoke(self, context, event):
        return {'FINISHED'}

"""
---------------------------------------------------
    SvGenerativeArtNode
---------------------------------------------------
"""
class SvGenerativeArtNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    ''' Generative Art or LSystem node'''
    bl_idname = 'SvGenerativeArtNodeMK2'
    bl_label = 'Generative Art'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_GENERATIVE_ART'

    
    def init_sockets(self, value):
        if value and (value in bpy.data.texts or self.xml_str):
            xml_str = "undefined"
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
                # TODO this operation execute in process. It would be better to do it once when loading XML and store the result, rather than repeating it on every process.
                shape_names.discard(None)
                shape_names.discard("none")
                # if None in shape_names:
                #     self.is_xml_valid = True
                #     self.is_xml_error_text = "Some 'instance' tags in xml file are missing 'shape' attribute. Please fix xml file and try again."
                #     raise Exception(self.is_xml_error_text)
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
            except ParseError as _ex:
                self.xml_str = ""
                self.is_xml_valid = False
                try:
                    text = "\n".join([str(s[0:30]).replace("\n", "") for s in xml_str.split("\n") if s][0:20][0:3])
                except:
                    text = ""
                self.is_xml_error_text = "Exception in xml:\n\n"+text+"\n\n"+str(_ex)
                raise Exception(_ex)
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
        update=updateNode,
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
            return f"{SvGenerativeArtNodeMK2.bl_label}: {self.menu_index}{self.file_name}"
        else:
            return self.bl_label
        
    def draw_buttons(self, context, layout):
        sn_callback = SvGenerativeArtCallBackMK2.bl_idname
        sn_custom_callback = SvGenerativeArtCustomCallBackMK2.bl_idname

        elem = layout.box()
        row = elem.row()
        if self.xml_str:
            #row.enabled = False
            pass
        row.prop_search(self, 'file_name', bpy.data, 'texts', text='', icon='TEXT')
        if self.is_xml_valid==False:
            col = row.column(align=True)
            col.alert = True
            #col.label(text='', icon='ERROR')
            col.operator(SvGenerativeArtNodeAlertOperatorMK2.bl_idname, text='', icon='ERROR').description_text = self.is_xml_error_text
        row.operator(sn_callback, text='', icon='PLUGIN').fn_name = 'load'
        self.wrapper_tracked_ui_draw_op(row, SvGenerativeArtSearchMK2.bl_idname, text="", icon="VIEWZOOM")
        menu = elem.menu(SV_MT_GenerativeArtMenuMK2.bl_idname)
        
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
                for I, x in enumerate(xml_tree.iter('rule')):
                    x.set("id", str(I))

                lsys = LSystem(xml_tree, self.maxmats)
                shapes = lsys.evaluate(seed=self.rseed)

                # lsys1 = LSystemYeld(xml_tree, self.maxmats)
                # shapes1 = lsys1.evaluate(seed=self.rseed)
                # shapes = shapes1


                
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
                # TODO this operation was done during XML analysis. It would be better to do it once when loading XML and store the result, rather than repeating it on every process.
                shape_names.discard(None)
                shape_names.discard("none")

                mat_dict = {s: [] for s in shape_names}
                mat_out  = {s: [] for s in shape_names}
                if self.inputs['Vertices'].is_linked:
                    verts = Vector_generate(self.inputs['Vertices'].sv_get())
                for i, shape in enumerate(shapes):
                    if shape:
                        mat_sublist.append(shape.matrix)
                        mat_dict[shape.name].append(shape.matrix)
                        if shape.type!=LSystemShapeType.TAIL:
                            mat_out[shape.name].append(shape.matrix)
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
                    self.outputs[shape].sv_set(mat_out[shape])
            else:
                pass
        else:
            pass

        return

classes = [
    SvGenerativeArtNodeAlertOperatorMK2,
    SV_MT_GenerativeArtMenuMK2,
    SvGenerativeArtTextImportMK2,
    SvGenerativeArtSearchMK2,
    SvGenerativeArtCallBackMK2,
    SvGenerativeArtNodeMK2,
]

register, unregister = bpy.utils.register_classes_factory(classes)
