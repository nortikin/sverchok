import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from ezdxf.math import Vec3
from mathutils import Vector
import ezdxf
from ezdxf import colors
from ezdxf import units
from ezdxf.tools.standards import setup_dimstyle


LWdict = {
    '0.00':0,   
    '0.05':5,   
    '0.09':9,   
    '0.13':13,  
    '0.15':15,
    '0.18':18,
    '0.20':20,
    '0.25':25,
    '0.30':30,
    '0.35':35,
    '0.40':40,
    '0.50':50,
    '0.53':53,
    '0.60':60,
    '0.70':70,
    '0.80':80,
    '0.90':90,
    '1.00':100,
    '1.06':106,
    '1.20':120,
    '1.40':140,
    '1.58':158,
    '2.00':200,
    '2.11':211,
}

class DxfLines:
    def __repr__(self):
        return "<DXF Lines>"

    def __init__(self, vers, color, lineweight, metadata, linetype, node):
        self.vers = vers
        self.node = node
        self.color = color
        self.lineweight = lineweight
        self.metadata = metadata
        self.linetype = linetype

    def draw(self):
        return self.vers


class SvDxfLinesNode(SverchCustomTreeNode, bpy.types.Node):
    bl_idname = 'SvDxfLinesNode'
    bl_label = 'DXF Lines'
    bl_icon = 'EXPORT'
    sv_icon = 'SV_PATH_SVG'
    bl_category = 'DXF'
    sv_dependencies = {'ezdxf'}

    scale: bpy.props.FloatProperty(default=1.0,name='scale')

    text_scale: bpy.props.FloatProperty(default=1.0,name='text_scale')

    metadata: bpy.props.StringProperty(default='',name='metadata')

    color: bpy.props.IntProperty(default=1, min=-3, max=255,name='color')

    lineweights = [
        ('0.00', '0.00','Thin mm',1),
        ('0.05', '0.05','0.05 mm',2), 
        ('0.09', '0.09','0.09 mm',3), 
        ('0.13', '0.13','0.13 mm',4), 
        ('0.15', '0.15','0.15 mm',5), 
        ('0.18', '0.18','0.18 mm',6), 
        ('0.20', '0.20','0.20 mm',7), 
        ('0.25', '0.25','0.25 mm',8), 
        ('0.30', '0.30','0.30 mm',9), 
        ('0.35', '0.35','0.35 mm',10), 
        ('0.40', '0.40','0.40 mm',11), 
        ('0.50', '0.50','0.50 mm',12), 
        ('0.53', '0.53','0.53 mm',13), 
        ('0.60', '0.60','0.60 mm',14), 
        ('0.70', '0.70','0.70 mm',15), 
        ('0.80', '0.80','0.80 mm',16), 
        ('0.90', '0.90','0.90 mm',17), 
        ('1.00', '1.00','1.00 mm',18), 
        ('1.09', '1.06','1.06 mm',19), 
        ('1.20', '1.20','1.20 mm',20), 
        ('1.40', '1.40','1.40 mm',21), 
        ('1.58', '1.58','1.58 mm',22), 
        ('2.00', '2.00','2.00 mm',23), 
        ('2.11', '2.11','2.11 mm',24), 
    ]

    linetypes = [
        ("CONTINUOUS", "CONTINUOUS", "So called Solid linetype", 1),
        ("CENTER", "CENTER", "CENTER linetype", 2),
        ("DASHED", "DASHED", "DASHED linetype", 3),
        ("PHANTOM", "PHANTOM", "PHANTOM linetype", 4),
        ("DASHDOT", "DASHDOT", "DASHDOT linetype", 5),
        ("DOT", "DOT", "DOT linetype", 6),
        ("DIVIDE", "DIVIDE", "DIVIDE linetype", 7),
        ("CENTERX2", "CENTERX2", "CENTERX2 linetype", 8),
        ("DASHEDX2", "DASHEDX2", "DASHEDX2 linetype", 9),
        ("PHANTOMX2", "PHANTOMX2", "PHANTOMX2 linetype", 10),
        ("DASHDOTX2", "DASHDOTX2", "DASHDOTX2 linetype", 11),
        ("DOTX2", "DOTX2", "DOTX2 linetype", 12),
        ("DIVIDEX2", "DIVIDEX2", "DIVIDEX2 linetype", 13),
        ("CENTER2", "CENTER2", "CENTER2 linetype", 14),
        ("DASHED2", "DASHED2", "DASHED2 linetype", 15),
        ("PHANTOM2", "PHANTOM2", "PHANTOM2 linetype", 16),
        ("DASHDOT2", "DASHDOT2", "DASHDOT2 linetype", 17),
        ("DOT2", "DOT2", "DOT2 linetype", 18),
        ("DIVIDE2", "DIVIDE2", "DIVIDE2 linetype", 19)
    ]

    linetype: bpy.props.EnumProperty(
        name="linetype", description="linetypes", default='CONTINUOUS', items=linetypes, update=updateNode)

    lineweight: bpy.props.EnumProperty(
        name="lineweight", description="lineweight", default='0.00', items=lineweights, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'verts')
        self.inputs.new('SvStringsSocket', 'edges')
        self.inputs.new('SvColorSocket', 'color').prop_name='color'
        self.inputs.new('SvTextSocket', 'metadata').prop_name='metadata'
        self.outputs.new('SvSvgSocket', 'dxf')

    def draw_buttons(self, context, layout):
        layout.prop(self, "linetype", expand=False)
        layout.prop(self, "lineweight", expand=False)

    def process(self):
        if self.outputs['dxf'].is_linked:
            # All starts with dxf socket
            if self.inputs['verts'].is_linked:
                vers_ = self.inputs['verts'].sv_get()
            if self.inputs['edges'].is_linked:
                edges_ = self.inputs['edges'].sv_get()
            #if self.inputs['color'].is_linked:
            # color [[ (1,0,1) ]]
            cols_ = self.inputs['color'].sv_get()[0][0]
            #if self.inputs['metadata'].is_linked:
            # It is any text [['text']]
            meta_ = self.inputs['metadata'].sv_get()
            dxf = []
            # not match long repeate because we can use several nodes 
            # and multipliying mesh with colors absurdic, except meta
            # lw,lt - lineweight, linetype
            lw = LWdict[self.lineweight]
            lt = self.linetype
            for obv,obe,met in zip_long_repeat(vers_,edges_,meta_):
                for ed in obe:
                    points = []
                    for ver, me in zip_long_repeat(ed,met):
                        vr = obv[ver]
                        if type(vr) == Vector: vr = vr.to_tuple()
                        points.append(vr)
                    edgs = DxfLines(points,cols_,lw,me,lt,self)
                    dxf.append(edgs)
            self.outputs['dxf'].sv_set([dxf])

    def sv_update(self):
        if not ("verts" in self.inputs):
            return

def register():
    bpy.utils.register_class(SvDxfLinesNode)

def unregister():
    bpy.utils.unregister_class(SvDxfLinesNode)

if __name__ == "__main__":
    register()