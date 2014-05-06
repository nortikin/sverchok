from node_s import *
from util import *
from mathutils import Vector, kdtree
import bpy

# documentation/blender_python_api_2_70_release/mathutils.kdtree.html


class SvKDTreeEdgesNode(Node, SverchCustomTreeNode):

    bl_idname = 'SvKDTreeEdgesNode'
    bl_label = 'Kdtree Edges'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mindist = bpy.props.FloatProperty(
        name='mindist', description='Minimum dist',
        default=0.1, options={'ANIMATABLE'}, update=updateNode)

    maxdist = bpy.props.FloatProperty(
        name='maxdist', description='Maximum dist',
        default=2.0, options={'ANIMATABLE'}, update=updateNode)

    maxNum = bpy.props.IntProperty(
        name='maxNum', description='max edge count',
        default=4, min=1, options={'ANIMATABLE'}, update=updateNode)

    skip = bpy.props.IntProperty(
        name='skip', description='skip first n',
        default=0, min=0, options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'Verts', 'Verts')
        self.inputs.new('StringsSocket', 'mindist', 'mindist').prop_name = 'mindist'
        self.inputs.new('StringsSocket', 'maxdist', 'maxdist').prop_name = 'maxdist'
        self.inputs.new('StringsSocket', 'maxNum', 'maxNum').prop_name = 'maxNum'
        self.inputs.new('StringsSocket', 'skip', 'skip').prop_name = 'skip'

        self.outputs.new('StringsSocket', 'Edges', 'Edges')

    def update(self):
        inputs = self.inputs
        outputs = self.outputs

        try:
            verts = SvGetSocketAnyType(self, inputs['Verts'])[0]
            linked = outputs[0].links
        except (IndexError, KeyError) as e:
            return

        optional_sockets = [
            ['mindist', self.mindist, float],
            ['maxdist', self.maxdist, float],
            ['maxNum', self.maxNum, int],
            ['skip', self.skip, int]]

        socket_inputs = []
        for s, s_default_value, dtype in optional_sockets:
            if s in inputs and inputs[s].links:
                sock_input = dtype(SvGetSocketAnyType(self, inputs[s])[0][0])
            else:
                sock_input = s_default_value
            socket_inputs.append(sock_input)

        self.run_kdtree(verts, socket_inputs)

    def run_kdtree(self, verts, socket_inputs):
        mindist, maxdist, maxNum, skip = socket_inputs

        # make kdtree
        # documentation/blender_python_api_2_70_release/mathutils.kdtree.html
        size = len(verts)
        kd = mathutils.kdtree.KDTree(size)

        for i, vtx in enumerate(verts):
            kd.insert(Vector(vtx), i)
        kd.balance()

        # set minimum values
        maxNum = max(maxNum, 1)
        skip = max(skip, 0)

        # makes edges
        e = set()
        mcount = 0
        for i, vtx in enumerate(verts):
            num_edges = 0
            for (co, index, dist) in kd.find_range(vtx, maxdist):
                if (dist <= mindist) or (i == index):
                    continue
                if (num_edges > maxNum):
                    # continue
                    break
                if num_edges <= skip:
                    num_edges += 1
                    continue
                e.add(tuple(sorted([i, index])))
                mcount += 1
                num_edges += 1

        print(len(e), 'vs', mcount)

        SvSetSocketAnyType(self, 'Edges', [list(e)])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvKDTreeEdgesNode)


def unregister():
    bpy.utils.unregister_class(SvKDTreeEdgesNode)
