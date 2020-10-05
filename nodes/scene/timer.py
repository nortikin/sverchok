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
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, EnumProperty, CollectionProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.utils.modules.statistics_functions import *
from sverchok.utils.logging import debug

TIMER_STATUS_STOPPED = "STOPPED"
TIMER_STATUS_STARTED = "STARTED"
TIMER_STATUS_PAUSED = "PAUSED"
TIMER_STATUS_EXPIRED = "EXPIRED"

timer_status_items = [(TIMER_STATUS_STOPPED, "Stopped", "", 1),
                      (TIMER_STATUS_STARTED, "Started", "", 2),
                      (TIMER_STATUS_PAUSED, "Paused", "", 3),
                      (TIMER_STATUS_EXPIRED, "Expired", "", 4)]

TIMER_OPERATION_STOP = 0
TIMER_OPERATION_START = 1
TIMER_OPERATION_PAUSE = 2
TIMER_OPERATION_RESET = 3
TIMER_OPERATION_EXPIRE = 4
TIMER_OPERATION_LOOP_BACKWARD = 5
TIMER_OPERATION_LOOP_FORWARDS = 6

EPSILON = 1e-10  # used to avoid division by zero


class SvTimerPropertyGroup(bpy.types.PropertyGroup):
    ''' Timer class '''
    timer_id: IntProperty(
        name="Timer ID",
        description="ID of the timer entry",
        default=0)

    last_timer_status: EnumProperty(
        name="Last Timer Status", description="Timer status before it expired",
        items=timer_status_items,
        default=TIMER_STATUS_STOPPED)

    timer_status: EnumProperty(
        name="Timer Status", description="Timer Status",
        items=timer_status_items,
        default=TIMER_STATUS_STOPPED)

    timer_time: FloatProperty(
        name="Time", description="Elapsed time",
        default=0.0)

    timer_duration: FloatProperty(
        name="Duration", description="Time after which the timer loops or expires",
        default=10.0, min=0.0)

    timer_speed: FloatProperty(
        name="Speed", description="Time speed as a multiplier of playback time",
        default=1.0)

    timer_loops: IntProperty(
        name="Loops", description="Number of loops before expiring (0 = no loop)",
        default=0, min=0)

    timer_loop_count: IntProperty(
        name="Loop Count", description="Number of realized loops",
        default=0, min=0)

    timer_last_operation: IntProperty(
        name="Last Operation", description="Last external control operation executed",
        default=0)

    timer_start_frame: IntProperty(
        name="Start Frame", description="Frame at which timer was started",
        default=0)

    timer_last_frame: IntProperty(
        name="Last Frame", description="The last frame the timer was updated",
        default=0)

    def id(self):
        return self.timer_id

    def status(self):
        return self.timer_status

    def elapsed_time(self, normalized=False):
        if normalized:
            return self.timer_time / self.timer_duration
        else:
            return self.timer_time

    def remaining_time(self, normalized=False):
        remaining_time = max(0, self.timer_duration - self.timer_time)
        if normalized:
            return remaining_time / self.timer_duration
        else:
            return remaining_time

    def expired(self):
        return self.timer_status == TIMER_STATUS_EXPIRED

    def loop_count(self):
        return self.timer_loop_count

    def stop(self):
        debug("* Timer {0}: STOP".format(self.timer_id))
        self.timer_time = 0
        self.timer_loop_count = 0
        self.timer_status = TIMER_STATUS_STOPPED
        self.last_timer_status = TIMER_STATUS_STOPPED

    def start(self):
        debug("* Timer {0}: START".format(self.timer_id))
        if self.timer_status in [TIMER_STATUS_STOPPED, TIMER_STATUS_EXPIRED]:
            debug("starting from zero")
            self.timer_time = 0
            self.timer_start_frame = bpy.context.scene.frame_current
            self.timer_loop_count = 0
        self.timer_status = TIMER_STATUS_STARTED
        self.last_timer_status = TIMER_STATUS_STARTED

    def pause(self):
        debug("* Timer {0}: PAUSE".format(self.timer_id))
        if self.timer_status == TIMER_STATUS_STARTED:
            self.timer_status = TIMER_STATUS_PAUSED

    def reset(self):
        debug("* Timer {0}: RESET".format(self.timer_id))
        self.timer_status = TIMER_STATUS_STOPPED
        self.timer_time = 0
        self.timer_loop_count = 0

    def expire(self):
        debug("* Timer {0}: EXPIRE".format(self.timer_id))
        self.timer_status = TIMER_STATUS_EXPIRED
        self.timer_time = self.timer_duration
        self.timer_loop_count = self.timer_loops

    def loop_backward(self):
        debug("* Timer {0}: LOOP BACKWARD".format(self.timer_id))
        if self.timer_loop_count == 0:  # first loop ?
            self.last_timer_status = self.timer_status
            self.timer_status = TIMER_STATUS_STOPPED
            self.timer_time = 0
        else:  # not the first loop
            if self.timer_status == TIMER_STATUS_EXPIRED:
                self.timer_status = TIMER_STATUS_PAUSED

            if self.timer_time > 0:  # has some time in this loop? => reset to 0
                self.timer_time = 0
            else:  # time already reset to 0 ? => wrap around to previous loop
                self.timer_time = self.timer_duration
                self.timer_loop_count -= 1

    def loop_forward(self):
        debug("* Timer {0}: LOOP FORWARD".format(self.timer_id))
        if self.timer_loop_count == self.timer_loops:  # last loop ?
            self.last_timer_status = self.timer_status
            self.timer_status = TIMER_STATUS_EXPIRED
            self.timer_time = self.timer_duration
        else:  # not the last loop
            if self.timer_status == TIMER_STATUS_STOPPED:
                self.timer_status = TIMER_STATUS_PAUSED

            if self.timer_time < self.timer_duration:  # has some time in this loop? => reset to duration
                self.timer_time = self.timer_duration
            else:  # time already reset to duration ? => wrap around to next loop
                self.timer_time = 0
                self.timer_loop_count += 1

    def execute_operation(self, operation):
        if self.timer_last_operation != operation:
            self.timer_last_operation = operation

            if operation == TIMER_OPERATION_STOP:
                self.stop()

            elif operation == TIMER_OPERATION_START:
                self.start()

            elif operation == TIMER_OPERATION_PAUSE:
                self.pause()

            elif operation == TIMER_OPERATION_RESET:
                self.reset()

            elif operation == TIMER_OPERATION_EXPIRE:
                self.expire()

            elif operation == TIMER_OPERATION_LOOP_BACKWARD:
                self.loop_backward()

            elif operation == TIMER_OPERATION_LOOP_FORWARDS:
                self.loop_forward()

    def scrub_time(self, time):  # used externally to set time by slider scrubbing
        debug("scrub_time: {0}".format(time))
        if time == 0:
            self.loop_backward()

        elif time == self.timer_duration:
            self.loop_forward()

        else:  # time in between 0 and duration
            if self.timer_status == TIMER_STATUS_STOPPED:
                self.timer_status = TIMER_STATUS_PAUSED

            elif self.timer_status == TIMER_STATUS_EXPIRED:
                self.timer_status = TIMER_STATUS_PAUSED

        self.timer_time = time

    def update_time(self, loops, speed, duration, operation, absolute, sticky):
        ''' Update timer's time (called from the node's update loop) '''
        # debug("Timer {0}: UPDATE with loops = {1}, speed = {2}, duration = {3}, operation = {4}".format(self.timer_id, loops, speed, duration, operation))

        self.timer_loops = loops
        self.timer_speed = speed
        self.timer_duration = duration

        old_frame = self.timer_last_frame
        new_frame = bpy.context.scene.frame_current
        self.timer_last_frame = new_frame

        # execute external operation (this can change the timer status)
        self.execute_operation(operation)

        fps = bpy.context.scene.render.fps

        # update the time if the timer is STARTED
        if self.timer_status == TIMER_STATUS_STARTED:
            if absolute:  # update based on ABSOLUTE frame difference
                self.timer_time = (new_frame - self.timer_start_frame) / fps * self.timer_speed

            else:  # update based on RELATIVE frame difference
                delta_time = (new_frame - old_frame) / fps * self.timer_speed
                # debug("timer time = {0}".format(self.timer_time))
                # debug("timer delta = {0}".format(delta_time))
                self.timer_time += delta_time

            # time is out of range at either ends ? => check for looping
            if self.timer_time < 0:
                if self.timer_loops:  # looping ?
                    if self.timer_loop_count == 0:  # at the first loop => stop
                        # debug("start < looping = 0")
                        self.timer_time = 0
                        self.timer_status = TIMER_STATUS_STOPPED
                        self.last_timer_status = TIMER_STATUS_STARTED
                    else:  # not at the first loop => wrap around to previous loop
                        # debug("start < looping > 0")
                        self.timer_time = self.timer_time % self.timer_duration
                        self.timer_loop_count -= 1

                else:  # not looping => stop ?
                    # debug("start < NO looping")
                    self.timer_time = 0
                    self.timer_status = TIMER_STATUS_STOPPED
                    self.last_timer_status = TIMER_STATUS_STARTED

            elif self.timer_time > self.timer_duration:
                if self.timer_loops:  # looping ?
                    if self.timer_loop_count == self.timer_loops:  # at the last loop => expire
                        # debug("start >= looping = N")
                        self.timer_time = self.timer_duration
                        self.timer_status = TIMER_STATUS_EXPIRED
                        self.last_timer_status = TIMER_STATUS_STARTED

                    else:  # not at the last loop => wrap around to next loop
                        # debug("start >= looping < N")
                        self.timer_time = self.timer_time % self.timer_duration
                        self.timer_loop_count += 1

                else:  # not looping => expire ?
                    # debug("start >= NO looping")
                    self.timer_time = self.timer_duration
                    self.timer_status = TIMER_STATUS_EXPIRED
                    self.last_timer_status = TIMER_STATUS_STARTED

        elif self.timer_status == TIMER_STATUS_STOPPED and not sticky:
            delta_time = (new_frame - old_frame) / fps * self.timer_speed
            if delta_time > 0:
                self.timer_status = self.last_timer_status

        elif self.timer_status == TIMER_STATUS_EXPIRED and not sticky:
            delta_time = (new_frame - old_frame) / fps * self.timer_speed
            if delta_time < 0:
                self.timer_status = self.last_timer_status

        # keep the time within range
        self.timer_time = max(0, min(self.timer_time, self.timer_duration))

        # debug("Timer {0}: Status = {1}, Elapsed Time = {2}, Remaining Time = {3}, Expired = {4}".format(self.id(), self.status(), self.elapsed_time(), self.remaining_time(), self.expired()))


class SvTimerOperatorCallback(bpy.types.Operator):
    ''' Timer Operation (Start, Stop, Pause, Reset, Expire) '''
    bl_idname = "nodes.sv_timer_callback"
    bl_label = "Sv Ops Timer callback"

    function_name: StringProperty()  # what function to call

    def execute(self, context):
        n = context.node
        getattr(n, self.function_name)(context)
        return {"FINISHED"}


class SvTimerNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    """
    Triggers: Timer, Elapse
    Tooltip: Manage elapsed time via Start, Stop, Pause, Reset, Expire operations.
    """
    bl_idname = 'SvTimerNode'
    bl_label = 'Timer'
    bl_icon = 'PREVIEW_RANGE'

    timers: CollectionProperty(name="Timers", type=SvTimerPropertyGroup)

    def update_time_slider(self, context):
        ''' Callback to update timers time when scrubbing the timer slider '''
        if self.inhibit_update:
            return

        for timer in self.timers:
            timer.scrub_time(self.timer_slider * timer.timer_duration)

        updateNode(self, context)

    def update_duration(self, context):
        ''' Update the timer slider when the node duration updates '''
        time = get_average([timer.timer_time for timer in self.timers])
        duration = self.timer_duration
        slider_value = min(1.0, max(0.0, time/duration))
        self.sync_time_slider(slider_value)

        updateNode(self, context)

    timer_slider: FloatProperty(
        name="Slider", description="Time slider for scrubbing and feedback",
        default=0.0, min=0.0, max=1.0, precision=3, update=update_time_slider)

    timer_duration: FloatProperty(
        name="Duration", description="Time after which the timer expires",
        default=10.0, min=0.0, update=update_duration)

    timer_speed: FloatProperty(
        name="Speed", description="Time speed as a multiplier of playback time",
        default=1.0, update=updateNode)

    timer_loops: IntProperty(
        name="Loops", description="Number of times it loops until expires (0 = no loop)",
        default=0, min=0)

    normalize: BoolProperty(
        name="normalize", description="Display times as percetage of the duration",
        default=False, update=updateNode)

    inhibit_update: BoolProperty(
        name="Inhibiter", description="Inhibit the update calls", default=False)

    absolute: BoolProperty(
        name="Absolute", description="Absolute time reference", default=False)

    sticky: BoolProperty(
        name="Sticky", description="Make timer stick to the STOPPED/EXPIRED ends", default=False)

    def sync_time_slider(self, value):
        self.inhibit_update = True
        self.timer_slider = value
        self.inhibit_update = False

    def draw_buttons(self, context, layout):
        cb = SvTimerOperatorCallback.bl_idname

        box = layout.box()

        row = box.row(align=True)
        split = row.split(align=True, factor=1/4)

        reset_button = split.operator(cb, text='', icon="REW")
        reset_button.function_name = "reset_timer"

        split = split.split(align=True, factor=2/3)

        timer_status = TIMER_STATUS_PAUSED
        for timer in self.timers:
            if timer.timer_status == TIMER_STATUS_STARTED:
                timer_status = TIMER_STATUS_STARTED
                break

        if timer_status == TIMER_STATUS_STARTED:
            pause_button = split.operator(cb, text='', icon="PAUSE")
            pause_button.function_name = "pause_timer"
        else:  # PAUSED
            start_button = split.operator(cb, text='', icon='PLAY')
            start_button.function_name = "start_timer"

        expire_button = split.operator(cb, text='', icon='FF')
        expire_button.function_name = "expire_timer"

        row = box.row(align=True)

        loop_backward_button = row.operator(cb, text='', icon="LOOP_BACK")
        loop_backward_button.function_name = "loop_backward_timer"

        row.prop(self, 'timer_slider', text="", slider=True)

        loop_forward_button = row.operator(cb, text='', icon='LOOP_FORWARDS')
        loop_forward_button.function_name = "loop_forward_timer"

        col = layout.column(align=True)
        col.prop(self, "normalize", text="Normalize Time")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        self.draw_animatable_buttons(layout)
        layout.prop(self, "absolute")
        layout.prop(self, "sticky")

    def start_timer(self, context):
        debug("* Timer: start_timer")
        for timer in self.timers:
            timer.start()
        updateNode(self, context)

    def stop_timer(self, context):
        debug("* Timer: stop_timer")
        for timer in self.timers:
            timer.stop()
        self.sync_time_slider(0)
        updateNode(self, context)

    def pause_timer(self, context):
        debug("* Timer: pause_timer")
        for timer in self.timers:
            timer.pause()
        updateNode(self, context)

    def reset_timer(self, context):
        debug("* Timer: reset_timer")
        for timer in self.timers:
            timer.reset()
        self.sync_time_slider(0)
        updateNode(self, context)

    def expire_timer(self, context):
        debug("* Timer: expire_timer")
        for timer in self.timers:
            timer.expire()
        self.sync_time_slider(1)
        updateNode(self, context)

    def loop_backward_timer(self, context):
        debug("* Timer: loop_backward_timer")
        for timer in self.timers:
            timer.loop_backward()
        self.sync_time_slider(0)
        updateNode(self, context)

    def loop_forward_timer(self, context):
        debug("* Timer: loop_forward_timer")
        for timer in self.timers:
            timer.loop_forward()
        self.sync_time_slider(1)
        updateNode(self, context)

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('SvStringsSocket', "Duration").prop_name = "timer_duration"
        self.inputs.new('SvStringsSocket', "Speed").prop_name = "timer_speed"
        self.inputs.new('SvStringsSocket', "Loops").prop_name = "timer_loops"
        self.inputs.new('SvStringsSocket', "Operation")

        self.outputs.new('SvStringsSocket', "Status")
        self.outputs.new('SvStringsSocket', "Elapsed Time")
        self.outputs.new('SvStringsSocket', "Remaining Time")
        self.outputs.new('SvStringsSocket', "Expired")
        self.outputs.new('SvStringsSocket', "Loop")

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists (single or multi value)
        input_loops = self.inputs["Loops"].sv_get()[0]
        input_speed = self.inputs["Speed"].sv_get()[0]
        input_duration = self.inputs["Duration"].sv_get()[0]
        input_operation = self.inputs["Operation"].sv_get(default=[[-1]])[0]

        # sanitize the inputs
        input_loops = list(map(lambda n: max(0, n), input_loops))
        input_duration = list(map(lambda d: max(EPSILON, d), input_duration))

        # update the array of timers
        parameters = match_long_repeat([input_loops, input_speed, input_duration, input_operation])

        old_timer_count = len(self.timers)
        new_timer_count = len(parameters[0])
        # debug("we need {0} timers".format(new_timer_count))
        # debug("old_timer_count = {0}".format(old_timer_count))
        # debug("new_timer_count = {0}".format(new_timer_count))

        # did the number of timers change ? => add or remove timers
        if old_timer_count != new_timer_count:
            if new_timer_count > old_timer_count:  # add new timers
                for n in range(old_timer_count, new_timer_count):
                    # debug("creating new timer: {0}".format(n))
                    timer = self.timers.add()
                    timer.timer_id = n
            else:  # remove old timers
                while len(self.timers) > new_timer_count:
                    n = len(self.timers) - 1
                    # debug("removing old timer: {0}".format(self.timers[n].timer_id))
                    self.timers.remove(n)

        # process timers
        status_list = []
        elapsed_list = []
        remaining_list = []
        expired_list = []
        loop_list = []
        for index, params in enumerate(zip(*parameters)):
            loops, speed, duration, operation = params
            # update timer
            timer = self.timers[index]
            timer.update_time(loops, speed, duration, operation, self.absolute, self.sticky)
            # update lists
            status_list.append(timer.status())
            elapsed_list.append(timer.elapsed_time(self.normalize))
            remaining_list.append(timer.remaining_time(self.normalize))
            expired_list.append(timer.expired())
            loop_list.append(timer.loop_count())

        # update slider if needed (todo: figure out a better way to do this)
        time = get_average([timer.timer_time for timer in self.timers])
        duration = get_average([timer.timer_duration for timer in self.timers])
        slider_value = min(1.0, max(0.0, time/duration))
        self.sync_time_slider(slider_value)

        self.outputs["Status"].sv_set([status_list])
        self.outputs["Elapsed Time"].sv_set([elapsed_list])
        self.outputs["Remaining Time"].sv_set([remaining_list])
        self.outputs["Expired"].sv_set([expired_list])
        self.outputs["Loop"].sv_set([loop_list])


classes = [SvTimerPropertyGroup, SvTimerOperatorCallback, SvTimerNode]


def register():
    _ = [bpy.utils.register_class(cls) for cls in classes]


def unregister():
    _ = [bpy.utils.unregister_class(cls) for cls in reversed(classes)]
