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

from mathutils import Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, StringProperty, BoolProperty, FloatVectorProperty, IntVectorProperty

import blf
import bgl
import gpu
from gpu_extras.batch import batch_for_shader

from sverchok.utils.context_managers import sv_preferences
from sverchok.core.socket_data import SvGetSocketInfo
from sverchok.data_structure import updateNode, node_id, enum_item_4, fullList, match_long_repeat
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui import bgl_callback_nodeview as nvBGL

# star imports easing_dict and all easing functions.
from sverchok.utils.sv_easing_functions import *

easing_list = []
for k in sorted(easing_dict.keys()):
    fname = easing_dict[k].__name__
    easing_list.append(tuple([str(k), fname, "", k]))


palette_dict = {
    "default": (
        (0.243299, 0.590403, 0.836084, 1.00),  # back_color
        (0.390805, 0.754022, 1.000000, 0.70),  # grid_color
        (1.000000, 0.330010, 0.107140, 1.00)   # line_color
    ),
    "scope": (
        (0.274677, 0.366253, 0.386430, 1.00),  # back_color
        (0.423268, 0.558340, 0.584078, 1.00),  # grid_color
        (0.304762, 1.000000, 0.062827, 1.00)   # line_color
    ),
    "sniper": (
        (0.2, 0.2, 0.2, 0.20),  # back_color
        (0.423268, 0.558340, 0.584078, 0.40),  # grid_color
        (0.304762, 1.000000, 0.062827, 1.00)   # line_color
    )
}


def simple28_grid_xy(x, y, args):
    """ x and y are passed by default so you could add font content """

    geom, config = args
    back_color, grid_color, line_color = config.palette
    background_color = config.background_color
    # draw background, this could be cached......
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": geom.background_coords}, indices=geom.background_indices)
    shader.bind()
    shader.uniform_float("color", background_color)
    batch.draw(shader)

    # draw grid and graph
    config.batch.draw(config.shader)


def generate_number_geom(config, numbers):
    geom = lambda: None
    x, y = config.loc
    size = 140 * config.scale
    scale = config.scale
    # back_color, grid_color, line_color = config.palette
    cycle = config.cycle
    sys_scale = config.sys_scale
    line_color = config.line_color
    w, h = config.size
    all_numbers = [n for l in numbers for n in l ]
    maxmin = [max(all_numbers), min(all_numbers)]
    # background geom
    # w = size
    # h = size
    # w = (maxmin[0][0]- maxmin[0][1]) * scale
    # h = (maxmin[1][0]- maxmin[1][1]) * scale
    margin = 1 * scale
    margin = 10 * sys_scale
    geom.background_coords = [
        (x, y + margin),
        (x + w + 2*margin, y + margin),
        (w + x + 2*margin, y - h - margin),
        (x, y - h - margin)]
    geom.background_indices = [(0, 1, 2), (0, 2, 3)]

    vertices = []
    vertex_colors = []
    indices = []
    num_height = h/(max(all_numbers)- min(all_numbers))
    idx_offset = 0
    if config.continuous:
        for nums, col in zip(numbers, line_color):
            num_width = w/(len(nums)-1)
            for i, n in enumerate(nums):
                _px = x + (i * num_width) * sys_scale + margin
                _py = y + ((n -maxmin[1])* num_height) * sys_scale - h 
                vertices.append([_px, _py])
                vertex_colors.append(col)
            for i in range(len(nums)-1):
                indices.append([i + idx_offset, i + 1 + idx_offset])
            idx_offset += len(nums)
    else:
        for nums, col in zip(numbers, line_color):
            num_width = w/len(nums)
            for i, n in enumerate(nums):
                _px = x + (i * num_width) * sys_scale + margin
                _py = y + ((n -maxmin[1])* num_height) * sys_scale - h 
                vertices.extend([[_px, _py], [_px + num_width, _py]])
                vertex_colors.extend([col, col])
                indices.append([2*i + idx_offset, 2*i + 1 + idx_offset])
            idx_offset += 2*len(nums)
            

    geom.vertices = vertices
    geom.vertex_colors = vertex_colors
    geom.indices = indices
    return geom

class SvViewer2D(bpy.types.Node, SverchCustomTreeNode):
    '''Curved interpolation'''
    bl_idname = 'SvViewer2D'
    bl_label = 'Viewer 2D'
    sv_icon = 'SV_EASING'

    modes = [
        ('Number', 'Number', 'Input UV coordinates to evaluate texture', '', 1),
        ('Path', 'Path', 'Matrix to apply to verts before evaluating texture', '', 2),
        ('Edges', 'Edges', 'Matrix of texture (External Object matrix)', '', 3),
        ('Polygons', 'Polygons', 'Matrix of texture (External Object matrix)', '', 3),

    ]
    n_id: StringProperty(default='')

    mode: EnumProperty(
        name='Mode',
        items=modes,
        default='Path',
        description="Display Mode",
        update=updateNode)

    activate: BoolProperty(
        name='Show', description='Activate drawing',
        default=True, update=updateNode
    )
    cycle: BoolProperty(
        name='Cycle', description='Activate drawing',
        default=True, update=updateNode
    )

    selected_mode: EnumProperty(
        items=easing_list, description="Set easing Function to:",
        default="0", update=updateNode
    )

    in_float: FloatProperty(
        min=0.0, max=1.0, default=0.0, name='Float Input',
        description='input to the easy function', update=updateNode
    )
    draw_scale: FloatProperty(
        min=0.0, default=10.0, name='Scale',
        description='Drawing Scale', update=updateNode
    )
    drawing_size: IntVectorProperty(
        update=updateNode, name='Size', default=(150, 150),
        size=2
        )
    continuous: BoolProperty(
        name='Continuous', description='Continuous Graph',
        default=True, update=updateNode
    )
    unit_color: FloatVectorProperty(
        update=updateNode, name='', default=(.9, .9, .8, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
        )
    background_color: FloatVectorProperty(
        update=updateNode, name='', default=(.05, .05, .05, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
        )
    selected_theme_mode: EnumProperty(
        items=enum_item_4(["default", "scope", "sniper"]), default="default", update=updateNode
    )

    def custom_draw_socket(self, socket, context, l):
        info = socket.get_socket_info()

        r = l.row(align=True)
        split = r.split(factor=0.85)
        r1 = split.row(align=True)
        r1.prop(self, "selected_mode", text="")
        r1.prop(self, 'activate', icon='NORMALIZE_FCURVES', text="")
        if info:
            r2 = split.row()
            r2.label(text=info)
    def draw_buttons(self, context, layout):
        r0 = layout.row()
        r0.prop(self, "activate", text="", icon="HIDE_" + ("OFF" if self.activate else "ON"))
        r0.prop(self, "mode")
        c0 = layout.column(align=True)
        c0.prop(self, "background_color")
        
        if self.mode == 'Number':
            row = c0.row(align=True)
            for j in range(2):
                row.prop(self, 'drawing_size', index=j, text='XY'[j])
            c0.prop(self, 'continuous')
        elif self.mode == 'Path':
            c0.prop(self, "draw_scale")
            layout.prop(self, "cycle")
        
    def draw_buttons_ext(self, context, l):
        l.prop(self, "selected_theme_mode")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Number")
        self.inputs.new('SvVerticesSocket', "Vecs")
        self.inputs.new('SvColorSocket', "Color").custom_draw = 'draw_color_socket'
        self.get_and_set_gl_scale_info()
        
    def draw_color_socket(self, socket, context, layout):
        if not socket.is_linked:
            layout.prop(self, 'unit_color', text="")

        else:
            layout.label(text=socket.name+ '. ' + SvGetSocketInfo(socket))

    def get_drawing_attributes(self):
        """
        adjust render location based on preference multiplier setting
        """
        x, y = [int(j) for j in (Vector(self.absolute_location) + Vector((self.width + 20, 0)))[:]]

        try:
            with sv_preferences() as prefs:
                multiplier = prefs.render_location_xy_multiplier
                scale = prefs.render_scale
        except:
            # print('did not find preferences - you need to save user preferences')
            multiplier = 1.0
            scale = 1.0
        x, y = [x * multiplier, y * multiplier]

        return x, y, scale, multiplier

    def generate_shader(self, geom):
        shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": geom.vertices, "color": geom.vertex_colors}, indices=geom.indices)
        return batch, shader

    def generate_graph_geom(self, config, paths):
        geom = lambda: None
        x, y = config.loc
        size = 140 * config.scale
        scale = config.scale
        # back_color, grid_color, line_color = config.palette
        cycle = config.cycle
        sys_scale = config.sys_scale
        line_color = config.line_color

        all_vecs = [v for vecs in paths for v in vecs ]
        maxmin = list(zip(map(max, *all_vecs), map(min, *all_vecs)))
        # background geom
        w = size
        h = size
        w = (maxmin[0][0]- maxmin[0][1]) * scale
        h = (maxmin[1][0]- maxmin[1][1]) * scale
        margin = 1 * scale
        margin = 10 * sys_scale
        geom.background_coords = [
            (x, y + margin), 
            (x + w + 2*margin, y + margin),
            (w + x + 2*margin, y - h - margin),
            (x, y - h - margin)]
        geom.background_indices = [(0, 1, 2), (0, 2, 3)]

        vertices = []
        vertex_colors = []
        indices = []

        idx_offset = 0
        for vecs, col in zip(paths, line_color):
            graphline = []
            for v in vecs:
                _px = x + (v[0] - maxmin[0][1]) * scale + margin
                _py = y + (v[1] - maxmin[1][0]) * scale
                graphline.append([_px, _py])
                vertex_colors.append(col)
            vertices.extend(graphline)

            for i in range(len(vecs)-1):
                indices.append([i + idx_offset, i + 1 + idx_offset])
            if cycle:
                indices.append([len(graphline)-1 + idx_offset, 0 + idx_offset])
            idx_offset += len(graphline)

        geom.vertices = vertices
        geom.vertex_colors = vertex_colors
        geom.indices = indices
        return geom

    def process(self):
        if self.mode == 'Number':
            p = self.inputs['Number'].sv_get()
        else:
            p = self.inputs['Vecs'].sv_get()
        path_color = self.inputs['Color'].sv_get(default=[[self.unit_color]])[0]
        fullList(path_color, len(p))
        n_id = node_id(self)

        # end early
        nvBGL.callback_disable(n_id)

        if self.activate:

            config = lambda: None
            x, y, scale, multiplier = self.get_drawing_attributes()

            config.loc = (x, y)
            config.palette = palette_dict.get(self.selected_theme_mode)[:]
            config.sys_scale = scale
            config.scale = scale*self.draw_scale
            config.cycle = self.cycle
            config.background_color = self.background_color
            config.line_color = path_color
            # config.easing_func = easing_func

            if self.mode == 'Number':
                config.size = self.drawing_size
                config.continuous = self.continuous
                geom = generate_number_geom(config, p)
            else:
                geom = self.generate_graph_geom(config, p)
            
            config.batch, config.shader = self.generate_shader(geom)
            
            draw_data = {
                'mode': 'custom_function',
                'tree_name': self.id_data.name[:],
                'loc': (x, y),
                'custom_function': simple28_grid_xy,
                'args': (geom, config)
            }
            nvBGL.callback_enable(n_id, draw_data)

    def sv_free(self):
        nvBGL.callback_disable(node_id(self))

    def sv_copy(self, node):
        # reset n_id on copy
        self.n_id = ''

    def sv_update(self):
        # handle disconnecting sockets, also disconnect drawing to view?
        if not ("Float" in self.inputs):
            return
        try:
            if not self.inputs[0].other:
                nvBGL.callback_disable(node_id(self))
        except:
            print('Easing node update holdout (not a problem)')


classes = [SvViewer2D,]
register, unregister = bpy.utils.register_classes_factory(classes)
