# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, map_recursive, zip_long_repeat,
                                     ensure_nesting_level, get_data_nesting_level)
from sverchok.utils.curve.freecad import SvSolidEdgeCurve
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import Part

class SvSolidSectionNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Section
    Tooltip: Generate Intersection Curves and Points
    """
    bl_idname = 'SvSolidSectionNode'
    bl_label = 'Solid Section'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SOLID_SECTION'
    sv_category = "Solid Operators"
    sv_dependencies = {'FreeCAD'}

    nurbs_output : BoolProperty(
        name = "NURBS Output",
        description = "Output curves in NURBS representation",
        default = False,
        update=updateNode)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'nurbs_output', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Shape A")
        #"Shape" is a generic term covering all different topological types defined by Open CASCADE Technology (OCCT)
        self.inputs.new('SvSolidSocket', "Shape B")
        
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvCurveSocket', "Curves")

    def make_section(self, shapes):
        base = shapes[0].copy()
        rest = shapes[1:]
        section = base.section(rest)
        return section

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sections_out = []

        shapes_a_in = self.inputs['Shape A'].sv_get()
        shapes_b_in = self.inputs['Shape B'].sv_get()
        level_a = get_data_nesting_level(shapes_a_in, data_types=(Part.Shape,))
        level_b = get_data_nesting_level(shapes_b_in, data_types=(Part.Shape,))
        shapes_a_in = ensure_nesting_level(shapes_a_in, 2, data_types=(Part.Shape,))
        shapes_b_in = ensure_nesting_level(shapes_b_in, 2, data_types=(Part.Shape,))
        level = max(level_a, level_b)

        for params in zip_long_repeat(shapes_a_in, shapes_b_in):
            new_sections = []
            for shape_a, shape_b in zip_long_repeat(*params):
                result = self.make_section([shape_a, shape_b])
                new_sections.append(result)
            sections_out.extend(new_sections)

        def get_verts(section):
            verts = []
            for v in section.Vertexes:
                verts.append(v.Point[:])
            return verts

        def get_edges(section):
            edges_curves = []
            for e in section.Edges:
                try:
                    curve = SvSolidEdgeCurve(e)
                    if self.nurbs_output:
                        curve = curve.to_nurbs()
                    edges_curves.append(curve)
                except TypeError:
                    pass
            return edges_curves

        verts_out = map_recursive(get_verts, sections_out, data_types=(Part.Shape,))
        edges_out = map_recursive(get_edges, sections_out, data_types=(Part.Shape,))

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Curves'].sv_set(edges_out)


def register():
    bpy.utils.register_class(SvSolidSectionNode)


def unregister():
    bpy.utils.unregister_class(SvSolidSectionNode)

