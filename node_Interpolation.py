from node_s import *
from util import *
import bpy
import numpy as np
from bpy.props import EnumProperty, FloatProperty
import bisect



class SvInterpolationNode(Node, SverchCustomTreeNode):
    '''Interpolate'''
    bl_idname = 'SvInterpolationNode'
    bl_label = 'Interpolation'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    t_in = FloatProperty(name="t", min=0, max=1, precision=5, default=.5, update=updateNode)
    
    modes = [('SPL','Cubic',"Cubic Spline",0),
             ('LIN','Linear',"Linear Interpolation",1)]
    mode = EnumProperty( items = modes, name='Mode', default="LIN", update=updateNode)
    
    def init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')
        self.inputs.new('StringsSocket', 'Interval').prop_name = 't_in'
        self.outputs.new('VerticesSocket', 'Vertices')
    
    def draw_buttons(self, context, layout):
        pass
    #    layout.prop(self, 'mode', expand=True)
        
    def update(self):
        if not 'Vertices' in self.outputs:
            return
        if not any((s.links for s in self.outputs)):
            return       
        
        if self.inputs['Vertices'].links:
            verts = SvGetSocketAnyType(self,self.inputs['Vertices'])
            verts = dataCorrect(verts)
            t_ins = self.inputs['Interval'].sv_get()
            verts_out = []
            for v,t_in in zip(verts,repeat_last(t_ins)):
                pts = np.array(v).T
                tmp = np.apply_along_axis(np.linalg.norm,0,pts[:,:-1]-pts[:,1:])
                t = np.insert(tmp,0,0).cumsum()
                t = t/t[-1]
                t_corr = [min(1, max(t_c, 0)) for t_c in t_in]
                # this should also be numpy
                if self.mode == 'LIN':
                    out = [np.interp(t_corr, t, pts[i]) for i in range(3)]
                else: #SPL
                    spl = [spline(t,pts[i]) for i in range(3)]
                    out = [spline_eval(t,pts[i],spl[i],t_corr) for i in range(3)]
                verts_out.append(list(zip(*out)))

            if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
                SvSetSocketAnyType(self, 'Vertices',verts_out)

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SvInterpolationNode)   
    
def unregister():
    bpy.utils.unregister_class(SvInterpolationNode)

if __name__ == "__main__":
    register()
