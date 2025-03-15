import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
#from ezdxf.math import Vec3
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

class DxfHatch:
    def __repr__(self):
        return "<DXF Hatch>"

    def __init__(self, vers, color, metadata, pattern, scale, node):
        self.vers = vers
        self.node = node
        self.color = color
        self.pattern = pattern
        self.scale = scale
        self.metadata = metadata

    def draw(self):
        return self.vers


class SvDxfHatchNode(SverchCustomTreeNode, bpy.types.Node):
    bl_idname = 'SvDxfHatchNode'
    bl_label = 'DXF Hatches'
    bl_icon = 'EXPORT'
    sv_icon = 'SV_PATTERN_SVG'
    bl_category = 'DXF'
    sv_dependencies = {'ezdxf'}

    scale: bpy.props.FloatProperty(default=1.0,name='scale')

    text_scale: bpy.props.FloatProperty(default=1.0,name='text_scale')

    hatch_scale: bpy.props.FloatProperty(default=0.5,name='hatch_scale', description='Hatch can be too dense or too rear, carefully')

    metadata: bpy.props.StringProperty(default='',name='metadata')

    color: bpy.props.IntProperty(default=1, min=-3, max=255,name='color')

    patterns = [
        ('ANSI31',        'Simple cut ANSI31','ANSI31',         1),
        ('ANSI32',        'Brick cut ANSI32','ANSI32',          2),
        ('ANSI33',        'R/f concrete cut ANSI33','ANSI33',   3),
        ('ANSI34',        'ground cut ANSI34','ANSI34',         4),
        ('ANSI35',        'R/f concrete cut ANSI35','ANSI35',   5),
        ('ANSI36',        'Concrete cut ANSI36','ANSI36',       6),
        ('ANSI37',        'Insulation cut ANSI37','ANSI37',     7),
        ('ANSI38',        'Wood cut ANSI38','ANSI38',           8),
        ('ACAD_ISO02W100','dash 02 W100','ACAD_ISO',            9),
        ('ACAD_ISO03W100','dash 03 W100','ACAD_ISO',            10),
        ('ACAD_ISO04W100','dash 04 W100','ACAD_ISO',            11),
        ('ACAD_ISO05W100','dashdot 05 W100','ACAD_ISO',         12),
        ('ACAD_ISO06W100','dashdotdot 06 W100','ACAD_ISO',      13),
        ('ACAD_ISO07W100','dots 07 W100','ACAD_ISO',            14),
        ('ACAD_ISO08W100','solid 08 W100','ACAD_ISO',           15),
        ('ACAD_ISO09W100','dash 09 W100','ACAD_ISO',            16),
        ('ACAD_ISO10W100','dashdot 10 W100','ACAD_ISO',         17),
        ('ACAD_ISO11W100','dashdot 11 W100','ACAD_ISO',         18),
        ('ACAD_ISO12W100','dashdotdot 12 W100','ACAD_ISO',      19),
        ('ACAD_ISO13W100','dashdotdot 13 W100','ACAD_ISO',      20),
        ('ACAD_ISO14W100','dashdotdot 14 W100','ACAD_ISO',      21),
        ('ACAD_ISO15W100','dashdotdot 15 W100','ACAD_ISO',      22),
        ('ANGLE',         'ANGLE','Angle',                      23),
        ('AR-B816',       'Brick 816','Simple Brick',           24),
        ('AR-B816C',      'Brick 816C','Simple Brick',          25),
        ('AR-B88',        'Brick 88','Simple Brick',            26),
        ('AR-BRELM',      'Brick ELM','Simple Brick',           27),
        ('AR-BRSTD',      'Brick STD','Simple Brick',           28),
        ('AR-CONC',       'Concrete','Concrete',                29),
        ('AR-HBONE',      'Pavement Hbone','Pavement',          30),
        ('AR-PARQ1',      'Parquete square','Parquete',         31),
        ('AR-RROOF',      'Water like roof','Roof',             32),
        ('AR-RSHKE',      'Slices roof','Roof',                 33),
        ('AR-SAND',       'Sand','Sand',                        34),
        ('BOX',           'Box pattern','Crosses and dots',     35),
        ('BRASS',         'Brass','solids and dashed lines',    36),
        ('BRICK',         'Brick','Brick',                      37),
        ('BRSTONE',       'Brick Stone','Long mansory bricks',  38),
        ('CLAY',          'CLAY cut','Glina/Clay cut',          39),
        ('CORK',          'CORK cut','Cork cut',                40),
        ('CROSS',         'CROSS','Cross',                      41),
        ('DASH',          'DASH','Dash',                        42),
        ('DOLMIT',        'DOLMIT','DOLMIT',                    43),
        ('DOTS',          'DOTS','Dots',                        44),
        ('EARTH',         'EARTH cut','English symbol for earth cut',45),
        ('ESCHER',        'ESCHER','ESCHER pattern',            46),
        ('FLEX',          'FLEX','Flex',                        47),
        ('GOST_GLASS',    'GOST_GLASS','GLASS symbol by ГОСТ',  48),
        ('GOST_WOOD',     'GOST_WOOD','WOOD symbol by ГОСТ',    49),
        ('GOST_GROUND',   'GOST_GROUND','GROUND symbol by ГОСТ',50),
        ('GRASS',         'GRASS','GRASS',                      51),
        ('GRATE',         'GRATE','GRATE',                      52),
        ('GRAVEL',        'GRAVEL','GRAVEL',                    53),
        ('HEX',           'HEX','HEX',                          54),
        ('HONEY',         'HONEY','HONEY',                      55),
        ('HOUND',         'HOUND','HOUND',                      56),
        ('INSUL',         'INSUL','INSUL',                      57),
        ('LINE',          'LINE','LINE horisontal',             58),
        ('MUDST',         'MUDST','MUDST',                      59),
        ('NET',           'NET','NET',                          60),
        ('NET3',          'NET3','NET3',                        61),
        ('PLAST',         'PLAST','PLAST',                      62),
        ('PLASTI',        'PLASTI','PLASTI',                    63),
        ('SACNCR',        'SACNCR','SACNCR',                    64),
        ('SQUARE',        'SQUARE','SQUARE',                    65),
        ('STARS',         'STARS','STARS',                      66),
        ('STEEL',         'STEEL','STEEL',                      67),
        ('SWAMP',         'SWAMP','SWAMP',                      68),
        ('TRANS',         'TRANS','TRANS',                      69),
        ('TRIANG',        'TRIANG','TRIANG',                    70),
        ('ZIGZAG',        'ZIGZAG','ZIGZAG',                    71),
        
    ]

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

    pattern: bpy.props.EnumProperty(
        name="pattern", description="pattern", default='ANSI31', items=patterns, update=updateNode)

    linetype: bpy.props.EnumProperty(
        name="linetype", description="linetypes", default='CONTINUOUS', items=linetypes, update=updateNode)

    lineweight: bpy.props.EnumProperty(
        name="lineweight", description="lineweight", default='0.00', items=lineweights, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'verts')
        self.inputs.new('SvStringsSocket', 'pols')
        self.inputs.new('SvColorSocket', 'color').prop_name='color'
        self.inputs.new('SvTextSocket', 'metadata').prop_name='metadata'
        self.outputs.new('SvSvgSocket', 'dxf')

    def draw_buttons(self, context, layout):
        #layout.prop(self, "linetype", expand=False)
        #layout.prop(self, "lineweight", expand=False)
        layout.prop(self, "pattern", expand=False)
        layout.prop(self, "hatch_scale")

    def process(self):
        if self.outputs['dxf'].is_linked:
            # All starts with dxf socket
            if self.inputs['verts'].is_linked:
                vers_ = self.inputs['verts'].sv_get()
            if self.inputs['pols'].is_linked:
                pols_ = self.inputs['pols'].sv_get()
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
            pt = self.pattern
            sc = self.hatch_scale
            print('$%#@$%#%#%#',sc)
            for obv,obp,met in zip_long_repeat(vers_,pols_,meta_):
                # объекты
                for po, me in zip_long_repeat(obp,met):
                    # целый полигон [0,1,2,3]
                    points = []
                    for ver in po:
                        # индексы вершин полигона вытаскивают точки
                        vr = obv[ver]
                        if type(vr) == Vector: vr = vr.to_tuple()
                        points.append(vr)
                    # каждый полигон это отдельный экземпляр
                    pols = DxfHatch(points,cols_,me,pt,sc,self)
                    dxf.append(pols)
            self.outputs['dxf'].sv_set([dxf])

    def sv_update(self):
        if not ("verts" in self.inputs):
            return

def register():
    bpy.utils.register_class(SvDxfHatchNode)

def unregister():
    bpy.utils.unregister_class(SvDxfHatchNode)

if __name__ == "__main__":
    register()