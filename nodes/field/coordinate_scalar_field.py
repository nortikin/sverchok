
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from sverchok.utils.field.scalar import SvCoordinateScalarField


class SvCoordScalarFieldNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Coordinate Scalar Field
    Tooltip: Generate scalar field which equals one of point coordinates
    """
    bl_idname = 'SvCoordScalarFieldNode'
    bl_label = 'Coordinate Scalar Field'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POINT_DISTANCE_FIELD'

    coordinates = [
            ('X', "X", "Cartesian X", 0),
            ('Y', "Y", "Cartesian Y", 1),
            ('Z', "Z", "Cartesian or cylindrical Z", 2),
            ('CYL_RHO', "Rho - Cylindrical", "Cylindrical Rho", 3),
            ('PHI', "Phi", "Cylindrical or spherical Phi", 4),
            ('SPH_RHO', "Rho - Spherical", "Spherical Rho", 5),
            ('SPH_THETA', "Theta - Spherical", "Spherical Theta", 6)
        ]

    coordinate : EnumProperty(
            name = "Coordinate",
            items = coordinates,
            default = 'X',
            update = updateNode)

    def sv_init(self, context):
        self.outputs.new('SvScalarFieldSocket', "Field")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'coordinate', text='')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        field = SvCoordinateScalarField(self.coordinate)
        self.outputs['Field'].sv_set([field])

def register():
    bpy.utils.register_class(SvCoordScalarFieldNode)

def unregister():
    bpy.utils.unregister_class(SvCoordScalarFieldNode)
