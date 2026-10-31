# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.stairs_module import StairError, build_flight, build, check


KINDS = [
    ('CONCRETE', 'Concrete', 'One cast solid with a sloping soffit', 0),
    ('PRECAST', 'Precast', 'One block per step, each lapping under the next', 1),
    ('TIMBER', 'Timber', 'Separate tread boards and riser boards', 2),
]
TOES = [
    ('SQUARE', 'Square', 'Square front edge', 0),
    ('CHAMFER', 'Chamfer', 'Chamfered front edge', 1),
    ('ROUND', 'Round', 'Rounded front edge', 2),
]
STANDARDS = [
    ('PRIVATE', 'Private', 'Private stair: rise 150-220 mm, going 220 mm or more, 2R+G 550-700 mm', 0),
    ('PUBLIC', 'Public', 'General use stair: rise 150-170 mm, going 280 mm or more, 2R+G 550-700 mm', 1),
    ('NONE', 'No check', 'Do not check rise and going', 2),
]


def _depth(data):
    d = 0
    while True:
        if hasattr(data, 'ndim'):
            return d + data.ndim
        if isinstance(data, (list, tuple)) and len(data):
            d += 1
            data = data[0]
        else:
            return d + (1 if isinstance(data, (list, tuple)) else 0)


def as_objects(data, level):
    """wrap a single object's data so the outer level is always the object list"""
    while _depth(data) < level:
        data = [data]
    return data


def per_object_value(values):
    out = []
    for obj in as_objects(values, 2):
        obj = list(obj) if hasattr(obj, '__len__') else [obj]
        out.append(float(obj[0]) if len(obj) else 0.0)
    return out


class SvStairsNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: stairs steps stair flight riser tread winder
    Tooltip: Stairs from a plan sketch: two boundaries, riser lines and a walking path
    """
    bl_idname = 'SvStairsNode'
    bl_label = 'Stairs'
    bl_icon = 'IPO_CONSTANT'

    kind: EnumProperty(name="Kind", items=KINDS, default='CONCRETE', update=updateNode)
    toe: EnumProperty(name="Toe", items=TOES, default='SQUARE', update=updateNode)
    standard: EnumProperty(name="Check", items=STANDARDS, default='PRIVATE', update=updateNode)

    level_start: FloatProperty(name="Level Start", default=0.0, precision=3, update=updateNode)
    level_end: FloatProperty(name="Level End", default=2.7, precision=3, update=updateNode)

    toe_size: FloatProperty(
        name="Toe Size", default=0.01, min=0.0, precision=3, subtype='DISTANCE',
        description="Chamfer or radius of the front edge", update=updateNode)
    nosing: FloatProperty(
        name="Nosing", default=0.02, min=0.0, precision=3, subtype='DISTANCE',
        description="How far a tread reaches past its riser line", update=updateNode)
    waist: FloatProperty(
        name="Waist", default=0.15, min=0.01, precision=3, subtype='DISTANCE',
        description="Concrete thickness under the steps, square to the pitch", update=updateNode)
    tread_thickness: FloatProperty(
        name="Tread", default=0.04, min=0.005, precision=3, subtype='DISTANCE',
        description="Tread board thickness", update=updateNode)
    riser_thickness: FloatProperty(
        name="Riser", default=0.02, min=0.005, precision=3, subtype='DISTANCE',
        description="Riser board thickness", update=updateNode)
    open_risers: BoolProperty(
        name="Open Risers", default=False, description="Treads only, no riser boards", update=updateNode)
    lap: FloatProperty(
        name="Lap", default=0.05, min=0.0, precision=3, subtype='DISTANCE',
        description="How far a precast block reaches under the block above", update=updateNode)

    status: StringProperty(default="")
    status_level: StringProperty(default="INFO")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Boundaries")
        self.inputs.new('SvVerticesSocket', "Riser Vertices")
        self.inputs.new('SvStringsSocket', "Riser Edges")
        self.inputs.new('SvVerticesSocket', "Path")
        self.inputs.new('SvStringsSocket', "Level Start").prop_name = 'level_start'
        self.inputs.new('SvStringsSocket', "Level End").prop_name = 'level_end'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Polygons")
        self.outputs.new('SvStringsSocket', "Rise")
        self.outputs.new('SvStringsSocket', "Goings")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'kind', expand=True)
        col = layout.column(align=True)
        if self.kind == 'CONCRETE':
            col.prop(self, 'waist')
        else:
            row = col.row(align=True)
            row.prop(self, 'toe', expand=True)
            if self.toe != 'SQUARE':
                col.prop(self, 'toe_size')
            col.prop(self, 'nosing')
            if self.kind == 'TIMBER':
                col.prop(self, 'tread_thickness')
                col.prop(self, 'open_risers')
                if not self.open_risers:
                    col.prop(self, 'riser_thickness')
            else:
                col.prop(self, 'lap')
        layout.prop(self, 'standard')
        for k, line in enumerate(self.status.split('\n') if self.status else []):
            icon = ('ERROR' if self.status_level == 'WARNING' else 'INFO') if k == 0 else 'BLANK1'
            layout.label(text=line, icon=icon)

    def set_status(self, text, level="INFO"):
        # plain StringProperties without update callbacks: setting them does not re-run process()
        if self.status != text:
            self.status = text
        if self.status_level != level:
            self.status_level = level

    def settings(self):
        return dict(waist=self.waist, toe=self.toe, toe_size=self.toe_size, nosing=self.nosing,
                    tread=self.tread_thickness, riser=self.riser_thickness,
                    risers=not self.open_risers, lap=self.lap)

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return
        need = ('Boundaries', 'Riser Vertices', 'Riser Edges', 'Path')
        if not all(self.inputs[n].is_linked for n in need):
            self.set_status("connect Boundaries, Riser Vertices, Riser Edges and Path", "WARNING")
            return

        inputs = self.inputs
        bounds_in = as_objects(inputs['Boundaries'].sv_get(), 4)
        rverts_in = as_objects(inputs['Riser Vertices'].sv_get(), 3)
        redges_in = as_objects(inputs['Riser Edges'].sv_get(), 3)
        path_in = as_objects(inputs['Path'].sv_get(), 3)
        start_in = per_object_value(inputs['Level Start'].sv_get())
        end_in = per_object_value(inputs['Level End'].sv_get())

        verts_out, faces_out, rise_out, goings_out, notes = [], [], [], [], []
        objects = list(zip(*match_long_repeat([bounds_in, rverts_in, redges_in, path_in, start_in, end_in])))
        for idx, (bounds, rverts, redges, path, z0, z1) in enumerate(objects):
            prefix = f"stair {idx}: " if len(objects) > 1 else ""
            try:
                flight = build_flight(bounds, rverts, redges, path, z0, z1)
                pieces = build(self.kind, flight, **self.settings())
            except StairError as err:
                self.set_status(f"{prefix}{err}", "WARNING")
                raise StairError(f"{prefix}{err}") from None
            notes += [prefix + n for n in check(flight, self.standard) + flight.messages]
            for verts, faces in pieces:
                verts_out.append(verts)
                faces_out.append(faces)
            rise_out.append([flight.rise])
            goings_out.append(flight.goings)

        if objects:
            first = rise_out[0][0]
            summary = f"{sum(len(g) + 1 for g in goings_out)} risers, rise {first * 1000:.0f} mm"
            if len(objects) == 1:
                g = goings_out[0]
                summary += f", going {min(g) * 1000:.0f}" + (f"-{max(g) * 1000:.0f}" if max(g) - min(g) > 5e-4 else "") + " mm"
            self.set_status("\n".join(notes + [summary]), "WARNING" if notes else "INFO")

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Polygons'].sv_set(faces_out)
        self.outputs['Rise'].sv_set(rise_out)
        self.outputs['Goings'].sv_set(goings_out)


def register():
    bpy.utils.register_class(SvStairsNode)


def unregister():
    bpy.utils.unregister_class(SvStairsNode)
