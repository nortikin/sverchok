import bpy
from bpy.props import StringProperty

from sverchok.node_tree import SverchCustomTreeNode, StringsSocket
from sverchok.data_structure import SvGetSocketAnyType

class EvalNode(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'EvalNode'
    bl_label = 'Eval'

    # Callbacks
    def update_value(self, context):
        self.process_node(context)

    # Properties
    x = StringProperty(name='x',
                       description='Input String',
                       default='')

    eval_string = StringProperty(name='eval',
                                 default='x')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'eval_string', text='')

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'x', 'x').prop_name = 'x'
        self.outputs.new('StringsSocket', 'out', 'out')

    def process(self):
        x = None
        if self.inputs['x'].is_linked:
            x = SvGetSocketAnyType(self, self.inputs['x'])

        if not x:
            return

        if self.outputs['out'].is_linked:
            self.outputs['out'].sv_set(eval(self.eval_string))

def register():
    bpy.utils.register_class(EvalNode)

def unregister():
    bpy.utils.unregister_class(EvalNode)