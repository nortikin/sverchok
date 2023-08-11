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


import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level,\
    ensure_min_nesting, repeat_last_for_length
from sverchok.utils.voronoi3d import voronoi_on_solid
from sverchok.utils.geom import scale_relative, center, diameter
from sverchok.utils.solid import BMESH, svmesh_to_solid
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import Part


class SvVoronoiOnSolidNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Voronoi Solid
    Tooltip: Generate Voronoi diagram on the Solid object
    """
    bl_idname = 'SvVoronoiOnSolidNode'
    bl_label = 'Voronoi on Solid'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'
    sv_dependencies = {'scipy', 'FreeCAD'}

    modes = [
            ('SURFACE', "Surface", "Generate regions of Voronoi diagram on the surface of the solid", 0),
            ('VOLUME', "Volume", "Split volume of the solid body into regions of Voronoi diagram", 2)
        ]

    mode : EnumProperty(
        name = "Mode",
        items = modes,
        update = updateNode)
    
    accuracy : IntProperty(
            name = "Accuracy",
            description = "Accuracy for mesh to solid transformation",
            default = 6,
            min = 1,
            update = updateNode)

    inset : FloatProperty(
        name = "Inset",
        min = 0.0, max = 1.0,
        default = 0.1,
        description="Percentage of space to leave between generated Voronoi regions",
        update = updateNode)

    scale_types = [
            ('SITE', "Site", "Scale each region relative to corresponding site location", 0),
            ('MEAN', "Barycenter", "Scale each region relative to it's barycenter, i.e. average location of it's vertices", 1)
        ]

    scale_center : EnumProperty(
            name = "Scale around",
            description = "Defines the center, along which the regions of Voronoi diagram are to be scaled in order to make inset",
            items = scale_types,
            default = 'SITE',
            update = updateNode)

    flat_output : BoolProperty(
        name = "Flat output",
        description = "If checked, output single flat list of fragments for all input solids; otherwise, output a separate list of fragments for each solid.",
        default = True,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', 'Solid')
        self.inputs.new('SvVerticesSocket', "Sites")
        self.inputs.new('SvStringsSocket', "Inset").prop_name = 'inset'
        self.outputs.new('SvSolidSocket', "InnerSolid")
        self.outputs.new('SvSolidSocket', "OuterSolid")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")
        layout.prop(self, "flat_output")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'scale_center')
        layout.prop(self, 'accuracy')

    def scale_cells(self, verts, sites, insets, precision):
        if all(i == 0.0 for i in insets):
            return verts
        verts_out = []
        for vs, site, inset in zip(verts, sites, insets):
            if inset >= 1.0:
                continue
            if self.scale_center == 'SITE':
                c = site
            else:
                c = center(vs)
            vs1 = scale_relative(vs, c, 1.0 - inset)
            if diameter(vs1, axis=None) <= precision:
                continue
            verts_out.append(vs1)
        return verts_out

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        solid_in = self.inputs['Solid'].sv_get()
        sites_in = self.inputs['Sites'].sv_get()
        inset_in = self.inputs['Inset'].sv_get()

        solid_in = ensure_nesting_level(solid_in, 2, data_types=(Part.Shape,))
        input_level = get_data_nesting_level(sites_in)
        sites_in = ensure_nesting_level(sites_in, 4)
        inset_in = ensure_min_nesting(inset_in, 2)

        nested_output = input_level > 3
        need_inner = self.outputs['InnerSolid'].is_linked
        need_outer = self.outputs['OuterSolid'].is_linked

        precision = 10 ** (-self.accuracy)

        inner_fragments_out = []
        outer_fragments_out = []
        for params in zip_long_repeat(solid_in, sites_in, inset_in):
            new_inner_fragments = []
            new_outer_fragments = []
            for solid, sites, inset in zip_long_repeat(*params):
                verts, edges, faces = voronoi_on_solid(solid, sites,
                            do_clip=True, clipping=None)

                if isinstance(inset, list):
                    inset = repeat_last_for_length(inset, len(sites))
                else:
                    inset = [inset for i in range(len(sites))]
                verts = self.scale_cells(verts, sites, inset, precision)
                fragments = [svmesh_to_solid(vs, fs, precision, method=BMESH, remove_splitter=False) for vs, fs in zip(verts, faces)]

                if self.mode == 'SURFACE':
                    if solid.Shells:
                        shell = solid.Shells[0]
                    else:
                        shell = Part.Shell(solid.Faces)
                    src = shell
                else: # VOLUME
                    src = solid

                if need_inner:
                    inner = [src.common(fragments)]
                    if self.flat_output:
                        new_inner_fragments.extend(inner)
                    else:
                        new_inner_fragments.append(inner)

                if need_outer:
                    outer = [src.cut(fragments)]
                    if self.flat_output:
                        new_outer_fragments.extend(outer)
                    else:
                        new_outer_fragments.append(outer)

            if nested_output:
                inner_fragments_out.append(new_inner_fragments)
                outer_fragments_out.append(new_outer_fragments)
            else:
                inner_fragments_out.extend(new_inner_fragments)
                outer_fragments_out.extend(new_outer_fragments)

        self.outputs['InnerSolid'].sv_set(inner_fragments_out)
        self.outputs['OuterSolid'].sv_set(outer_fragments_out)


def register():
    bpy.utils.register_class(SvVoronoiOnSolidNode)


def unregister():
    bpy.utils.unregister_class(SvVoronoiOnSolidNode)
