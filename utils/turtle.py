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

from collections import defaultdict
import bmesh
import mathutils

from sverchok.utils.logging import debug

class Turtle(object):

    PREVIOUS = 'PREVIOUS'
    NEXT = 'NEXT'

    SELECT = 'SELECT'
    UNSELECT = 'UNSELECT'
    TOGGLE = 'TOGGLE'
    MASK = 'MASK'

    PAINT = 'turtle_paint'

    def __init__(self, bm, bm_face = None):
        self.bmesh = bm
        self.index_layer = bm.faces.layers.int.new("turtle_index")
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        self.current_face = bm.faces[0] if bm_face is None else bm_face
        self.current_loop = self.current_face.loops[0]
        self.opposite_bias = self.PREVIOUS
        self.selection_mode = None
        self.selection_mask = None
        self.selection_cycle_index = 0
        self.current_index = 1

        self.painting_layer = dict()
        self.painting_mask = dict()
        self.painting_index = defaultdict(int)
        self.is_painting = False

        self.current_face[self.index_layer] = self.current_index
        self.declare_painting_layer(self.PAINT)

    def declare_painting_layer(self, layer_name, data_type = int):
        if data_type == int:
            layers = self.bmesh.faces.layers.int
        elif data_type == float:
            layers = self.bmesh.faces.layers.float
        elif data_type == str:
            layers = self.bmesh.faces.layers.string

        face_index = self.current_face.index
        loop_index = self.current_loop.index
        layer = layers.new(layer_name)
        self.bmesh.faces.ensure_lookup_table()
        self.bmesh.faces.index_update()
        self.painting_layer[layer_name] = layer
        self.current_face = self.bmesh.faces[face_index]
        self.current_loop = self.current_face.loops[loop_index]

    def turn_next(self, count=1):
        for i in range(count):
            self.current_loop = self.current_loop.link_loop_next

    def turn_prev(self, count=1):
        for i in range(count):
            self.current_loop = self.current_loop.link_loop_prev

    def click(self):
        self.current_index += 1
        self.current_face[self.index_layer] = self.current_index
        next_loop = self.current_loop.link_loop_radial_next
        self.current_loop = next_loop
        self.current_face = next_loop.face

        debug("Current face # := %s", self.current_face.index)

        if self.selection_mode == self.MASK:
            if not self.selection_mask:
                raise Exception("Selection mode is set to MASK, but mask is not specified")
            n = len(self.selection_mask)
            self.selection_cycle_index = (self.selection_cycle_index + 1) % n
            mode = self.selection_mask[self.selection_cycle_index]
            if mode not in [self.SELECT, self.UNSELECT, self.TOGGLE, 0, 1, False, True]:
                raise Exception("Unsupported flag in the selection mask")
            if mode == True or mode == 1:
                mode = self.SELECT
            elif mode == False or mode == 0:
                mode = self.UNSELECT
        else:
            mode = self.selection_mode
        if mode == self.SELECT:
            self.select()
        elif mode == self.UNSELECT:
            self.unselect()
        elif mode == self.TOGGLE:
            self.toggle()

        if self.is_painting:
            for painting_layer in self.painting_layer.values():
                painting_mask = self.painting_mask.get(painting_layer.name)
                if not painting_mask:
                    raise Exception("Painting layer is set, but painting mask is not")
                n = len(painting_mask)
                self.painting_index[painting_layer.name] = (self.painting_index[painting_layer.name] + 1) % n
                value = painting_mask[self.painting_index[painting_layer.name]]
                self.current_face[painting_layer] = value
                debug("Paint face #%s, layer `%s' with value `%s'", self.current_face.index, painting_layer.name, value)

    def get_opposite_loop(self, loop, bias=None):
        if bias is None:
            bias = self.opposite_bias
        face = loop.face
        n = len(face.loops)
        if n % 2 == 0:
            steps = n // 2
        else:
            if bias == self.PREVIOUS:
                steps = n // 2
            else:
                steps = n // 2 + 1
        for i in range(steps):
            loop = loop.link_loop_next
        return loop

    def turn_opposite(self, bias=None):
        self.current_loop = self.get_opposite_loop(self.current_loop)

    def get_next_face(self, count=1, bias=None):
        face = self.current_face
        loop = self.current_loop
        for i in range(count):
            # click
            next_loop = loop.link_loop_radial_next
            face = next_loop.face
            # opposite
            loop = self.get_opposite_loop(next_loop, bias)
        return face

    def step(self, count=1, bias=None):
        for i in range(count):
            self.click()
            self.turn_opposite(bias=bias)

    def step_back(self, count=1, bias=None):
        for i in range(count):
            self.turn_opposite(bias=bias)
            self.click()

    def strafe_next(self, count=1):
        for i in range(count):
            self.turn_next()
            self.click()
            self.turn_next()

    def strafe_prev(self, count=1):
        for i in range(count):
            self.turn_prev()
            self.click()
            self.turn_prev()

    def zig_zag(self, steps=1, leg=0, turns=1):
        for i in range(steps):
            self.step(count=leg)
            self.click()
            self.turn_next(turns)
            self.step(count=leg)
            self.click()
            self.turn_prev(turns)

    def select(self):
        self.current_face.select = True
        debug("Selecting face #%s", self.current_face.index)

    def unselect(self):
        self.current_face.select = False
        debug("Unselecting face #%s", self.current_face.index)

    def toggle(self):
        self.current_face.select = not self.current_face.select
        debug("Set face #%s selection := %s", self.current_face.index, self.current_face.select)

    def start_selecting(self, mode = None, mask=None):
        if mode is None:
            mode = self.SELECT
        self.selection_mode = mode
        if mode == self.MASK:
            if not mask and not self.selection_mask:
                raise Exception("You have to specify the mask when setting selection mode to MASK")
            if mask:
                self.selection_mask = mask

    def stop_selecting(self):
        self.selection_mode = None

    def paint(self, value, layer_name = PAINT):
        layer = self.painting_layer[layer_name]
        self.current_face[layer] = value

    def start_painting(self, value = None, layer_name = PAINT):
        if value is not None and not isinstance(value, (list, tuple)):
            value = [value]
        layer = self.painting_layer.get(layer_name)
        if layer is None:
            raise Exception("This layer was not declared")
        if value is None and self.painting_mask.get(layer_name) is None:
            raise Exception("Painting mask was not specified")
        if value is not None:
            self.painting_mask[layer_name] = value
        self.is_painting = True

    def stop_painting(self, layer_name = PAINT):
        self.is_painting = False

    def reset_selection_cycle(self):
        self.selection_cycle_index = 0

    def reset_painting_cycle(self, layer_name = PAINT):
        self.painting_index[layer_name] = 0

    def get_selected_faces(self):
        return [[vert.index for vert in face.verts] for face in self.bmesh.faces if face.select]

    def get_selection_mask(self):
        return [face.select for face in self.bmesh.faces]

    def get_painting_data(self, layer_name = PAINT):
        layer = self.painting_layer[layer_name]
        return [face[layer] for face in self.bmesh.faces]

    @property
    def is_looking_at_boundary(self):
        return self.current_loop.edge.is_boundary

    @property
    def is_at_boundary(self):
        return any(edge.is_boundary for edge in self.current_face.edges)

    @property
    def was_here(self):
        v = self.current_face[self.index_layer]
        return (v != 0)

