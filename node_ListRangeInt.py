import bpy
from node_s import *
from util import *
from bpy.props import IntProperty, EnumProperty, BoolProperty

'''
- range exclusive n
Start, stop, step. Like range()
Start, step, count

See class unit tests for behaviours

'''

def intRange( start=0, step=1, stop=1):
    '''
    slightly different behaviour: "lazy range"
    - step is always |step| (absolute)
    - step is converted to negative if stop is less than start
    '''
    if start == stop:
        return []
    step = max(step, 1)
    if stop < start:
        step *= -1
    return list(range(start, stop, step))

def countRange( start=0, step=1, count=10):
    count = max(count, 0)
    if count == 0:
        return []
    stop = (count*step) + start
    return list(range(start, stop, step))


class GenListRangeInt(Node, SverchCustomTreeNode):
    ''' Generator range list of ints '''
    bl_idname = 'GenListRangeIntNode'
    bl_label = 'List Range Int'
    bl_icon = 'OUTLINER_OB_EMPTY'

    start_ = IntProperty(
        name='start', description='start', default=0,
        options={'ANIMATABLE'}, update=updateNode)

    stop_ = IntProperty(
        name='stop', description='stop', default=10,
        options={'ANIMATABLE'}, update=updateNode)
    count_ = IntProperty(
        name='count', description='num items', default=10,
        options={'ANIMATABLE'}, update=updateNode)

    step_ = IntProperty(
        name='step', description='step', default=1,
        options={'ANIMATABLE'}, update=updateNode)

    current_mode = StringProperty(default="LAZYRANGE")

    modes = [
        ("LAZYRANGE", "Range", "Use python Range function", 1),
        ("COUNTRANGE", "Count", "Create range based on count", 2)
    ]

    def mode_change(self, context):

        # just because click doesn't mean we need to change mode
        mode = self.mode
        if mode == self.current_mode:
            return

        self.inputs[-1].prop_name = {'LAZYRANGE': 'stop_'}.get(mode, 'count_')

        self.current_mode = mode
        updateNode(self, context)

    mode = EnumProperty(items=modes, default='LAZYRANGE', update=mode_change)

    def init(self, context):
        self.inputs.new('StringsSocket', "Start").prop_name = 'start_'
        self.inputs.new('StringsSocket', "Step").prop_name = 'step_'
        self.inputs.new('StringsSocket', "Stop").prop_name = 'stop_'

        self.outputs.new('StringsSocket', "Range", "Range")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)

    func_dict ={'LAZYRANGE': intRange,
                'COUNTRANGE': countRange}
            
    def update(self):
        inputs = self.inputs
        outputs = self.outputs

        # outputs, end early.
        if not 'Range' in outputs or not outputs['Range'].links:
            return
        
        param=[inputs[i].sv_get()[0] for i in range(3)]
        f=self.func_dict[self.mode]
        out = [f(*args) for args in zip(*match_long_repeat(param))]
        outputs['Range'].sv_set(out)
                

def register():
    bpy.utils.register_class(GenListRangeInt)


def unregister():
    bpy.utils.unregister_class(GenListRangeInt)
