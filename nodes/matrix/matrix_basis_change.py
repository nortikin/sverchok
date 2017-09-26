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
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty
from mathutils import Vector
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_repeat, enum_item as e)


class SvMatrixBasisChangeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Construct a Matrix from Tangent, Binormal and Normal vectors '''
    bl_idname = 'SvMatrixBasisChangeNode'
    bl_label = 'Matrix Basis Change'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def update_mapping(self, context):
        ''' Set the mapping of the third XYZ axis to its corresponding orthonormal TBN vector '''
        v1, v2, v3 = [v for v in self.orthogonalizing_order.replace(" ", "")]

        T = Vector([1, 0, 0])
        B = Vector([0, 1, 0])
        N = Vector([0, 0, 1])

        a = {}
        a[v1] = eval(eval("self." + v1))
        a[v2] = eval(eval("self." + v2))
        a[v3] = eval(eval("self." + v3))

        if v3 == "X":
            m3 = a["Y"].cross(a["Z"])
        elif v3 == "Y":
            m3 = a["Z"].cross(a["X"])
        else:  # Z
            m3 = a["X"].cross(a["Y"])

        b = {"T":  T, "-T": -T, "B":  B, "-B": -B, "N": N, "-N": -N}
        l3 = "N"
        for label, vector in b.items():
            if m3 == vector:
                l3 = label
                break

        setattr(self, v3, l3)

    def update_order(self, context):
        if self.syncing:
            return

        self.syncing = True  # disable recursive update callback
        self.update_mapping(context)
        self.syncing = False  # enable update callback
        updateNode(self, context)

    OO = ["X Y Z", "X Z Y", "Y X Z", "Y Z X", "Z X Y", "Z Y X"]
    orthogonalizing_order = EnumProperty(
        name="Orthogonalizing Order",
        description="The priority order in which the XYZ vectors are orthogonalized",
        items=e(OO), default=OO[0], update=update_order)

    normalize = BoolProperty(
        name="Normalize Vectors",
        default=True, update=updateNode)

    origin = FloatVectorProperty(
        name='Location', description="Origin location of the coordinate system",
        default=(0, 0, 0), update=updateNode)

    tangent = FloatVectorProperty(
        name='Tangent', description="T : Tangent direction",
        default=(1, 0, 0), update=updateNode)

    binormal = FloatVectorProperty(
        name='Binormal', description='B : Binormal direction',
        default=(0, 1, 0), update=updateNode)

    normal = FloatVectorProperty(
        name='Normal', description='N : Normal direction',
        default=(0, 0, 1), update=updateNode)

    TBN = ["T", "B", "N", "-T", "-B", "-N"]
    X = EnumProperty(name="X", items=e(TBN), default=TBN[0], update=update_order)
    Y = EnumProperty(name="Y", items=e(TBN), default=TBN[1], update=update_order)
    Z = EnumProperty(name="Z", items=e(TBN), default=TBN[2], update=update_order)

    syncing = BoolProperty(
        name='Syncing', description='Syncing flag', default=False)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Location").prop_name = "origin"  # V
        self.inputs.new('VerticesSocket', "T : Tangent").prop_name = "tangent"  # T
        self.inputs.new('VerticesSocket', "B : Binormal").prop_name = "binormal"  # B
        self.inputs.new('VerticesSocket', "N : Normal").prop_name = "normal"  # N
        self.outputs.new('MatrixSocket', "Matrix")
        self.outputs.new('VerticesSocket', "X")
        self.outputs.new('VerticesSocket', "Y")
        self.outputs.new('VerticesSocket', "Z")

    def draw_buttons1(self, context, layout):
        layout.prop(self, "normalize")
        box = layout.box()
        box.prop(self, "orthogonalizing_order", "")
        col = box.column(align=True)
        for p in self.orthogonalizing_order:
            row = col.row(align=True)
            row.prop(self, p)
        row.enabled = False

    def draw_buttons2(self, context, layout):
        layout.prop(self, "normalize")
        box = layout.box()
        col = box.column(align=True)
        col.prop(self, "orthogonalizing_order", "")

        row = col.row(align=True)
        for p in self.orthogonalizing_order.replace(" ", ""):
            col1 = row.column(align=True)
            col1.prop(self, p, text="")

        # disable last mapping as it is generated automatically via orthogonalization
        col1.enabled = False

        row = col.row(align=True)
        for p in self.orthogonalizing_order.replace(" ", ""):
            col1 = row.column(align=True)
            col1.label(p)

    def draw_buttons(self, context, layout):
        self.draw_buttons2(context, layout)

    def orthogonalizeXYZ(self, X, Y, Z):  # keep X, recalculate Z form X&Y then Y
        Z = X.cross(Y)
        Y = Z.cross(X)
        return X, Y, Z

    def orthogonalizeXZY(self, X, Y, Z):  # keep X, recalculate Y form Z&X then Z
        Y = Z.cross(X)
        Z = X.cross(Y)
        return X, Y, Z

    def orthogonalizeYXZ(self, X, Y, Z):  # keep Y, recalculate Z form X&Y then X
        Z = X.cross(Y)
        X = Y.cross(Z)
        return X, Y, Z

    def orthogonalizeYZX(self, X, Y, Z):  # keep Y, recalculate X form Y&Z then Z
        X = Y.cross(Z)
        Z = X.cross(Y)
        return X, Y, Z

    def orthogonalizeZXY(self, X, Y, Z):  # keep Z, recalculate Y form Z&X then X
        Y = Z.cross(X)
        X = Y.cross(Z)
        return X, Y, Z

    def orthogonalizeZYX(self, X, Y, Z):  # keep Z, recalculate X form Y&Z then Y
        X = Y.cross(Z)
        Y = Z.cross(X)
        return X, Y, Z

    def orthogonalizer(self):
        if self.orthogonalizing_order == "X Y Z":
            orthogonalizer = lambda X, Y, Z: self.orthogonalizeXYZ(X, Y, Z)
        elif self.orthogonalizing_order == "X Z Y":
            orthogonalizer = lambda X, Y, Z: self.orthogonalizeXZY(X, Y, Z)
        elif self.orthogonalizing_order == "Y X Z":
            orthogonalizer = lambda X, Y, Z: self.orthogonalizeYXZ(X, Y, Z)
        elif self.orthogonalizing_order == "Y Z X":
            orthogonalizer = lambda X, Y, Z: self.orthogonalizeYZX(X, Y, Z)
        elif self.orthogonalizing_order == "Z X Y":
            orthogonalizer = lambda X, Y, Z: self.orthogonalizeZXY(X, Y, Z)
        elif self.orthogonalizing_order == "Z Y X":
            orthogonalizer = lambda X, Y, Z: self.orthogonalizeZYX(X, Y, Z)
        else:  # default is XYZ (fall through case)
            orthogonalizer = lambda X, Y, Z: self.orthogonalizeXYZ(X, Y, Z)

        return orthogonalizer

    def process(self):
        outputs = self.outputs

        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists
        inputs = self.inputs
        input_locations = inputs["Location"].sv_get()[0]
        input_tangents = inputs["T : Tangent"].sv_get()[0]
        input_binormals = inputs["B : Binormal"].sv_get()[0]
        input_normals = inputs["N : Normal"].sv_get()[0]

        locations = [Vector(i) for i in input_locations]
        tangents = [Vector(i) for i in input_tangents]
        binormals = [Vector(i) for i in input_binormals]
        normals = [Vector(i) for i in input_normals]

        params = match_long_repeat([locations, tangents, binormals, normals])

        orthogonalize = self.orthogonalizer()

        xList = []  # ortho-normal X vector list
        yList = []  # ortho-normal Y vector list
        zList = []  # ortho-normal Z vector list
        matrixList = []
        for V, T, B, N in zip(*params):
            X = eval(self.X)  # map X to one of T, B, N or its negative
            Y = eval(self.Y)  # map Y to one of T, B, N or its negative
            Z = eval(self.Z)  # map Z to one of T, B, N or its negative

            X, Y, Z = orthogonalize(X, Y, Z)

            if self.normalize:
                X.normalize()
                Y.normalize()
                Z.normalize()

            # prepare the Ortho-Normalized outputs
            if outputs["X"].is_linked:
                xList.append([X.x, X.y, X.z])
            if outputs["Y"].is_linked:
                yList.append([Y.x, Y.y, Y.z])
            if outputs["Z"].is_linked:
                zList.append([Z.x, Z.y, Z.z])

            m = [[X.x, Y.x, Z.x, V.x], [X.y, Y.y, Z.y, V.y], [X.z, Y.z, Z.z, V.z], [0, 0, 0, 1]]

            matrixList.append(m)

        outputs["Matrix"].sv_set(matrixList)
        outputs["X"].sv_set([xList])
        outputs["Y"].sv_set([yList])
        outputs["Z"].sv_set([zList])


def register():
    bpy.utils.register_class(SvMatrixBasisChangeNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixBasisChangeNode)
