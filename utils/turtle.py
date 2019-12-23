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
    """
    Face walking turtle API.

    At each moment in time, a turtle stays on one of the mesh faces,
    and looks towards one of edges of the face:

    +---+---+---+
    |   |   |   |
    +---+---+---+
    |   | ^ |   |
    |   | @ |   |
    +---+---+---+
    |   |   |   |
    +---+---+---+

    Walking primitives are turn_next(), turn_prev() and click().
    Other methods are build from these primitives.
    One of the most used methods is step().

    For selecting faces, there are two sets of methods:

    1. select(), unselect() and toggle() to set selection state of the current face.
    2. start_selecting() and stop_selecting() to select all faces which the
       turtle is passing. The selection mask can be specified, to select, for example,
       each second face.

    This class also provides the API to "paint" on custom data layers of the faces.
    Three types of "paints" are supported: int, float and str.
    Each painting layer is identified by it's name. The turtle can paint on several
    layers at the same time.
    By default, there is only one painting layer, of type int, named Turtle.PAINT.
    One can add other painting layers by calling declare_painting_layer().
    NB 1: All painting layers must be declared BEFORE any commands to the turtle, i.e.
    right after constructor was called.
    NB 2: If you wish to use other custom data layers on the same bmesh, for purposes
    other than painting by turtle, then you have to create them BEFORE calling the Turtle
    constructor.
    """

    PREVIOUS = 'PREVIOUS'
    NEXT = 'NEXT'

    SELECT = 'SELECT'
    UNSELECT = 'UNSELECT'
    TOGGLE = 'TOGGLE'
    MASK = 'MASK'

    PAINT = 'turtle_paint'

    def __init__(self, bm, bm_face = None):
        self.bmesh = bm
        # Creation of the custom data layer invalidates all
        # references to mesh's BMFaces!
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
        """
        Create a custom data layer for painting.

        NB 1: All painting layers must be declared BEFORE any commands to the turtle, i.e.
        right after constructor was called.
        NB 2: If you wish to use other custom data layers on the same bmesh, for purposes
        other than painting by turtle, then you have to create them BEFORE calling the Turtle
        constructor.
        """
        if data_type == int:
            layers = self.bmesh.faces.layers.int
        elif data_type == float:
            layers = self.bmesh.faces.layers.float
        elif data_type == str:
            layers = self.bmesh.faces.layers.string

        # Creation of the custom data layer invalidates all
        # references to mesh's BMFaces!
        face_index = self.current_face.index
        loop_index = self.current_loop.index
        layer = layers.new(layer_name)
        self.bmesh.faces.ensure_lookup_table()
        self.bmesh.faces.index_update()
        self.painting_layer[layer_name] = layer
        self.current_face = self.bmesh.faces[face_index]
        self.current_loop = self.current_face.loops[loop_index]

    def turn_next(self, count=1):
        """
        Turn towards the next edge in the sequence.
        If face normal is oriented "as usual", then this
        means "turn counterclockwise".

        +----+      +----+
        |  ^ |  --> |    |
        |  @ |      | <@ |
        +----+      +----+

        If count is more than 1, then repeat this turn specified
        number of times.
        """
        for i in range(count):
            self.current_loop = self.current_loop.link_loop_next

    def turn_prev(self, count=1):
        """
        Turn towards the previous edge in the sequence.
        If face normal is oriented "as usual", then this
        means "turn clockwise".

        +----+      +----+
        | ^  |  --> |    |
        | @  |      | @> |
        +----+      +----+

        If count is more than 1, then repeat this turn specified
        number of times.
        """
        for i in range(count):
            self.current_loop = self.current_loop.link_loop_prev

    def click(self):
        """
        Jump to the face which is beyound the edge
        at which the turtle is looking currently.
        This turtle is a bit strange, because when it jumps it
        turns around, to look at the same edge it was looking, but
        from another side:

        +----+----+      +----+----+
        | @> |    |  --> |    | <@ |
        +----+----+      +----+----+

        This changes the selection state of the face where the turtle
        stepped, if it is in "start_selecting()" mode, according to selection
        mask.

        This updates custom data layers of the face where the turtle stepped,
        if it is in "start_painting()" mode, according to painting masks.
        """
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
        """
        Get the BMLoop opposite to the current one.
        This does not change current turtle or mesh state.
        """
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
        """
        Turn the turtle around, to look at the opposite edge:

        +----+       +----+
        | @> |  -->  | <@ |
        +----+       +----+

        If the current face has odd count of edges, then the term
        "around" is ambigous:

                    +----+      
                    |   > \
                    |  @   *
                    |     /
                  > +----+
                 /
        +----+  /   
        |     \
        | <@   *   ? OR ?
        |     / 
        +----+  \
                 \
                  > +----+      
                    |     \
                    |  @   *
                    |   > /
                    +----+
                
        To decide in such cases, there is `bias` parameter; it can have
        one of two values: Turtle.PREVIOUS and Turtle.NEXT.
        The default value of `bias` parameter can be set as "turtle.opposite_bias".
        By default it is set to Turtle.PREVIOUS.
        """
        self.current_loop = self.get_opposite_loop(self.current_loop)

    def get_next_face(self, count=1, bias=None):
        """
        Get the face (BMFace) which is beyound that edge at which turtle is
        currently looking. If count is greater than 1, then look for the next
        face in the same direction.
        Bias can be provided for cases of odd count of edges in the face.
        This does not change turtle or face state.
        """
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
        """
        Step to the next face, i.e. the face which is beyond the edge
        at which the turtle is currently looking, without changing 
        turtle's orientation.

        +----+----+      +----+----+
        | @> |    |  --> |    | @> |
        +----+----+      +----+----+

        If count is greater than 1, then repeat this step the specified
        number of times.
        Bias can be provided for cases of odd count of edges in the face.
        """
        for i in range(count):
            self.click()
            self.turn_opposite(bias=bias)

    def step_back(self, count=1, bias=None):
        """
        Similar to step(), but step backwards:

        +----+----+      +----+----+
        |    | @> |  --> | @> |    |
        +----+----+      +----+----+
        """
        for i in range(count):
            self.turn_opposite(bias=bias)
            self.click()

    def strafe_next(self, count=1):
        """
        Step to the face which is in the "next" (i.e. usually counterclockwise)
        direction, without changing turtle's orientation:

        +----+----+      +----+----+
        |    |  ^ |      |  ^ |    |
        |    |  @ |  --> |  @ |    |
        +----+----+      +----+----+

        If count is greater than 1, then repeat this step the specified
        number of times.
        """
        for i in range(count):
            self.turn_next()
            self.click()
            self.turn_next()

    def strafe_prev(self, count=1):
        """
        Step to the face which is in the "prev" (i.e. usually clockwise)
        direction, without changing turtle's orientation:

        +----+----+      +----+----+
        |  ^ |    |      |    |  ^ |
        |  @ |    |  --> |    |  @ |
        +----+----+      +----+----+

        If count is greater than 1, then repeat this step the specified
        number of times.
        """
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
        """
        Mark the current face as selected.
        """
        self.current_face.select = True
        debug("Selecting face #%s", self.current_face.index)

    def unselect(self):
        """
        Mark the current face as not selected.
        """
        self.current_face.select = False
        debug("Unselecting face #%s", self.current_face.index)

    def toggle(self):
        """
        Toggle the selection state of the current face.
        """
        self.current_face.select = not self.current_face.select
        debug("Set face #%s selection := %s", self.current_face.index, self.current_face.select)

    def start_selecting(self, mode = None, mask=None):
        """
        Start selecting faces which the turtle passes.
        This mode can be stoppped by calling stop_selecting().

        mode: selection mode. Can be Turtle.SELECT, Turtle.UNSELECT, Turtle.TOGGLE or Turtle.MASK.
        mask: selection mask. Used with mode == Turtle.MASK. The mask is used with
              infinite repetition. For example:

              turtle.start_selecting(mode = Turtle.MASK, mask = [0, 1])
              turtle.step(6)
              turtle.stop_selecting()

              This will select each other face: 0[1]2[3]4[5].

        If mask is not specified, then the mask used with the previous start_selecting() call
        will be used. If the mask was never provided, there will be an exception.
        """
        if mode is None:
            mode = self.SELECT
        self.selection_mode = mode
        if mode == self.MASK:
            if not mask and not self.selection_mask:
                raise Exception("You have to specify the mask when setting selection mode to MASK")
            if mask:
                self.selection_mask = mask

    def stop_selecting(self):
        """
        Stop selecting faces which the turtle passes.
        """
        self.selection_mode = None

    def paint(self, value, layer_name = PAINT):
        """
        Paint the current face with specified value, on specified layer.
        The painting layer must be defined by calling declare_painting_layer()
        right after calling the Turtle() constructor. By default, there is
        one painting layer, named Turtle.PAINT.
        """
        layer = self.painting_layer[layer_name]
        self.current_face[layer] = value

    def start_painting(self, value = None, layer_name = PAINT):
        """
        Start painting faces which the turtle passes.
        If value is not specified, then the value used with previous
        start_painting() call will be used. If the value was never provided,
        there will be an exception.
        A list of values can be specified instead of the single value. In this
        case, these values will be used in order, with repetition.
        The painting layer must be defined by calling declare_painting_layer()
        right after calling the Turtle() constructor. By default, there is
        one painting layer, named Turtle.PAINT.
        """
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
        """
        Stop painting faces which the turtle passes.
        """
        self.is_painting = False

    def reset_selection_cycle(self):
        self.selection_cycle_index = 0

    def reset_painting_cycle(self, layer_name = PAINT):
        self.painting_index[layer_name] = 0

    def get_selected_faces_pydata(self):
        return [[vert.index for vert in face.verts] for face in self.bmesh.faces if face.select]

    def get_selected_faces(self):
        return [face for face in self.bmesh.faces if face.select]

    def get_selection_mask(self):
        return [face.select for face in self.bmesh.faces]

    def get_painting_value(self, face, layer_name = PAINT):
        layer = self.painting_layer[layer_name]
        return face[layer]

    def get_painting_data(self, layer_name = PAINT):
        layer = self.painting_layer[layer_name]
        return [face[layer] for face in self.bmesh.faces]

    def was_at_face(self, face):
        v = face[self.index_layer]
        return (v != 0)

    @property
    def is_looking_at_boundary(self):
        return self.current_loop.edge.is_boundary

    @property
    def is_at_boundary(self):
        return any(edge.is_boundary for edge in self.current_face.edges)

    @property
    def was_here(self):
        return self.was_at_face(self.current_face)

