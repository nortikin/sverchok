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
from mathutils import Matrix
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, Vector_generate, match_long_repeat, enum_item as e)


class SvMatrixTrackToNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Align to Track & Up vectors
    Tooltip:  Construct a Matrix from arbitrary Track and Up vectors

    """

    bl_idname = 'SvMatrixTrackToNode'
    bl_label = 'Matrix Track To'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_TRACK_TO'

    TUA = ["X Y", "X Z", "Y X", "Y Z", "Z X", "Z Y"]
    tu_axes: EnumProperty(
        name="Track/Up Axes",
        description="Select which two of the XYZ axes to be the Track and Up axes",
        items=e(TUA), default=TUA[0], update=updateNode)

    normalize: BoolProperty(
        name="Normalize Vectors", description="Normalize the output X,Y,Z vectors",
        default=True, update=updateNode)

    origin: FloatVectorProperty(
        name='Location', description="The location component of the output matrix",
        default=(0, 0, 0), update=updateNode)

    scale: FloatVectorProperty(
        name='Scale', description="The scale component of the output matrix",
        default=(1, 1, 1), update=updateNode)

    vA: FloatVectorProperty(
        name='A', description="A direction",
        default=(1, 0, 0), update=updateNode)

    vB: FloatVectorProperty(
        name='B', description='B direction',
        default=(0, 1, 0), update=updateNode)
    flat_output: BoolProperty(
        name="Flat output",
        description="Flatten output by list-joining level 1",
        default=True,
        update=updateNode)
    TUM = ["A B", "A -B", "-A B", "-A -B", "B A", "B -A", "-B A", "-B -A"]
    tu_mapping: EnumProperty(
        name="Track/Up Mapping",
        description="Map the Track and Up vectors to one of the two inputs or their negatives",
        items=e(TUM), default=TUM[0], update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Location").prop_name = "origin"  # L
        self.inputs.new('SvVerticesSocket', "Scale").prop_name = "scale"  # S
        self.inputs.new('SvVerticesSocket', "A").prop_name = "vA"  # A
        self.inputs.new('SvVerticesSocket', "B").prop_name = "vB"  # B
        self.outputs.new('SvMatrixSocket', "Matrix")
        self.outputs.new('SvVerticesSocket', "X")
        self.outputs.new('SvVerticesSocket', "Y")
        self.outputs.new('SvVerticesSocket', "Z")

    def split_columns(self, panel, ratios, aligns):
        """
        Splits the given panel into columns based on the given set of ratios.
        e.g ratios = [1, 2, 1] or [.2, .3, .2] etc
        Note: The sum of all ratio numbers doesn't need to be normalized
        """
        col2 = panel
        cols = []
        ns = len(ratios) - 1  # number of splits
        for n in range(ns):
            n1 = ratios[n]  # size of the current column
            n2 = sum(ratios[n + 1:])  # size of all remaining columns
            p = n1 / (n1 + n2)  # percentage split of current vs remaning columns
            # print("n = ", n, " n1 = ", n1, " n2 = ", n2, " p = ", p)
            split = col2.split(factor=p, align=aligns[n])
            col1 = split.column(align=True)
            col2 = split.column(align=True)
            cols.append(col1)
        cols.append(col2)

        return cols

    def draw_buttons(self, context, layout):
        row = layout.column().row()
        cols = self.split_columns(row, [1, 1], [True, True])

        cols[0].prop(self, "tu_axes", text="")
        cols[1].prop(self, "tu_mapping", text="")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "normalize")
        layout.prop(self, "flat_output")

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "tu_axes")
        layout.prop_menu_enum(self, "tu_mapping")
        layout.prop(self, "normalize")
        layout.prop(self, "flat_output", text="Flat Output", expand=False)

    def orthogonalizeXY(self, X, Y):  # keep X, recalculate Z form X&Y then Y
        Z = X.cross(Y)
        Y = Z.cross(X)
        return X, Y, Z

    def orthogonalizeXZ(self, X, Z):  # keep X, recalculate Y form Z&X then Z
        Y = Z.cross(X)
        Z = X.cross(Y)
        return X, Y, Z

    def orthogonalizeYX(self, Y, X):  # keep Y, recalculate Z form X&Y then X
        Z = X.cross(Y)
        X = Y.cross(Z)
        return X, Y, Z

    def orthogonalizeYZ(self, Y, Z):  # keep Y, recalculate X form Y&Z then Z
        X = Y.cross(Z)
        Z = X.cross(Y)
        return X, Y, Z

    def orthogonalizeZX(self, Z, X):  # keep Z, recalculate Y form Z&X then X
        Y = Z.cross(X)
        X = Y.cross(Z)
        return X, Y, Z

    def orthogonalizeZY(self, Z, Y):  # keep Z, recalculate X form Y&Z then Y
        X = Y.cross(Z)
        Y = Z.cross(X)
        return X, Y, Z

    def orthogonalizer(self):
        order = self.tu_axes.replace(" ", "")
        orthogonalizer = eval("self.orthogonalize" + order)
        return lambda T, U: orthogonalizer(T, U)

    def matrix_track_to(self, params, mT, mU, orthogonalize, gates):
        x_list = []  # ortho-normal X vector list
        y_list = []  # ortho-normal Y vector list
        z_list = []  # ortho-normal Z vector list
        matrix_list = []
        print(len(params))
        for L, S, A, B in zip(*params):
            T = eval(mT)  # map T to one of A, B or its negative
            U = eval(mU)  # map U to one of A, B or its negative

            X, Y, Z = orthogonalize(T, U)

            if gates[4]:
                X.normalize()
                Y.normalize()
                Z.normalize()

            # prepare the Ortho-Normalized outputs
            if gates[1]:
                x_list.append([X.x, X.y, X.z])
            if gates[2]:
                y_list.append([Y.x, Y.y, Y.z])
            if gates[3]:
                z_list.append([Z.x, Z.y, Z.z])
            if gates[0]:
                # composite matrix: M = T * R * S (Tanslation x Rotation x Scale)
                m = [[X.x * S.x, Y.x * S.y, Z.x * S.z, L.x],
                     [X.y * S.x, Y.y * S.y, Z.y * S.z, L.y],
                     [X.z * S.x, Y.z * S.y, Z.z * S.z, L.z],
                     [0, 0, 0, 1]]

                matrix_list.append(Matrix(m))

        return matrix_list, x_list, y_list, z_list

    def process(self):
        outputs = self.outputs

        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists
        inputs = self.inputs
        params = match_long_repeat([Vector_generate(s.sv_get()) for s in inputs])
        orthogonalize = self.orthogonalizer()

        mT, mU = self.tu_mapping.split(" ")
        gates = [s.is_linked for s in outputs]
        gates.append(self.normalize)
        x_lists = []  # ortho-normal X vector list
        y_lists = []  # ortho-normal Y vector list
        z_lists = []  # ortho-normal Z vector list
        matrix_lists = []
        if self.flat_output:
            m_add, x_add, y_add, z_add = matrix_lists.extend,  x_lists.extend, y_lists.extend, z_lists.extend
        else:
            m_add, x_add, y_add, z_add = matrix_lists.append, x_lists.append, y_lists.append, z_lists.append
        for par in zip(*params):
            matrix_list, x_list, y_list, z_list = self.matrix_track_to(match_long_repeat(par), mT, mU, orthogonalize, gates)
            m_add(matrix_list)
            x_add([x_list])
            y_add(y_list)
            z_add(z_list)

        outputs["Matrix"].sv_set(matrix_lists)
        outputs["X"].sv_set(x_lists)
        outputs["Y"].sv_set(y_lists)
        outputs["Z"].sv_set(z_lists)

def register():
    bpy.utils.register_class(SvMatrixTrackToNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixTrackToNode)
