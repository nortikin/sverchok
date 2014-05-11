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

    had_links = BoolProperty(default=False)
    current_mode = StringProperty(default="LAZYRANGE")

    modes = [
        ("LAZYRANGE", "Range", "Use python Range function", 1),
        ("COUNTRANGE", "Count", "Create range based on count", 2)
    ]

    def mode_change(self, context):

        # print(dir(context))
        # print(dir(self))

        # just because click doesn't mean we need to change mode
        mode = self.mode
        if mode == self.current_mode:
            return

        inputs = self.inputs
        outputs = self.outputs

        # find if input socket three has any input from another node,
        # if it does, as a nicety we keep track of it and reconnect that node
        # into the changed socket. manually disconnecting is often less work
        # than trying to find out where a connection came from.
        links = inputs[2].links
        if links:
            self.had_links = True
            link = links[0]
            node_from = link.from_node
            socket_from = link.from_socket
        else:
            self.had_links = False

        # now disconnect by removing
        outputs.remove(inputs[-1])

        if mode == 'LAZYRANGE':
            inputs.new('StringsSocket', "Stop", "Stop").prop_name = 'stop_'
        else:
            inputs.new('StringsSocket', "Count", "Count").prop_name = 'count_'

        if self.had_links:
            ng = self.id_data
            ng.links.new(socket_from, inputs[2])

        self.current_mode = mode

    mode = EnumProperty(items=modes, default='LAZYRANGE', update=mode_change)

    def init(self, context):
        self.inputs.new('StringsSocket', "Start", "Start").prop_name = 'start_'
        self.inputs.new('StringsSocket', "Step", "Step").prop_name = 'step_'
        self.inputs.new('StringsSocket', "Stop", "Stop").prop_name = 'stop_'

        self.outputs.new('StringsSocket', "Range", "Range").prop_name = 'range_'

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)

    def update(self):
        inputs = self.inputs
        outputs = self.outputs

        # outputs, end early.
        if not 'Range' in outputs or not (len(outputs['Range'].links) > 0):
            return

        # inputs, both modes use these
        if 'Start' in inputs and inputs['Start'].links:
            tmp = SvGetSocketAnyType(self, inputs['Start'])
            Start = tmp[0][0]
            # Start = inputs['Start'].sv_get()
        else:
            Start = self.start_

        if 'Step' in inputs and inputs['Step'].links:
            tmp = SvGetSocketAnyType(self, inputs['Step'])
            Step = tmp[0][0]
            # Step = inputs['Step'].sv_get()
        else:
            Step = self.step_

        # mode dependant stuff
        if self.mode == 'LAZYRANGE':
            if 'Stop' in inputs and inputs['Stop'].links:
                tmp = SvGetSocketAnyType(self, inputs['Stop'])
                Stop = tmp[0][0]
                #Stop = inputs['Stop'].sv_get()
            else:
                Stop = self.stop_

            range_ = self.intRange(Start, Stop, Step)

        # mode dependant stuff
        elif self.mode == 'COUNTRANGE':
            if 'Count' in inputs and inputs['Count'].links:
                tmp = SvGetSocketAnyType(self, inputs['Count'])
                Count = tmp[0][0]
                # Count = inputs['Count'].sv_get()
            else:
                Count = self.count_
            range_ = self.countRange(Start, Step, Count)

        # print(range_)
        SvSetSocketAnyType(self, 'Range', [range_])

    def intRange(self, start=0, stop=1, step=1):
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

    def countRange(self, start=0, step=1, count=10):
        count = max(count, 0)
        if count == 0:
            return []

        stop = (count*step) + start
        return list(range(start, stop, step))

    def print_tests(self, tests):
        for i in tests:
            print(i, ':', eval(i))

    def unit_tests(self):
        # test intRange "lazy range"
        a = 'self.intRange(20, 40, 2)'
        b = 'self.intRange(20, 30, 1)'
        c = 'sefl.intRange(-4, 4, 1)'
        d = 'self.intRange(5, -4, 1)'
        e = 'self.intRange(20, 30, -1)'
        self.print_tests([a, b, c, d, e])

        # test intRange "lazy range"
        a = 'self.countRange(20, 1, 3)'
        b = 'self.countRange(20, 2, 8)'
        c = 'self.countRange(-4, -1, 7)'
        d = 'self.countRange(5, -4, 1)'
        e = 'self.countRange(20, 30, -1)'
        self.print_tests([a, b, c, d, e])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(GenListRangeInt)


def unregister():
    bpy.utils.unregister_class(GenListRangeInt)
