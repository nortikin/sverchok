# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty, BoolVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, map_recursive, unzip_dict_recursive, throttle_and_update_node
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvSolidBoundBoxNode', 'Solid Bounding Box', 'FreeCAD')
else:
    from FreeCAD import Base
    import Part

class SvSolidBoundBoxNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Solid Bound Box
    Tooltip: Calculate bounding box of a Solid object
    """
    bl_idname = 'SvSolidBoundBoxNode'
    bl_label = 'Solid Bounding Box'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_BOUNDING_BOX'
    solid_catergory = "Operators"

    def _get_socket(self, axis, key):
        return self.outputs[axis + key]

    @throttle_and_update_node
    def update_sockets(self, context):
        for axis_idx, axis in enumerate(['X', 'Y', 'Z']):
            self._get_socket(axis, 'Min').hide_safe = not self.min_list[axis_idx]
            self._get_socket(axis, 'Max').hide_safe = not self.max_list[axis_idx]
            self._get_socket(axis, 'Size').hide_safe = not self.size_list[axis_idx]

    min_list: BoolVectorProperty(
        name='Min', description="Show Minimum values sockets", size=3, update=update_sockets)
    max_list: BoolVectorProperty(
        name='Max', description="Show Maximun values sockets", size=3, update=update_sockets)
    size_list: BoolVectorProperty(
        name='Size', description="Show Size values sockets", size=3, update=update_sockets)

    optimal : BoolProperty(
            name = "Optimal",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        # Returns weird results, hide for now
        #layout.prop(self, 'optimal')

        col = layout.column(align=True)
        for key, prop in zip(['Min','Max','Size'], ['min_list', 'max_list', 'size_list']):
            row = col.row(align=True)
            row.label(text=key)
            for axis_idx, axis in enumerate(['X', 'Y', 'Z']):
                row.prop(self, prop, index=axis_idx, text=axis, toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', 'Solid')
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvVerticesSocket', 'Center')

        for key in ['Min','Max','Size']:
            for axis in ['X', 'Y', 'Z']:
                self.outputs.new('SvStringsSocket', axis+key)

        self.update_sockets(context)

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        solids_in = self.inputs['Solid'].sv_get()

        def calc_bbox(solid):
            if self.optimal:
                return solid.optimalBoundingBox(False)
            else:
                return solid.BoundBox

        def get_verts(box):
            pts = [box.getPoint(i) for i in range(8)]
            return [(p.x, p.y, p.z) for p in pts]

        def get_center(box):
            p = box.Center
            return (p.x, p.y, p.z)
        
        def to_dict(box):
            return dict(XMin=[box.XMin],
                    XMax=[box.XMax],
                    XSize=[box.XLength],
                    YMin=[box.YMin],
                    YMax=[box.YMax],
                    YSize=[box.YLength],
                    ZMin=[box.ZMin],
                    ZMax=[box.ZMax],
                    ZSize=[box.ZLength],
                    Center=get_center(box),
                    Vertices = get_verts(box))

        results = map_recursive(calc_bbox, solids_in, data_types=(Part.Shape,))
        bboxes = unzip_dict_recursive(results, item_type=Base.BoundBox, to_dict=to_dict)

        for key in bboxes:
            self.outputs[key].sv_set(bboxes[key])

def register():
    bpy.utils.register_class(SvSolidBoundBoxNode)

def unregister():
    bpy.utils.unregister_class(SvSolidBoundBoxNode)

