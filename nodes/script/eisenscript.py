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

"""
EisenScript node for Sverchok.

Provides access to the EisenScript interpreter. Select a Blender text
block containing an EisenScript program, and the node outputs one
matrix socket per primitive type (box, sphere, grid, line, point,
triangle). Each socket carries a list of 4×4 placement matrices.
"""

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from sverchok.utils.modules.eisenscript import parse, Interpreter


# Canonical primitive names (keys in InterpreterResult.matrices)
_PRIMITIVE_NAMES = ("box", "grid", "sphere", "line", "point", "triangle")


class SvEisenscriptNode(SverchCustomTreeNode, bpy.types.Node):
    """EisenScript interpreter node."""
    bl_idname = 'SvEisenscriptNode'
    bl_label = 'EisenScript'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_GENERATIVE_ART'

    # --- bpy properties ---

    script_text: StringProperty(
        name="Script",
        description="Blender text block with EisenScript source",
        default="",
        update=updateNode,
    )

    seed: IntProperty(
        name="Seed",
        description="Random seed for weighted rule selection",
        default=0,
        min=0,
        options={'ANIMATABLE'},
        update=updateNode,
    )

    max_depth: IntProperty(
        name="Max depth",
        description="Global recursion depth limit (overrides set maxdepth)",
        default=1000,
        min=1,
        options={'ANIMATABLE'},
        update=updateNode,
    )

    max_objects: IntProperty(
        name="Max objects",
        description="Hard cap on total primitive instances (0 = unlimited)",
        default=0,
        min=0,
        options={'ANIMATABLE'},
        update=updateNode,
    )

    origin_as_center: BoolProperty(
        name="Origin center",
        description="Use (0,0,0) as transform center (legacy LSystem behavior). "
                    "If off, use (0.5,0.5,0.5) per EisenScript spec",
        default=True,
        update=updateNode,
    )

    # --- UI ---

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop_search(self, 'script_text', bpy.data, 'texts', text='', icon='TEXT')
        col.separator()
        col.prop(self, "seed", text="Seed")
        col.prop(self, "max_depth", text="Max depth")
        col.prop(self, "max_objects", text="Max objects")
        col.prop(self, "origin_as_center", text="Origin center")

    # --- Socket management ---

    def sv_init(self, context):
        # No inputs
        # Fixed outputs — one per primitive type
        for name in _PRIMITIVE_NAMES:
            self.outputs.new('SvMatrixSocket', name.capitalize())

    # --- Processing ---

    def process(self):
        if not self.script_text or self.script_text not in bpy.data.texts:
            for name in _PRIMITIVE_NAMES:
                self.outputs[name.capitalize()].sv_set([[]])
            return

        if not any(out.is_linked for out in self.outputs):
            return

        source = bpy.data.texts[self.script_text].as_string()
        program = parse(source)

        # Build interpreter with user overrides.
        # Node properties take precedence over program settings.
        max_objects_val = self.max_objects if self.max_objects > 0 else None

        interp = Interpreter(
            max_depth=self.max_depth,
            max_objects=max_objects_val,
            seed=self.seed,
            origin_as_center=self.origin_as_center,
        )
        result = interp._interpret(program)

        # Output matrices per primitive
        for name in _PRIMITIVE_NAMES:
            mats = result.matrices.get(name, [])
            self.outputs[name.capitalize()].sv_set(mats if mats else [[]])


def register():
    bpy.utils.register_class(SvEisenscriptNode)


def unregister():
    bpy.utils.unregister_class(SvEisenscriptNode)
