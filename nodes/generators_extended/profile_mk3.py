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

import os

import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import BoolProperty, StringProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.core.socket_data import SvNoDataError
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.logging import info, debug, warning
from sverchok.utils.sv_update_utils import sv_get_local_path

from sverchok.utils.modules.profile_mk3.interpreter import Interpreter
from sverchok.utils.modules.profile_mk3.parser import parse_profile

'''
input like:

    default name = <value>
    let name = <value>

    M|m <2v coordinate>
    L|l <2v coordinate 1> <2v coordinate 2> <2v coordinate n> ["n = " num_segments] [z]
    C|c (<2v control1> <2v control2> <2v knot2>)+ ["n = " num_segments] [z]
    S|s (<2v control2> <2v knot2>)+ ["n = " num_segments] [z]
    Q|q (<2v control> <2v knot2>)+ ["n = " num_segments] [z]
    T|t (<2v knot2>)+ ["n = " num_segments] [z]
    A|a <2v rx,ry> <float rot> <int flag1> <int flag2> <2v x,y> ["n = " num_verts] [z]
    H|h <x1> <x2> ... ["n = " num_segments] ;
    V|v <y1> <y2> ... ["n = " num_segments] ;
    X
    #
    -----
    <>  : mandatory field
    []  : optional field
    (...)+ : something may appear several times
    2v  : two point vector `a,b`
            - no backticks
            - a and b can be number literals or lowercase 1-character symbols for variables
    <int .. >
        : means the value will be cast as an int even if you input float
        : flags generally are 0 or 1.
    z   : is optional for closing a line
    X   : as a final command to close the edges (cyclic) [-1, 0]
        in addition, if the first and last vertex share coordinate space
        the last vertex is dropped and the cycle is made anyway.
    #   : single line comment prefix

    Each integer or floating value may be represented as
    
    * Integer or floating literal (usual python syntax, such as 5 or 7.5)
    * Variable name, such as a or b or variable_name
    * Negation sign and a variable name, such as `-a` or `-size`.
    * Expression enclosed in curly brackets, such as {a+1} or {sin(phi)}

    "default" statement declares a default value for variable: this value will be used
    if corresponding input of the node is not connected.

    "let" statement declares a "name binding"; it may be used to calculate some value once
    and use it in the following definitions several times. Variable defined by "let" will
    not appear as node input!

    "default" and "let" definitions may use previously defined variables, or variables
    expected to be provided as inputs. Just note that these statements are evaluated in
    the same order as they follow in the input profile text.
    
    Statements may optionally be separated by semicolons (;).
    For some commands (namely: H/h, V/v) the trailing semicolon is *required*!

'''

"""
Our DSL has relatively simple BNF:

    <Profile> ::= <Statement> *
    <Statement> ::= <Default> | <Assign>
                    | <MoveTo> | <LineTo> | <CurveTo> | <SmoothLineTo>
                    | <QuadCurveTo> | <SmoothQuadCurveTo>
                    | <ArcTo> | <HorLineTo> | <VertLineTo> | "X"

    <Default> ::= "default" <Variable> "=" <Value>
    <Assign> ::= "let" <Variable> "=" <Value>

    <MoveTo> ::= ("M" | "m") <Value> "," <Value>
    <LineTo> ::= ...
    <CurveTo> ::= ...
    <SmoothCurveTo> ::= ...
    <QuadCurveTo> ::= ...
    <SmoothQuadCurveTo> ::= ...
    <ArcTo> ::= ...
    <HorLineTo> ::= ("H" | "h") <Value> * ";"
    <VertLineTo> ::= ("V" | "v") <Value> * ";"

    <Value> ::= "{" <Expression> "}" | <Variable> | <NegatedVariable> | <Const>
    <Expression> ::= Standard Python expression
    <Variable> ::= Python variable identifier
    <NegatedVariable> ::= "-" <Variable>
    <Const> ::= Python integer or floating-point literal

"""

#################################
# "From Selection" Operator
#################################

# Basically copy-pasted from mk2
# To understand how it works will take weeks :/

class SvPrifilizerMk3(bpy.types.Operator):
    """SvPrifilizer"""
    bl_idname = "node.sverchok_profilizer_mk3"
    bl_label = "SvPrifilizer"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    knotselected : BoolProperty(description='if selected knots than use extended parsing in PN', default=False)
    x : BoolProperty(default=True)
    y : BoolProperty(default=True)


    def stringadd(self, x,selected=False):
        precision = bpy.data.node_groups[self.treename].nodes[self.nodename].precision
        if selected:
            if self.x: letterx = '+a'
            else: letterx = ''
            if self.y: lettery = '+a'
            else: lettery = ''
            a = f'{{{round(x[0], precision)}{letterx}}},{{{round(x[1], precision)}{lettery}}} '
            self.knotselected = True
        else:
            a = f"{round(x[0], precision)},{round(x[1], precision)} "
        return a
    
    def curve_points_count(self):
        count = bpy.data.node_groups[self.treename].nodes[self.nodename].curve_points_count
        return str(count)

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        precision = node.precision
        subdivisions = node.curve_points_count
        if not bpy.context.selected_objects:
            warning('Pofiler: Select curve!')
            self.report({'INFO'}, 'Select CURVE first')
            return {'CANCELLED'}
        if not bpy.context.selected_objects[0].type == 'CURVE':
            warning('Pofiler: NOT a curve selected')
            self.report({'INFO'}, 'It is not a curve selected for profiler')
            return {'CANCELLED'}

        objs = bpy.context.selected_objects
        names = str([o.name for o in objs])[1:-2]

        # test for POLY or NURBS curve types, these are not yet supported
        spline_type = objs[0].data.splines[0].type
        if spline_type in {'POLY', 'NURBS'}:
            msg = 'Pofiler: does not support {0} curve type yet'.format(spline_type)
            warning(msg)
            self.report({'INFO'}, msg)
            return {'CANCELLED'}

        # collect paths
        op = []
        clos = []
        for obj in objs:
            for spl in obj.data.splines:
                op.append(spl.bezier_points)
                clos.append(spl.use_cyclic_u)

        # define path to text
        values = '# Here is autogenerated values, \n# Please, rename text to avoid data loose.\n'
        values += '# Objects are: \n# %a' % (names)+'.\n'
        values += '# Object origin should be at 0,0,0. \n'
        values += '# Property panel has precision %a \n# and curve subdivision %s.\n\n' % (precision,subdivisions)
        # also future output for viewer indices
        out_points = []
        out_names = []
        ss = 0
        for ob_points, clo in zip(op,clos):
            values += '# Spline %a\n' % (ss)
            ss += 1
            # handles preperation
            curves_left  = [i.handle_left_type for i in ob_points]
            curves_right = ['v']+[i.handle_right_type for i in ob_points][:-1]
            # first collect C,L values to compile them later per point
            types = ['FREE','ALIGNED','AUTO']
            curves = ['C ' if x in types or c in types else 'L ' for x,c in zip(curves_left,curves_right)]
            # line for if curve was before line or not
            line = False
            curve = False

            for i,c in zip(range(len(ob_points)),curves):
                co = ob_points[i].co
                if not i:
                    # initial value
                    values += '\n'
                    values += 'M '
                    co = ob_points[0].co[:]
                    values += self.stringadd(co,ob_points[0].select_control_point)
                    values += '\n'
                    out_points.append(co)
                    out_names.append(['M.0'])
                    # pass if first 'M' that was used already upper
                    continue

                elif c == 'C ':
                    values += '\n'
                    values += '#C.'+str(i)+'\n'
                    values += c
                    hr = ob_points[i-1].handle_right[:]
                    hl = ob_points[i].handle_left[:]
                    # hr[0]hr[1]hl[0]hl[1]co[0]co[1] 20 0
                    values += self.stringadd(hr,ob_points[i-1].select_right_handle)
                    values += self.stringadd(hl,ob_points[i].select_left_handle)
                    values += self.stringadd(co,ob_points[i].select_control_point)
                    if curve:
                        values += '\n'
                    out_points.append(hr[:])
                    out_points.append(hl[:])
                    out_points.append(co[:])
                    #namecur = ['C.'+str(i)]
                    out_names.extend([['C.'+str(i)+'h1'],['C.'+str(i)+'h2'],['C.'+str(i)+'k']])
                    line = False
                    curve = True

                elif c == 'L ' and not line:
                    if curve:
                        values += '\n'
                    values += '#L.'+str(i)+'...'+'\n'
                    values += c
                    values += self.stringadd(co,ob_points[i].select_control_point)
                    out_points.append(co[:])
                    out_names.append(['L.'+str(i)])
                    line = True
                    curve = False

                elif c == 'L ' and line:
                    values += self.stringadd(co,ob_points[i].select_control_point)
                    out_points.append(co[:])
                    out_names.append(['L.'+str(i)])

            if clo:
                if ob_points[0].handle_left_type in types or ob_points[-1].handle_right_type in types:
                    line = False
                    values += '\n'
                    values += '#C.'+str(i+1)+'\n'
                    values += 'C '
                    hr = ob_points[-1].handle_right[:]
                    hl = ob_points[0].handle_left[:]
                    # hr[0]hr[1]hl[0]hl[1]co[0]co[1] 20 0
                    values += self.stringadd(hr,ob_points[-1].select_right_handle)
                    values += self.stringadd(hl,ob_points[0].select_left_handle)
                    values += self.stringadd(ob_points[0].co,ob_points[0].select_control_point)
                    #values += self.stringadd(len(ob_points))
                    #values += ' 0 '
                    values += '\n'
                    out_points.append(hr[:])
                    out_points.append(hl[:])
                    out_names.extend([['C.'+str(i+1)+'h1'],['C.'+str(i+1)+'h2']])
                    # preserving overlapping
                    #out_points.append(ob_points[0].co[:])
                    #out_names.append(['C'])
                if not line:
                    # hacky way till be fixed x for curves not only for lines
                    values += '# hacky way till be fixed x\n# for curves not only for lines'
                    values += '\nL ' + self.stringadd(ob_points[0].co,ob_points[0].select_control_point)
                    values += '\nx \n\n'
                else:
                    values += '\nx \n\n'

        if self.knotselected:
            values += '# expression (#+a) added because \n# you selected knots in curve'
        self.write_values(self.nodename, values)
        #print(values)
        node.filename = self.nodename
        #print([out_points], [out_names])
        # sharing data to node:
        if node.addnodes:
            self.index_viewer_adding(node)
            self.viewedraw_adding(node)
            if self.knotselected:
                self.float_add_if_selected(node)
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


    def index_viewer_adding(self, node):
        """ adding new viewer index node if none """
        if node.outputs[2].is_linked: return
        loc = node.location

        tree = bpy.context.space_data.edit_tree
        links = tree.links

        vi = tree.nodes.new("SvIDXViewer28")

        vi.location = loc+Vector((200,-100))
        vi.draw_bg = True

        links.new(node.outputs[2], vi.inputs[0])   #knots
        links.new(node.outputs[3], vi.inputs[4])   #names

    def float_add_if_selected(self, node):
        """ adding new float node if selected knots """
        if node.inputs[0].is_linked: return
        loc = node.location

        tree = bpy.context.space_data.edit_tree
        links = tree.links

        nu = tree.nodes.new('SvNumberNode')
        nu.location = loc+Vector((-200,-150))

        links.new(nu.outputs[0], node.inputs[0])   #number

    def viewedraw_adding(self, node):
        """ adding new viewer draw node node if none """
        if node.outputs[0].is_linked: return
        loc = node.location

        tree = bpy.context.space_data.edit_tree
        links = tree.links

        vd = tree.nodes.new("SvVDExperimental")

        vd.location = loc+Vector((200,225))

        links.new(node.outputs[0], vd.inputs[0])   #verts
        links.new(node.outputs[1], vd.inputs[1])   #edges



#################################
# Example Files Import
#################################

sv_path = os.path.dirname(sv_get_local_path()[0])
profile_template_path = os.path.join(sv_path, 'profile_examples')

class SvProfileImportMenu(bpy.types.Menu):
    bl_label = "Profile templates"
    bl_idname = "SV_MT_ProfileImportMenu"

    def draw(self, context):
        if context.active_node:
            node = context.active_node
            self.path_menu([profile_template_path], "node.sv_profile_import_example")

class SvProfileImportOperator(bpy.types.Operator):

    bl_idname = "node.sv_profile_import_example"
    bl_label = "Profile mk3 load"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    filepath : bpy.props.StringProperty()

    def execute(self, context):
        txt = bpy.data.texts.load(self.filepath)
        context.node.filename = os.path.basename(txt.name)
        updateNode(context.node, context)
        return {'FINISHED'}

#################################
# Node class
#################################

class SvProfileNodeMK3(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    '''
    Triggers: svg-like 2d profiles
    Tooltip: Generate multiple parameteric 2d profiles using SVG like syntax

    SvProfileNode generates one or more profiles / elevation segments using;
    assignments, variables, and a string descriptor similar to SVG.

    This node expects simple input, or vectorized input.
    - sockets with no input are automatically 0, not None
    - The longest input array will be used to extend the shorter ones, using last value repeat.
    '''

    bl_idname = 'SvProfileNodeMK3'
    bl_label = 'Profile Parametric Mk3'
    bl_icon = 'SYNTAX_ON'

    axis_options = [("X", "X", "", 0), ("Y", "Y", "", 1), ("Z", "Z", "", 2)]

    selected_axis : EnumProperty(
        items=axis_options, update=updateNode, name="Type of axis",
        description="offers basic axis output vectors X|Y|Z", default="Z")

    def on_update(self, context):
        self.adjust_sockets()
        updateNode(self, context)

    def fp_updateNode(self, context):
        self.filename = self.file_pointer.name if self.file_pointer else ""
        updateNode(self, context)

    properties_to_skip_iojson = ['file_pointer']
    # depreciated, but keep to prevent breakage
    filename : StringProperty(default="")

    file_pointer: PointerProperty(
        name="File", poll=lambda s,o: True, type=bpy.types.Text, update=fp_updateNode)

    x : BoolProperty(default=True)
    y : BoolProperty(default=True)

    precision : IntProperty(
        name="Precision", min=0, max=10, default=8, update=updateNode,
        description="decimal precision of coordinates when generating profile from selection")

    addnodes : BoolProperty(
        name="AddNodes", default=False,
        description="Lets add support nodes at pressing from selection button")

    curve_points_count : IntProperty(
        name="Curve points count", min=1, max=100, default=20, update=updateNode,
        description="Default number of points on curve segment")

    close_threshold : FloatProperty(
        name="X command threshold", min=0, max=1, default=0.0005, precision=6, update=updateNode,
        description="If distance between first and last point is less than this, X command will remove the last point")

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout, icon_only=True)
        layout.prop(self, 'selected_axis', expand=True)
        layout.prop_search(self, 'file_pointer', bpy.data, 'texts', text='', icon='TEXT')

        col = layout.column(align=True)
        row = col.row()
        do_text = row.operator('node.sverchok_profilizer_mk3', text='from selection')
        do_text.nodename = self.name
        do_text.treename = self.id_data.name
        do_text.x = self.x
        do_text.y = self.y

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)

        layout.prop(self, "close_threshold")

        layout.label(text="Profile Generator settings")
        layout.prop(self, "precision")
        layout.prop(self, "curve_points_count")
        row = layout.row(align=True)
        row.prop(self, "x",text='x-affect', expand=True)
        row.prop(self, "y",text='y-affect', expand=True)

        layout.label(text="Import Examples")
        layout.menu(SvProfileImportMenu.bl_idname)
        layout.prop(self, "addnodes",text='Auto add nodes')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "a")

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvVerticesSocket', "Knots")
        self.outputs.new('SvStringsSocket', "KnotNames")

    def load_profile(self):
        if not self.file_pointer or self.filename:
            return None

        if self.file_pointer:
            internal_file = self.file_pointer
        else:
            internal_file = self.get_bpy_data_from_name(self.filename, bpy.data.texts)
            if not internal_file:
                self.error("error in load_profile..fuzzysearch failed to find {self.filename}")
                return None

            # load file from old blend / json
            self.file_pointer = internal_file
        
        f = self.file_pointer.as_string()
        profile = parse_profile(f)
        return profile

    def get_variables(self):
        variables = set()
        profile = self.load_profile()
        if not profile:
            return variables

        for statement in profile:
            vs = statement.get_variables()
            variables.update(vs)

        for statement in profile:
            vs = statement.get_hidden_inputs()
            variables.difference_update(vs)

        return list(sorted(list(variables)))
    
    def get_optional_inputs(self, profile):
        result = set()
        if not profile:
            return result
        for statement in profile:
            vs = statement.get_optional_inputs()
            result.update(vs)
        return result

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

    def sv_update(self):
        '''
        analyze the state of the node and returns if the criteria to start processing are not met.
        '''
        if not self.file_pointer or not self.get_bpy_data_from_name(self.filename, bpy.data.texts):
            return

        self.adjust_sockets()

    def set_pointer_from_filename(self):
        """
        this function is called on post_load handler to upgrade in-place profile mk3
        if there is nothing to upgrade, then it's a no-op.

        """
        if self.filename and hasattr(self, "file_pointer") and not self.file_pointer:
            text_datablock = self.get_bpy_data_from_name(self.filename, bpy.data.texts)
            if text_datablock:
                print(f"upgrading profile node mk3 {self.name}")
                with self.sv_throttle_tree_update():
                    self.file_pointer = text_datablock

    def get_input(self):
        variables = self.get_variables()
        result = {}

        for var in variables:
            if var in self.inputs and self.inputs[var].is_linked:
                result[var] = self.inputs[var].sv_get()[0]
        return result
    
    def extend_out_verts(self, verts):
        if self.selected_axis == 'X':
            extend = lambda v: (0, v[0], v[1])
        elif self.selected_axis == 'Y':
            extend = lambda v: (v[0], 0, v[1])
        else:
            extend = lambda v: (v[0], v[1], 0)
        return list(map(extend, verts))

    def process(self):
        if not any(o.is_linked for o in self.outputs):
            return

        profile = self.load_profile()
        optional_inputs = self.get_optional_inputs(profile)

        var_names = self.get_variables()
        self.debug("Var_names: %s; optional: %s", var_names, optional_inputs)
        inputs = self.get_input()

        result_vertices = []
        result_edges = []
        result_knots = []
        result_names = []

        if var_names:
            input_values = []
            for name in var_names:
                try:
                    input_values.append(inputs[name])
                except KeyError as e:
                    name = e.args[0]
                    if name not in optional_inputs:
                        if name in self.inputs:
                            raise SvNoDataError(self.inputs[name])
                        else:
                            self.adjust_sockets()
                            raise SvNoDataError(self.inputs[name])
                    else:
                        input_values.append([None])
            parameters = match_long_repeat(input_values)
        else:
            parameters = [[[]]]

        input_names = [socket.name for socket in self.inputs if socket.is_linked]

        for values in zip(*parameters):
            variables = dict(zip(var_names, values))
            interpreter = Interpreter(self, input_names)
            interpreter.interpret(profile, variables)
            verts = self.extend_out_verts(interpreter.vertices)
            result_vertices.append(verts)
            result_edges.append(interpreter.edges)
            knots = self.extend_out_verts(interpreter.knots)
            result_knots.append(knots)
            result_names.append([[name] for name in interpreter.knotnames])

        self.outputs['Vertices'].sv_set(result_vertices)
        self.outputs['Edges'].sv_set(result_edges)
        self.outputs['Knots'].sv_set(result_knots)
        self.outputs['KnotNames'].sv_set(result_names)

    def storage_set_data(self, storage):
        """
        some verbosity introduced to minimize breaking exists blends/json with this node.
        """
        profile = storage['profile']
        filename = storage['params']['filename']
        new = False
        if new:
            self.info(f"filename |{filename}| found.")
            text_datablock = self.get_bpy_data_from_name(filename, bpy.data.texts)
            
            if text_datablock:
                self.info(f"filename {filename} found in bpy.data.texts - not creating it")
            else:
                text_datablock = bpy.data.texts.new(filename)
                text_datablock.write(profile)
            
            self.file_pointer = text_datablock
        else:
            text_datablock = bpy.data.texts.new(filename)  # are these two different files ?
            bpy.data.texts[filename].clear()               # are these two different files ?
            # yes they can be if filename is already present in bpy.data.texts
            print(text_datablock.name, bpy.data.texts[filename].name) 
            bpy.data.texts[filename].write(profile)
            self.file_pointer = text_datablock

    def storage_get_data(self, storage):

        if self.file_pointer:
            storage['profile'] = self.file_pointer.as_string()
        else:
            self.warning("No file selected")

classes = [
        SvProfileImportMenu,
        SvProfileImportOperator,
        SvPrifilizerMk3,
        SvProfileNodeMK3
    ]

def register():
    _ = [register_class(cls) for cls in classes]


def unregister():
    _ = [unregister_class(cls) for cls in reversed(classes)]
