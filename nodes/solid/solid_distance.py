
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvSolidDistanceNode', 'Solid Distance', 'FreeCAD')
else:
    import bpy
    from sverchok.node_tree import SverchCustomTreeNode
    from bpy.props import EnumProperty
    from sverchok.data_structure import updateNode
    from sverchok.data_structure import match_long_repeat as mlr
    import Part
    from FreeCAD import Base

    class SvSolidDistanceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Closest point on Solid
        Tooltip: Closest point to a vector on a solid surface, accepts also solid faces and solid edges
        """
        bl_idname = 'SvSolidDistanceNode'
        bl_label = 'Solid Distance'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_POINTS_INSIDE_SOLID'
        solid_catergory = "Operators"

        modes = [
            ('Solid', 'Solid', '', 0),
            ('Face', 'Face', '', 1),
            ('Edge', 'Edge', '', 2),
            ('Vertex', 'Vertex', '', 3),

        ]
        def set_sockets(self,context):
            self.update_sockets()
            updateNode(self, context)

        def update_sockets(self):
            self.inputs['Solid'].hide_safe = self.mode != 'Solid'
            self.inputs['Solid Face'].hide_safe = self.mode != 'Face'
            self.inputs['Solid Edge'].hide_safe = self.mode != 'Edge'
            self.inputs['Solid B'].hide_safe = self.mode_b != 'Solid'
            self.inputs['Solid Face B'].hide_safe = self.mode_b != 'Face'
            self.inputs['Solid Edge B'].hide_safe = self.mode_b != 'Edge'


        mode: EnumProperty(
            name="Mode",
            description="Algorithm used for conversion",
            items=modes[:3], default="Solid",
            update=set_sockets)

        mode_b: EnumProperty(
            name="Mode",
            description="Algorithm used for conversion",
            items=modes, default="Solid",
            update=set_sockets)

        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.inputs.new('SvSurfaceSocket', "Solid Face")
            self.inputs.new('SvCurveSocket', "Solid Edge")
            self.inputs.new('SvSolidSocket', "Solid B")
            self.inputs.new('SvSurfaceSocket', "Solid Face B")
            self.inputs.new('SvCurveSocket', "Solid Edge B")
            self.inputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Distance")
            self.outputs.new('SvVerticesSocket', "Closest Point")
            self.outputs.new('SvStringsSocket', "Info")
            self.outputs.new('SvVerticesSocket', "Closest Point B")
            self.outputs.new('SvStringsSocket', "Info B")
            self.mode= "Solid"
            self.mode_b= "Solid"
            self.update_sockets()

        def draw_buttons(self, context, layout):
            row = layout.row(align=True)
            col = row.column(align=True)
            col.label(text='From')
            col.prop(self, "mode", text="")
            col = row.column(align=True)
            col.label(text='To')
            col.prop(self, "mode_b", text="")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return


            solids_in = self.inputs[self["mode"]].sv_get()
            objects_b = self.inputs[self["mode_b"] + 3].sv_get()
            # points = self.inputs[6].sv_get()


            distances_out = []
            closest_points_out = []
            infos_out = []
            closest_points_out_b = []
            infos_out_b = []
            for solid, object_b, in zip(*mlr([solids_in, objects_b])):
                distances = []
                closest_points = []
                infos = []
                closest_points_b = []
                infos_b = []

                if self.mode == 'Solid':
                    if isinstance(solid, Part.Solid):
                        shape = solid.OuterShell
                    else:
                        shape = solid
                elif self.mode == 'Face':
                    shape = solid.face
                else:
                    shape = solid.edge

                if self.mode_b == 'Vertex':
                    for v in object_b:
                        vertex = Part.Vertex(Base.Vector(v))

                        d = shape.distToShape(vertex)
                        distances.append(d[0])
                        closest_points.append(d[1][0][0][:])
                        infos.append(d[2][0][0:3])
                else:
                    if self.mode_b == "Solid":
                        if isinstance(solid, Part.Solid):
                            shape_b = object_b.OuterShell
                        else:
                            shape_b = object_b
                    elif self.mode == 'Face':
                        shape_b = solid.face
                    else:
                        shape_b = solid.edge
                    d = shape.distToShape(shape_b)
                    distances.append(d[0])
                    closest_points.append(d[1][0][0][:])
                    infos.append(d[2][0][0:3])
                    closest_points_b.append(d[1][0][1][:])
                    infos_b.append(d[2][0][3:])
                    closest_points_out_b.append(closest_points_b)
                    infos_out_b.append(infos_b)


                distances_out.append(distances)
                closest_points_out.append(closest_points)
                infos_out.append(infos)


            self.outputs['Distance'].sv_set(distances_out)
            self.outputs['Closest Point'].sv_set(closest_points_out)
            self.outputs['Info'].sv_set(infos_out)
            self.outputs['Closest Point B'].sv_set(closest_points_out_b)
            self.outputs['Info B'].sv_set(infos_out_b)



def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidDistanceNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidDistanceNode)
