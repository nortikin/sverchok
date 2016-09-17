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

import pyaudio
import numpy as np

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode


class SpectrumAnalyzer:
    FORMAT = pyaudio.paFloat32
    CHANNELS = 1
    RATE = 16000
    CHUNK = 512
    START = 0
    N = 512

    wave_x = 0
    wave_y = 0
    spec_x = 0
    spec_y = 0
    data = []

    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.open_dataframe()

    def open_dataframe(self):
        self.stream = self.pa.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            output=False,
            frames_per_buffer=self.CHUNK
        )        

    def do_dataframe(self):
        self.data = self.audioinput()
        self.fft()
        # return self.wave_x, self.wave_y, self.N, self.spec_x, self.spec_y, self.RATE
        return self.wave_x, self.wave_y, self.spec_x, self.spec_y

    def end_updates(self):
        self.pa.close(stream=self.stream)

    def audioinput(self):
        ret = self.stream.read(self.CHUNK)
        ret = np.fromstring(ret, np.float32)
        return ret

    def fft(self):
        self.wave_x = range(self.START, self.START + self.N)
        self.wave_y = self.data[self.START:self.START + self.N]
        self.spec_x = np.fft.fftfreq(self.N, d=1.0 / self.RATE)  
        y = np.fft.fft(self.data[self.START:self.START + self.N])    
        self.spec_y = [np.sqrt(c.real ** 2 + c.imag ** 2) for c in y]



class SvFFTCallback(Operator):

    bl_idname = "node.fft_callback"
    bl_label = "Short Name"

    fn_name = bpy.props.StringProperty(default='')

    def dispatch(self, context, type_op):
        n = context.node

        if type_op == 'on':
            n.active = True
            wik = SpectrumAnalyzer()
            n.node_dict[hash(n)] = {'FFT': wik}
            wik.open_dataframe()
        elif type_op == 'off':
            n.active = False
            n.end_updates()

    def execute(self, context):
        self.dispatch(context, self.fn_name)
        return {'FINISHED'}


class SvFFTClientNode(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'SvFFTClientNode'
    bl_label = 'FFT Client'

    active = BoolProperty(default=False, name='Active')
    node_dict = {}

    def draw_buttons(self, context, layout):
        state = 'on' if not self.active else 'off'
        layout.operator('node.fft_callback', text=state).fn_name = state

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'frame')
        self.outputs.new('StringsSocket', 'wave_x')
        self.outputs.new('StringsSocket', 'wave_y')
        self.outputs.new('StringsSocket', 'spec_x')
        self.outputs.new('StringsSocket', 'spec_y')

    def process(self):
        if not self.active:
            return

        data = None
 
        input_value = self.inputs[0].sv_get()
        if input_value:
            current_node_dict = self.node_dict.get(hash(self))
            if current_node_dict:
                # at this point FFT must be present..
                wik = self.node_dict[hash(self)].get('FFT')
                data = wik.do_dataframe()
                print('updated')
            else:
                print('failed?')
                self.active = not self.active
                return

        outputs = self.outputs
        for idx, sock in enumerate('wave_x wave_y spec_x spec_y'.split(' ')):
            if outputs[sock].is_linked:
                outputs[sock].sv_set([data[idx]])

   
    def end_updates(self):
        wik = self.node_dict[hash(self)].get('FFT')
        if wik:
            wik.end_updates()


def register():
    bpy.utils.register_class(SvFFTCallback)
    bpy.utils.register_class(SvFFTClientNode)


def unregister():
    bpy.utils.unregister_class(SvFFTClientNode)
    bpy.utils.unregister_class(SvFFTCallback)

if __name__ == "__main__":
    register()