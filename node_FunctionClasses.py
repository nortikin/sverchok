import bpy
from node_s import *
from util import *
from mathutils import Vector, Matrix
from math import *



class ScalarFunctionXNode(Node, SverchCustomTreeNode):
    ''' ScalarFunctionXNode '''
    bl_idname = 'ScalarFunctionXNode'
    bl_label = 'f(x)'
    bl_icon = 'OUTLINER_OB_EMPTY'
 

# Math functions from http://docs.python.org/3.3/library/math.html
# maybe this should be distilled to most common with the others available via FormulaNode
    
    mode_items = [
        ("SINE",            "Sine",         "", 1),
        ("COSINE",          "Cosine",       "", 2),
        ("TANGENT",         "Tangent",      "", 3),
        ("ARCSINE",         "Arcsine",      "", 4),
        ("ARCCOSINE",       "Arccosine",    "", 5),
        ("ARCTANGENT",      "Arctangent",   "", 6),
        ("SQRT",            "Squareroot",   "", 7),
        ("NEG",             "Negate",       "", 8),
        ("DEGREES",         "Degrees",      "", 9),
        ("RADIANS",         "Radians",      "", 10),
        ("ABS",             "Absolute",     "", 11),
        ("CEIL",            "Ceiling",      "", 12),
        ("FLOOR",           "floor",        "", 13),
        ("EXP",             "Exponent",    "", 14),
        ("LN",              "log",          "", 15),
        ("LOG1P",           "log1p",        "", 16),
        ("LOG10",           "log10",        "", 17),
        ("ACOSH",           "acosh",        "", 18),
        ("ASINH",           "asinh",        "", 19),
        ("ATANH",           "atanh",        "", 20),
        ("COSH",            "cosh",         "", 21),
        ("SINH",            "sinh",         "", 22),
        ("TANH",            "tanh",         "", 23)
        ]
        
    items_=bpy.props.EnumProperty( items = mode_items, name="Function", 
            description="Function choice", default="SINE", update=updateNode)
    
    def draw_buttons(self, context, layout):
        layout.prop(self,"items_","F(x)");

    def init(self, context):
        self.inputs.new('StringsSocket', "float", "x")
        self.outputs.new('StringsSocket', "float", "out")
        

    def update(self):
        fx = {
              'SINE':       sin,
              'COSINE':     cos,
              'TANGENT':    tan,
              'ARCSINE':    asin,
              'ARCCOSINE':  acos,
              'ARCTANGENT': atan,
              'SQRT':       lambda x: sqrt(fabs(x)),
              'NEG':        lambda x: -x,
              'DEGREES':    degrees,
              'RADIANS':    radians,
              'ABS':        fabs,
              'FLOOR':      floor,
              'CEIL':       ceil,
              'EXP':        exp,
              'LOG':        log,
              'LOG1P':      log1p,
              'LOG10':      log10,
              'ACOSH':      acosh,
              'ASINH':      asinh,
              'COSH':       cosh,
              'SINH':       sinh,
              'TANH':       tanh
              } 
        # inputs
        self.label=self.items_
        if 'float' in self.inputs and len(self.inputs['float'].links)>0 and \
            type(self.inputs['float'].links[0].from_socket) == StringsSocket:
            if not self.inputs['float'].node.socket_value_update:
                self.inputs['float'].node.update()
            Number = self.inputs['float'].links[0].from_socket.StringsProperty
        else:
            Number = []
        
        # outputs
        if 'float' in self.outputs and len(self.outputs['float'].links)>0:
            if not self.outputs['float'].node.socket_value_update:
                self.inputs['float'].node.update()
            num = eval(Number)
            result = self.recurse(num,fx[self.items_])
                      
            self.outputs['float'].StringsProperty = str(result)
    
    
    def recurse(self, l,f):
        if type(l) == int or type(l) == float:
            t = f(l)
        else:
            t = []
            for i in l:
                i = self.recurse(i,f)
                t.append(i)
        return t
    
    def update_socket(self, context):
        self.update()        
    


def register():
    bpy.utils.register_class(ScalarFunctionXNode)
    
def unregister():
    bpy.utils.unregister_class(ScalarFunctionXNode)

if __name__ == "__main__":
    register()